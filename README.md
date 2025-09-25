# XQ Telegram 推播系統

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)

這個程式可以監控 XQ 全球贏家的 print 函數輸出，並自動推播到 Telegram。

## ✨ 功能特色

- 📁 監控 `local/xq_trigger.txt` 檔案變更
- 🤖 自動推播訊息到 Telegram
- ⏰ 附加時間戳記
- 🔄 避免重複發送相同內容
- 📝 完整的日誌記錄
- 🖥️ 圖形化管理介面

## 🚀 快速開始

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定 Telegram Bot

1. 在 Telegram 中搜尋 `@BotFather`
2. 發送 `/newbot` 創建新的 Bot
3. 按照指示設定 Bot 名稱和用戶名
4. 取得 Bot Token

### 3. 設定檔案

1. 複製 `config.example.json` 為 `config.json`
2. 編輯 `config.json` 填入您的設定：

```json
{
  "telegram_bot_token": "您的Bot Token",
  "telegram_chat_id": "您的Chat ID",
  "watch_directory": "./local"
}
```

### 4. 啟動程式

**方法一：圖形介面（推薦）**
```bash
# Windows
雙擊 "start_gui.bat"

# 或者
python gui.py
```

**方法二：命令列**
```bash
python XQTelegramNotifier.py
```

## 使用方式

### 啟動監控程式

```bash
python XQTelegramNotifier.py
```

### 在 XQ 全球贏家中設定

在你的 XQ 策略中使用以下方式將訊息寫入檔案：

```python
# XQ 策略範例
def main():
    message = "買進信號：台積電 價格：500"

    # 使用 XQ 的 print 函數將訊息寫到檔案
    print(message, file="local/xq_trigger.txt")
```

## 檔案結構

```
XQ alert to telegram/
├── XQTelegramNotifier.py  # 主程式
├── config.json           # 設定檔
├── requirements.txt      # Python 套件需求
├── local/               # XQ 輸出目錄
│   └── xq_trigger.txt   # XQ print 函數輸出檔案
└── README.md           # 說明文件
```

## 程式運作流程

1. **XQ 策略執行** → 使用 `print()` 函數將訊息寫入 `local/xq_trigger.txt`
2. **檔案監控** → 程式偵測到檔案變更
3. **讀取內容** → 讀取最新的檔案內容
4. **推播到 Telegram** → 將訊息發送到指定的聊天室

## 注意事項

- 確保 `local` 目錄存在且有寫入權限
- Bot Token 和 Chat ID 必須正確設定
- 程式會自動建立 `local` 目錄
- 重複的訊息不會被重複發送

## 故障排除

### 常見錯誤

1. **Bot Token 無效**
   - 檢查 config.json 中的 token 是否正確
   - 確認 Bot 還在運作中

2. **Chat ID 無效**
   - 確認 Chat ID 格式正確（可能是負數）
   - 確認 Bot 已被加入該群組/頻道

3. **檔案權限錯誤**
   - 確保程式對 local 目錄有讀寫權限
   - 在 Windows 上可能需要以管理員身份執行

### 測試方式

手動建立測試檔案：

```bash
echo "測試訊息" > local/xq_trigger.txt
```

如果設定正確，你應該會在 Telegram 中收到訊息。