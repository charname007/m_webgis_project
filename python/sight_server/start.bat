@echo off
REM Sight Server 快速启动脚本 (Windows)

echo ========================================
echo    Sight Server Quick Start (Windows)
echo ========================================
echo.

REM 检查 Python
echo [1/6] 检查 Python 版本...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [√] Python 版本: %PYTHON_VERSION%
echo.

REM 检查虚拟环境
echo [2/6] 检查虚拟环境...
if not exist "venv" (
    echo [*] 创建虚拟环境...
    python -m venv venv
    echo [√] 虚拟环境已创建
) else (
    echo [√] 虚拟环境已存在
)
echo.

REM 激活虚拟环境
echo [3/6] 激活虚拟环境...
call venv\Scripts\activate.bat
echo [√] 虚拟环境已激活
echo.

REM 安装依赖
echo [4/6] 安装依赖...
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo [√] 依赖安装完成
echo.

REM 检查环境变量
echo [5/6] 检查环境变量...
if not exist ".env" (
    echo [!] 未找到 .env 文件
    if exist ".env.example" (
        echo [*] 从 .env.example 创建 .env...
        copy .env.example .env
        echo.
        echo [!] 请编辑 .env 文件并配置必需的环境变量:
        echo     - DATABASE_URL
        echo     - DEEPSEEK_API_KEY
        echo.
        pause
        notepad .env
    ) else (
        echo [X] 未找到 .env.example 文件
        pause
        exit /b 1
    )
) else (
    echo [√] .env 文件已存在
)
echo.

REM 启动服务
echo [6/6] 启动 Sight Server...
echo ========================================
echo.
echo 访问以下地址:
echo   * API 文档: http://localhost:8001/docs
echo   * ReDoc: http://localhost:8001/redoc
echo   * 健康检查: http://localhost:8001/health
echo.
echo 按 Ctrl+C 停止服务
echo.
echo ========================================
echo.

python main.py

pause
