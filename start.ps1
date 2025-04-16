# 启动前后端服务的脚本

Write-Host "正在启动 SkyMind 项目..." -ForegroundColor Green

# 定义目录路径
$backendPath = "D:\Desktop\gitSkyMind\SkyMind\backend"
$frontendPath = "D:\Desktop\gitSkyMind\SkyMind\frontend"
$venvPath = "D:\Desktop\gitSkyMind\venv\Scripts\activate.bat"

# 在新窗口中启动后端服务 - 使用cmd以确保虚拟环境正确激活
$backendWindow = Start-Process cmd -ArgumentList "/c", "cd /d $backendPath && call `"$venvPath`" && uvicorn main:app --reload" -PassThru -NoNewWindow:$false

Write-Host "后端服务窗口已打开..." -ForegroundColor Cyan

# 在新窗口中启动前端服务
$frontendWindow = Start-Process cmd -ArgumentList "/c", "cd /d $frontendPath && npm run dev" -PassThru -NoNewWindow:$false

Write-Host "前端服务窗口已打开..." -ForegroundColor Cyan
Write-Host "所有服务已在新窗口中启动！" -ForegroundColor Green
Write-Host "按 Ctrl+C 停止所有服务" -ForegroundColor Yellow

try {
    # 保存进程ID以确保能正确关闭
    $backendProcessId = $backendWindow.Id
    $frontendProcessId = $frontendWindow.Id
    
    # 等待用户按 Ctrl+C
    Write-Host "`n服务正在运行中，按 Ctrl+C 可停止所有服务..." -ForegroundColor Yellow
    while ($true) {
        Start-Sleep -Seconds 1
        
        # 检查进程是否仍然运行中
        if (-not (Get-Process -Id $backendProcessId -ErrorAction SilentlyContinue)) {
            Write-Host "`n后端服务已停止运行" -ForegroundColor Red
            break
        }
        if (-not (Get-Process -Id $frontendProcessId -ErrorAction SilentlyContinue)) {
            Write-Host "`n前端服务已停止运行" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host "`n捕获到异常: $_" -ForegroundColor Red
} finally {
    # 确保强制停止所有进程及其子进程
    Write-Host "`n正在关闭所有服务..." -ForegroundColor Yellow
    
    # 停止后端进程及其所有子进程
    if (Get-Process -Id $backendProcessId -ErrorAction SilentlyContinue) {
        $childProcesses = Get-WmiObject Win32_Process | Where-Object { $_.ParentProcessId -eq $backendProcessId }
        foreach ($process in $childProcesses) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Stop-Process -Id $backendProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "后端服务已关闭" -ForegroundColor Green
    }
    
    # 停止前端进程及其所有子进程
    if (Get-Process -Id $frontendProcessId -ErrorAction SilentlyContinue) {
        $childProcesses = Get-WmiObject Win32_Process | Where-Object { $_.ParentProcessId -eq $frontendProcessId }
        foreach ($process in $childProcesses) {
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        }
        Stop-Process -Id $frontendProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "前端服务已关闭" -ForegroundColor Green
    }
    
    Write-Host "所有服务已成功关闭！" -ForegroundColor Green
} 