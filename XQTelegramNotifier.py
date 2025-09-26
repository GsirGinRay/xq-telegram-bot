import os
import time
import asyncio
import logging
import threading
from pathlib import Path
import telegram
from telegram import Bot
import json
from datetime import datetime
import glob

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XQDirectoryMonitor:
    def __init__(self, telegram_bot, chat_id, watch_directory):
        self.telegram_bot = telegram_bot
        self.chat_id = chat_id
        self.watch_directory = Path(watch_directory)
        self.file_states = {}  # 儲存每個檔案的狀態
        self.running = False
        self.state_file = self.watch_directory / ".xq_file_states.json"  # 狀態檔案

    def load_file_states(self):
        """載入檔案狀態"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.file_states = json.load(f)
                logger.info(f"載入檔案狀態: {len(self.file_states)} 個檔案")
            else:
                logger.info("沒有找到檔案狀態記錄，將記錄現有檔案")
        except Exception as e:
            logger.error(f"載入檔案狀態時發生錯誤: {e}")
            self.file_states = {}

    def save_file_states(self):
        """儲存檔案狀態"""
        try:
            # 使用臨時檔案避免寫入時程式崩潰導致狀態檔案損壞
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_states, f, indent=2, ensure_ascii=False)
            # 原子性移動檔案
            temp_file.replace(self.state_file)
        except Exception as e:
            logger.error(f"儲存檔案狀態時發生錯誤: {e}")

    async def initialize_existing_files(self):
        """初始化現有檔案，記錄其狀態但不發送通知"""
        try:
            # 載入之前記錄的檔案狀態
            self.load_file_states()

            # 只搜尋 .log 檔案
            all_files = list(self.watch_directory.glob("*.log"))

            for file_path in all_files:
                if not file_path.exists():
                    continue

                file_key = str(file_path)
                current_modified = file_path.stat().st_mtime

                # 如果檔案不在之前記錄中，才記錄為現有檔案
                if file_key not in self.file_states:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read().strip()
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='big5') as file:
                                content = file.read().strip()
                        except:
                            content = ""

                    # 記錄現有檔案狀態，不發送通知
                    self.file_states[file_key] = {
                        'modified': current_modified,
                        'content': content,
                        'initialized': True
                    }
                    logger.info(f"已記錄現有檔案: {file_path.name}")

            # 儲存更新後的檔案狀態
            self.save_file_states()

        except Exception as e:
            logger.error(f"初始化現有檔案時發生錯誤: {e}")

    async def check_and_send_updates(self):
        try:
            # 只搜尋 .log 檔案
            all_files = list(self.watch_directory.glob("*.log"))
            logger.info(f"掃描到 {len(all_files)} 個 .log 檔案")

            for file_path in all_files:
                if not file_path.exists():
                    continue

                file_key = str(file_path)
                current_modified = file_path.stat().st_mtime

                # 如果是新檔案或檔案有更新
                if file_key not in self.file_states:
                    logger.info(f"發現新檔案: {file_path.name}")
                    # 新檔案 - 需要發送通知
                    await asyncio.sleep(0.5)  # 等待檔案寫入完成

                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read().strip()
                        logger.info(f"成功讀取檔案內容 (UTF-8): {content[:50]}...")
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='big5') as file:
                                content = file.read().strip()
                            logger.info(f"成功讀取檔案內容 (Big5): {content[:50]}...")
                        except Exception as e:
                            content = ""
                            logger.error(f"讀取檔案失敗: {e}")

                    if content:
                        logger.info(f"檢測到新檔案，準備發送: {file_path.name} - {content[:50]}...")

                        # 只發送最後一行內容（最新的訊息）
                        lines = content.strip().split('\n')
                        latest_line = lines[-1].strip() if lines else content.strip()

                        # 加上時間戳記和檔案名稱
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message = f"🔔 XQ 全球贏家通知 [{timestamp}]\n📁 新檔案: {file_path.name}\n\n{latest_line}"

                        try:
                            await self.telegram_bot.send_message(
                                chat_id=self.chat_id,
                                text=message
                            )
                            logger.info(f"✅ 新檔案訊息已發送到 Telegram: {file_path.name}")
                        except Exception as e:
                            logger.error(f"發送 Telegram 訊息失敗: {e}")
                    else:
                        logger.warning(f"檔案內容為空，不發送通知: {file_path.name}")

                    # 記錄檔案狀態並立即保存
                    self.file_states[file_key] = {
                        'modified': current_modified,
                        'content': content
                    }
                    logger.info(f"已記錄檔案狀態: {file_path.name}")
                    # 立即保存新檔案狀態，確保不會重複發送
                    self.save_file_states()
                    logger.info("狀態檔案已保存")

                elif current_modified > self.file_states[file_key]['modified']:
                    # 現有檔案有更新 - 只有內容變更時才發送
                    await asyncio.sleep(0.5)

                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read().strip()
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='big5') as file:
                                content = file.read().strip()
                        except:
                            content = ""

                    last_content = self.file_states[file_key].get('content', '')

                    if content and content != last_content:
                        logger.info(f"檔案內容更新，準備發送: {file_path.name} - {content[:50]}...")

                        # 找出新增的內容（最新的一行）
                        if last_content:
                            # 分割成行
                            old_lines = last_content.strip().split('\n')
                            new_lines = content.strip().split('\n')

                            # 找出新增的行
                            if len(new_lines) > len(old_lines):
                                # 取最新加入的行
                                new_content = new_lines[-1].strip()
                            else:
                                # 如果行數相同，可能是最後一行有變化
                                new_content = new_lines[-1].strip() if new_lines else content.strip()
                        else:
                            # 如果沒有之前的內容，取最後一行
                            lines = content.strip().split('\n')
                            new_content = lines[-1].strip() if lines else content.strip()

                        # 加上時間戳記和檔案名稱
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message = f"🔔 XQ 全球贏家通知 [{timestamp}]\n📁 檔案更新: {file_path.name}\n\n{new_content}"

                        try:
                            await self.telegram_bot.send_message(
                                chat_id=self.chat_id,
                                text=message
                            )
                            logger.info(f"✅ 檔案更新訊息已發送到 Telegram: {file_path.name}")
                        except Exception as e:
                            logger.error(f"發送檔案更新訊息失敗: {e}")

                    # 更新檔案狀態
                    self.file_states[file_key] = {
                        'modified': current_modified,
                        'content': content
                    }

        except Exception as e:
            logger.error(f"檢查檔案更新時發生錯誤: {e}")

    async def start_monitoring(self):
        """開始監控目錄"""
        self.running = True
        logger.info(f"開始監控目錄: {self.watch_directory}")

        # 首先初始化現有檔案（不發送通知）
        await self.initialize_existing_files()
        logger.info("現有檔案初始化完成，開始監控新增檔案...")

        save_counter = 0
        try:
            while self.running:
                try:
                    await self.check_and_send_updates()
                    save_counter += 1

                    # 每30次循環保存一次狀態檔案（約30秒）
                    if save_counter >= 30:
                        self.save_file_states()
                        save_counter = 0

                except Exception as e:
                    logger.error(f"監控循環中發生錯誤: {e}")
                    await asyncio.sleep(5)  # 發生錯誤時等待5秒再繼續
                    continue

                await asyncio.sleep(1)  # 每秒檢查一次

        finally:
            # 程式結束時保存狀態
            self.save_file_states()
            logger.info("監控已停止，狀態已保存")

    def stop_monitoring(self):
        """停止監控"""
        self.running = False

class XQTelegramNotifier:
    def __init__(self, bot_token, chat_id, watch_directory="./local"):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.watch_directory = watch_directory
        self.bot = Bot(token=bot_token)
        self.monitor = None

        # 確保監控目錄存在
        os.makedirs(watch_directory, exist_ok=True)
        logger.info(f"監控目錄: {os.path.abspath(watch_directory)}")

    async def start_monitoring(self):
        """啟動檔案監控"""
        try:
            # 測試 Telegram Bot 連接
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram Bot 已連接: {bot_info.first_name}")

            # 設定目錄監控
            self.monitor = XQDirectoryMonitor(self.bot, self.chat_id, self.watch_directory)

            # 發送啟動通知
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="✅ XQ Telegram 通知服務已啟動\n正在監控目錄中的 .log 檔案...\n\n註：現有檔案不會推播，只推播新增的檔案"
            )

            # 啟動監控
            await self.monitor.start_monitoring()

        except KeyboardInterrupt:
            logger.info("收到中斷信號，正在關閉...")
            if self.monitor:
                self.monitor.stop_monitoring()
        except Exception as e:
            logger.error(f"啟動監控時發生錯誤: {e}")
            raise

async def main():
    # 讀取設定檔
    config_file = "config.json"

    if not os.path.exists(config_file):
        # 建立範例設定檔
        config = {
            "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
            "telegram_chat_id": "YOUR_CHAT_ID_HERE",
            "watch_directory": "./local"
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.error(f"請先設定 {config_file} 檔案中的 Telegram Bot Token 和 Chat ID")
        return

    # 載入設定
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)

    bot_token = config.get("telegram_bot_token")
    chat_id = config.get("telegram_chat_id")
    watch_directory = config.get("watch_directory", "./local")

    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        logger.error("請在 config.json 中設定有效的 Telegram Bot Token")
        return

    if not chat_id or chat_id == "YOUR_CHAT_ID_HERE":
        logger.error("請在 config.json 中設定有效的 Telegram Chat ID")
        return

    # 啟動通知服務
    notifier = XQTelegramNotifier(bot_token, chat_id, watch_directory)
    await notifier.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())