# HotspotCollection 项目说明

全栈热点文章收集 Web 应用：React + FastAPI + SQLite。

## 技术栈

- **前端**: React (Vite)
- **后端**: FastAPI + SQLite
- **关键词提取**: [google/langextract](https://github.com/google/langextract)，LLM 使用硅基流动 API（Qwen/Qwen3-8B）

## 首次运行

1. 初始化环境（安装依赖）:
   ```powershell
   .\agent-state\init.ps1
   ```
2. 启动后端:
   ```powershell
   cd backend
   .\.venv\Scripts\activate
   uvicorn app.main:app --reload
   ```
3. 启动前端（新开终端）:
   ```powershell
   cd frontend
   npm run dev
   ```
4. 打开浏览器: http://localhost:5173  
   健康检查: http://localhost:8000/health

**同时启动前后端**：开两个终端，一个执行步骤 2（后端），一个执行步骤 3（前端）。

## API Key 配置

在 `backend/.env` 中配置硅基流动 API（可复制 `backend/.env.example` 为 `.env` 后填写）。  
**请勿将 `.env` 或真实 API Key 提交到 Git。**

## 特性进度

见 `agent-state/features.json` 与 `agent-state/progress.md`。
