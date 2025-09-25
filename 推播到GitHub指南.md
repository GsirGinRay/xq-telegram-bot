# 推撥到 GitHub 完整指南

## 🚀 第一步：在 GitHub 建立新倉庫

1. 前往 [GitHub](https://github.com)
2. 點擊右上角 **"+"** → **"New repository"**
3. 填寫倉庫資訊：
   - **Repository name**: `xq-telegram-bot`
   - **Description**: `XQ 全球贏家 Telegram 推播系統 - 監控交易信號並自動推送到 Telegram`
   - **Public** ✅ (推薦，讓更多人受益)
   - **Add a README file** ❌ (我們已經有了)
   - **Add .gitignore** ❌ (我們已經有了)
   - **Choose a license** ❌ (我們已經有MIT授權)

4. 點擊 **"Create repository"**

## 💻 第二步：在本地執行 Git 指令

開啟命令提示字元（cmd）並執行以下指令：

```bash
# 1. 進入發佈目錄
cd "D:\G股網\XQ alert to telegram\github-release"

# 2. 初始化 Git 倉庫
git init

# 3. 設定預設分支名稱
git branch -M main

# 4. 添加所有檔案到暫存區
git add .

# 5. 檢查要提交的檔案 (可選)
git status

# 6. 提交變更
git commit -m "feat: 初始發布 - XQ Telegram 推播系統

✨ 功能特色:
- 🖥️ 圖形化管理介面
- 📁 監控檔案變更並推送到 Telegram
- ⏰ 自動時間戳記
- 🔄 避免重複發送
- 🤖 一鍵設定 Bot Token 和 Chat ID

🚀 支援:
- Windows 一鍵啟動
- 完整中文說明
- MIT 開源授權"

# 7. 連接到您的 GitHub 倉庫 (請替換成您的 GitHub 用戶名)
git remote add origin https://github.com/您的用戶名/xq-telegram-bot.git

# 8. 推撥到 GitHub
git push -u origin main
```

## 🔧 第三步：驗證和完善

推撥成功後：

1. **檢查倉庫內容**
   - 確認所有檔案都已上傳
   - 檢查 README.md 是否正常顯示

2. **完善專案資訊**
   - 在 GitHub 上編輯專案描述
   - 添加主題標籤：`telegram-bot`, `xq`, `python`, `gui`, `notification`

3. **分享給社群**
   - 邀請朋友試用
   - 收集使用回饋

## ❗ 常見問題解決

### 問題1：git 指令不存在
**解決方案：** 安裝 Git for Windows
- 下載：https://git-scm.com/download/win
- 安裝後重新開啟命令提示字元

### 問題2：認證失敗
**解決方案：** 設定 GitHub 認證
```bash
# 設定用戶資訊
git config --global user.name "您的姓名"
git config --global user.email "您的Email"
```

### 問題3：推撥被拒絕
**解決方案：** 可能需要使用 Personal Access Token
1. GitHub → Settings → Developer settings → Personal access tokens
2. 生成 token 並替代密碼使用

## 🎉 推撥成功後

您的專案將會在：
`https://github.com/您的用戶名/xq-telegram-bot`

其他人就可以：
```bash
git clone https://github.com/您的用戶名/xq-telegram-bot.git
cd xq-telegram-bot
pip install -r requirements.txt
cp config.example.json config.json
# 編輯 config.json
python gui.py
```

## 📊 建議的後續改進

- 添加 GitHub Actions 自動測試
- 建立 Releases 版本標籤
- 編寫更多使用範例
- 收集使用者反饋和建議

祝您推撥順利！🚀