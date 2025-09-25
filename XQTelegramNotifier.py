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

class XQFileMonitor:
    def __init__(self, telegram_bot, chat_id, file_path):
        self.telegram_bot = telegram_bot
        self.chat_id = chat_id
        self.file_path = Path(file_path)
        self.last_content = ""
        self.last_modified = 0
        self.running = False

    async def send_file_content(self):
        try:
            if not self.file_path.exists():
                return

            # 檢查檔案是否有變更
            current_modified = self.file_path.stat().st_mtime
            if current_modified <= self.last_modified:
                return

            self.last_modified = current_modified

            # 等待一下確保檔案寫入完成
            await asyncio.sleep(0.5)

            with open(self.file_path, 'r', encoding='utf-8') as file:
                content = file.read().strip()

            # 避免重複發送相同內容
            if content and content != self.last_content:
                self.last_content = content
                logger.info(f"檔案內容變更，準備發送: {content}")

                # 加上時間戳記
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"🔔 XQ 全球贏家通知 [{timestamp}]\n\n{content}"

                await self.telegram_bot.send_message(
                    chat_id=self.chat_id,
                    text=message
                )
                logger.info(f"✅ 訊息已發送到 Telegram: {content[:50]}...")
            elif content:
                logger.info(f"檔案內容未變更，跳過發送: {content[:30]}...")

        except Exception as e:
            logger.error(f"發送訊息時發生錯誤: {e}")

    async def start_monitoring(self):
        """開始監控檔案"""
        self.running = True
        logger.info(f"開始監控檔案: {self.file_path}")

        while self.running:
            await self.send_file_content()
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

            # 設定檔案監控
            file_path = os.path.join(self.watch_directory, "xq_trigger.txt")
            self.monitor = XQFileMonitor(self.bot, self.chat_id, file_path)

            # 發送啟動通知
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="✅ XQ Telegram 通知服務已啟動\n正在監控 xq_trigger.txt 檔案變更..."
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