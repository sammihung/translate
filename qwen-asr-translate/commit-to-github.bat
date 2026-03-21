@echo off
REM ==========================================
REM Qwen ASR Translate - Git Commit Script
REM ==========================================
REM This script helps you commit and push optimizations to GitHub

echo.
echo ========================================
echo  Qwen ASR Translate - Git Commit Tool
echo ========================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed!
    echo.
    echo Please install Git from: https://git-scm.com/download/win
    echo.
    echo After installation, run this script again.
    echo.
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo [INFO] Initializing Git repository...
    git init
    echo.
)

REM Check git status
echo [INFO] Checking repository status...
git status
echo.

REM Add all files
echo [INFO] Adding all files to staging...
git add .
echo.

REM Show what will be committed
echo [INFO] Files to be committed:
git status --short
echo.

REM Ask for commit message
set /p COMMIT_MSG="Enter commit message (or press Enter for default): "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=feat: Professional optimizations - type hints, logging, error handling

echo.
echo [INFO] Commit message: %COMMIT_MSG%
echo.

REM Commit
echo [INFO] Committing changes...
git commit -m "%COMMIT_MSG%"
if %ERRORLEVEL% NEQ 0 (
    echo [WARN] Commit failed. This might be because there are no changes.
    echo.
)

REM Check if remote is configured
git remote -v >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [INFO] No remote repository configured.
    echo.
    echo To push to GitHub, you need to:
    echo   1. Create a repository on GitHub
    echo   2. Run: git remote add origin YOUR_REPO_URL
    echo   3. Run: git push -u origin main
    echo.
    echo Your changes are committed locally and ready to push.
    echo.
    pause
    exit /b 0
)

REM Ask if user wants to push
set /p PUSH="Do you want to push to GitHub? (Y/N): "
if /i "%PUSH%"=="Y" (
    echo.
    echo [INFO] Pushing to GitHub...
    git push -u origin main
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo [SUCCESS] Changes pushed to GitHub!
        echo.
    ) else (
        echo.
        echo [ERROR] Push failed. Please check your GitHub credentials.
        echo.
    )
) else (
    echo.
    echo [INFO] Changes committed locally. Run 'git push' when ready.
    echo.
)

echo ========================================
echo  Done!
echo ========================================
echo.
pause
