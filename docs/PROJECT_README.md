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

## 自动采集（长线任务）

后端启动后会自动在**后台线程**中定时执行文章采集：

- **来源类型**：在「来源配置」中将类型设为 `rss` 或 `api`，并填写 **URL 或配置**（RSS 订阅地址或返回文章列表的 API 地址）。
- **执行节奏**：启动后约 1 分钟执行第一次采集，之后每 **30 分钟** 执行一次（可配置）。
- **去重**：同一来源下已存在相同原文链接的文章不会重复入库。
- **环境变量**（可选，在 `backend/.env` 或环境中设置）：
  - `COLLECT_INTERVAL_SEC`：采集间隔（秒），默认 `1800`（30 分钟）。
  - `COLLECT_FIRST_DELAY_SEC`：启动后首次采集延迟（秒），默认 `60`。

**手动触发一次采集**：`POST http://localhost:8000/collect/run`  
**查看最近一次采集结果**：`GET http://localhost:8000/collect/status`

## API Key 配置

在 `backend/.env` 中配置硅基流动 API（可复制 `backend/.env.example` 为 `.env` 后填写）。  
**请勿将 `.env` 或真实 API Key 提交到 Git。**

## 特性进度

见 `agent-state/features.json` 与 `agent-state/progress.md`。
