# SkyMind系统启动脚本
# 用途：同时启动前后端服务，后端在当前窗口，前端在新窗口

# 定义路径变量
$VENV_PATH = "D:\Desktop\gitSkyMind\venv"
$FRONTEND_PATH = "D:\Desktop\gitSkyMind\SkyMind\frontend"
$BACKEND_PATH = "D:\Desktop\gitSkyMind\SkyMind\backend"

# 显示欢迎信息
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "               SkyMind 系统启动器" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "正在启动前端和后端服务..." -ForegroundColor Cyan
Write-Host ""

# 检查路径是否存在
if (-not (Test-Path $VENV_PATH)) {
    Write-Host "错误: 虚拟环境路径不存在: $VENV_PATH" -ForegroundColor Red
    Exit 1
}

if (-not (Test-Path $FRONTEND_PATH)) {
    Write-Host "错误: 前端目录不存在: $FRONTEND_PATH" -ForegroundColor Red
    Exit 1
}

if (-not (Test-Path $BACKEND_PATH)) {
    Write-Host "错误: 后端目录不存在: $BACKEND_PATH" -ForegroundColor Red
    Exit 1
}

# 检查前端环境
Write-Host "检查前端环境..." -ForegroundColor Yellow
if (-not (Test-Path "$FRONTEND_PATH\node_modules")) {
    Write-Host "警告: 前端依赖可能未安装。若首次运行，请先在前端窗口中执行 'npm install'" -ForegroundColor Yellow
}

# 启动前端服务（在新PowerShell窗口）
Write-Host "正在启动前端服务..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$FRONTEND_PATH'; Write-Host '正在启动前端服务...' -ForegroundColor Cyan; Write-Host '如果首次运行，请先执行: npm install' -ForegroundColor Yellow; npm run dev"

# 等待1秒，确保前端窗口已经打开
Start-Sleep -Seconds 1

# 在当前窗口激活虚拟环境并启动后端服务
Write-Host "正在准备后端服务..." -ForegroundColor Yellow
Write-Host "当前目录: $(Get-Location)" -ForegroundColor Gray

# 切换到后端目录
Set-Location $BACKEND_PATH
Write-Host "已切换到后端目录: $BACKEND_PATH" -ForegroundColor Gray

# 检查后端环境
if (-not (Test-Path "$VENV_PATH\Scripts\python.exe")) {
    Write-Host "警告: Python虚拟环境可能未正确设置。请确认虚拟环境已创建。" -ForegroundColor Yellow
}

# 激活虚拟环境
try {
    Write-Host "正在激活虚拟环境: $VENV_PATH" -ForegroundColor Gray
    & "$VENV_PATH\Scripts\Activate.ps1"
    
    # 检查虚拟环境是否成功激活
    if ($env:VIRTUAL_ENV) {
        Write-Host "虚拟环境已激活: $env:VIRTUAL_ENV" -ForegroundColor Green
        
        # 启动后端服务
        Write-Host "正在启动后端服务..." -ForegroundColor Yellow
        Write-Host "如果首次运行，请先执行: pip install -r requirements.txt" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "=================================================" -ForegroundColor Cyan
        Write-Host "后端服务启动中..." -ForegroundColor Green
        Write-Host "=================================================" -ForegroundColor Cyan
        python main.py
    } else {
        Write-Host "错误: 无法激活虚拟环境，请检查路径是否正确: $VENV_PATH" -ForegroundColor Red
    }
} catch {
    Write-Host "错误: 激活虚拟环境时出现问题: $_" -ForegroundColor Red
    Write-Host "请确认虚拟环境路径正确，且已正确设置。" -ForegroundColor Yellow
} 