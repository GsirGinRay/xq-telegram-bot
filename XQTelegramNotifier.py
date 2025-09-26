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

    async def initialize_existing_files(self):
        """初始化現有檔案，記錄其狀態但不發送通知"""
        try:
            # 搜尋所有 .log 檔案和 xq_trigger.txt
            log_files = list(self.watch_directory.glob("*.log"))
            trigger_file = self.watch_directory / "xq_trigger.txt"

            # 加入 trigger 檔案到監控列表
            all_files = log_files.copy()
            if trigger_file.exists():
                all_files.append(trigger_file)

            for file_path in all_files:
                if not file_path.exists():
                    continue

                file_key = str(file_path)
                current_modified = file_path.stat().st_mtime

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

        except Exception as e:
            logger.error(f"初始化現有檔案時發生錯誤: {e}")

    async def check_and_send_updates(self):
        try:
            # 搜尋所有 .log 檔案和 xq_trigger.txt
            log_files = list(self.watch_directory.glob("*.log"))
            trigger_file = self.watch_directory / "xq_trigger.txt"

            # 加入 trigger 檔案到監控列表
            all_files = log_files.copy()
            if trigger_file.exists():
                all_files.append(trigger_file)

            for file_path in all_files:
                if not file_path.exists():
                    continue

                file_key = str(file_path)
                current_modified = file_path.stat().st_mtime

                # 如果是新檔案或檔案有更新
                if file_key not in self.file_states:
                    # 新檔案 - 需要發送通知
                    await asyncio.sleep(0.5)  # 等待檔案寫入完成

                    try:
                        with open(file_path, 'r', encoding='utf-8') as file:
                            content = file.read().strip()
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='big5') as file:
                                content = file.read().strip()
                        except:
                            content = ""

                    if content:
                        logger.info(f"檢測到新檔案，準備發送: {file_path.name} - {content[:50]}...")

                        # 加上時間戳記和檔案名稱
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message = f"🔔 XQ 全球贏家通知 [{timestamp}]\n📁 新檔案: {file_path.name}\n\n{content}"

                        await self.telegram_bot.send_message(
                            chat_id=self.chat_id,
                            text=message
                        )
                        logger.info(f"✅ 新檔案訊息已發送到 Telegram: {file_path.name}")

                    # 記錄檔案狀態
                    self.file_states[file_key] = {
                        'modified': current_modified,
                        'content': content
                    }

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

                        # 加上時間戳記和檔案名稱
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        message = f"🔔 XQ 全球贏家通知 [{timestamp}]\n📁 檔案更新: {file_path.name}\n\n{content}"

                        await self.telegram_bot.send_message(
                            chat_id=self.chat_id,
                            text=message
                        )
                        logger.info(f"✅ 檔案更新訊息已發送到 Telegram: {file_path.name}")

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

        while self.running:
            await self.check_and_send_updates()
            await asyncio.sleep(1)  # 每秒檢查一次

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
                text="✅ XQ Telegram 通知服務已啟動\n正在監控目錄中的 .log 檔案和 xq_trigger.txt...\n\n註：現有檔案不會推播，只推播新增的檔案"
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