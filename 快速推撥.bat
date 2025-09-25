@echo off
chcp 65001 > nul
echo ========================================
echo       XQ Telegram Bot - GitHub 推撥
echo ========================================
echo.

REM 檢查是否已經是 Git 倉庫
if not exist ".git" (
    echo 🚀 初始化 Git 倉庫...
    git init
    git branch -M main
    echo.
)

echo 📁 添加檔案到 Git...
git add .
echo.

echo 📝 檢查要提交的檔案:
git status
echo.

set /p commit_msg="請輸入提交訊息 (按Enter使用預設): "
if "%commit_msg%"=="" set commit_msg=feat: Update XQ Telegram Bot

echo 💾 提交變更...
git commit -m "%commit_msg%"
echo.

REM 檢查是否已設定 remote origin
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo ⚠️  尚未設定 GitHub 倉庫位址
    echo.
    echo 請先在 GitHub 建立倉庫，然後執行：
    echo git remote add origin https://github.com/您的用戶名/xq-telegram-bot.git
    echo.
    set /p repo_url="請輸入您的 GitHub 倉庫 URL: "
    if not "!repo_url!"=="" (
        git remote add origin !repo_url!
    )
)

echo 🚀 推撥到 GitHub...
git push -u origin main

if errorlevel 0 (
    echo.
    echo ✅ 推撥成功！
    echo 🌐 您的專案現在已經在 GitHub 上了！
) else (
    echo.
    echo ❌ 推撥失敗，請檢查：
    echo 1. 網路連接
    echo 2. GitHub 認證
    echo 3. 倉庫權限
)

echo.
echo 按任意鍵關閉...
pause > nul