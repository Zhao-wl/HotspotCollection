# HotspotCollection 环境初始化脚本 (Windows PowerShell)
# 用途：安装依赖、校验环境、启动开发服务器

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Ensure-Dir { param([string]$Path) if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null } }

Write-Host "`n--- HotspotCollection 环境初始化 ---`n" -ForegroundColor Cyan

# 1. 后端：Python 虚拟环境与依赖
$backendPath = Join-Path $ProjectRoot "backend"
if (Test-Path $backendPath) {
    $venvPath = Join-Path $backendPath ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "[后端] 创建虚拟环境 .venv ..." -ForegroundColor Yellow
        Set-Location $backendPath
        python -m venv .venv
        Set-Location $ProjectRoot
    }
    $pip = Join-Path $venvPath "Scripts\pip.exe"
    $python = Join-Path $venvPath "Scripts\python.exe"
    if (Test-Path $pip) {
        Write-Host "[后端] 安装依赖 (requirements.txt) ..." -ForegroundColor Yellow
        & $pip install -q -r (Join-Path $backendPath "requirements.txt")
        Write-Host "[后端] 依赖安装完成." -ForegroundColor Green
    }
} else {
    Write-Host "[后端] 未找到 backend/ 目录，跳过." -ForegroundColor Gray
}

# 2. 前端：Node 依赖
$frontendPath = Join-Path $ProjectRoot "frontend"
if (Test-Path $frontendPath) {
    $packageJson = Join-Path $frontendPath "package.json"
    if (Test-Path $packageJson) {
        Write-Host "[前端] 安装依赖 (npm install) ..." -ForegroundColor Yellow
        Set-Location $frontendPath
        npm install 2>&1 | Out-Null
        Set-Location $ProjectRoot
        Write-Host "[前端] 依赖安装完成." -ForegroundColor Green
    }
} else {
    Write-Host "[前端] 未找到 frontend/ 目录，跳过." -ForegroundColor Gray
}

# 3. 环境变量示例（不覆盖已有 .env）
$backendEnv = Join-Path $backendPath ".env"
$backendEnvExample = Join-Path $backendPath ".env.example"
if (Test-Path $backendEnvExample) {
    if (-not (Test-Path $backendEnv)) {
        Copy-Item $backendEnvExample $backendEnv
        Write-Host "[配置] 已从 .env.example 创建 .env，请按需填写 API Key." -ForegroundColor Yellow
    }
}

Write-Host "`n--- 启动说明 ---" -ForegroundColor Cyan
Write-Host "  后端:  cd backend && .\.venv\Scripts\activate && uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "  前端:  cd frontend && npm run dev" -ForegroundColor White
Write-Host "  健康检查:  GET http://localhost:8000/health" -ForegroundColor White
Write-Host ""
