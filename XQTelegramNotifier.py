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

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XQDirectoryMonitor:
    def __init__(self, telegram_bot, chat_id, watch_directory):
        self.telegram_bot = telegram_bot
        self.chat_id = chat_id
        self.watch_directory = Path(watch_directory)
        self.file_timestamps = {}  # 儲存每個檔案的最後修改時間
        self.last_contents = {}    # 儲存每個檔案的最後內容
        self.running = False

    async def check_directory_changes(self):
        """檢查目錄中所有檔案的變更"""
        try:
            if not self.watch_directory.exists():
                return

            # 查找所有 .txt 和 .log 檔案
            for file_path in self.watch_directory.glob('*.txt'):
                await self.check_file_change(file_path)

            for file_path in self.watch_directory.glob('*.log'):
                await self.check_file_change(file_path)

        except Exception as e:
            logger.error(f"檢查目錄變更時發生錯誤: {e}")

    async def check_file_change(self, file_path):
        """檢查單一檔案的變更"""
        try:
            file_key = str(file_path)
            current_modified = file_path.stat().st_mtime

            # 檢查是否為新檔案或檔案已修改
            if file_key not in self.file_timestamps or current_modified > self.file_timestamps[file_key]:
                self.file_timestamps[file_key] = current_modified

                # 等待檔案寫入完成
                await asyncio.sleep(0.5)

                # 讀取檔案內容
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().strip()

                # 檢查內容是否有變更（避免重複發送）
                if content and content != self.last_contents.get(file_key, ""):
                    self.last_contents[file_key] = content

                    # 發送到 Telegram
                    await self.send_to_telegram(file_path.name, content)

        except Exception as e:
            logger.error(f"檢查檔案 {file_path} 時發生錯誤: {e}")

    async def send_to_telegram(self, filename, content):
        """發送訊息到 Telegram"""
        try:
            # 加上時間戳記和檔案名稱
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"🔔 XQ 交易信號 [{timestamp}]\n📁 檔案: {filename}\n\n{content}"

            await self.telegram_bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            logger.info(f"✅ 訊息已發送到 Telegram: {filename} - {content[:30]}...")

        except Exception as e:
            logger.error(f"發送訊息到 Telegram 時發生錯誤: {e}")

    async def start_monitoring(self):
        """開始監控目錄"""
        self.running = True
        logger.info(f"開始監控目錄: {self.watch_directory}")

        while self.running:
            await self.check_directory_changes()
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
                text="✅ XQ Telegram 通知服務已啟動\n正在監控目錄中的 .txt 和 .log 檔案變更..."
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