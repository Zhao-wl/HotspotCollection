# 项目进度日志

## Session 11 - 2026-02-13
- **完成**: F011 文章列表显示 LangExtract 提取的关键词（每条 2-3 个）
- **实现**: 在 `features.json` 中新增 F011；前端文章列表中原「标签」改为「关键词」，使用 `a.tags.slice(0, 3)` 仅展示每篇文章前 2-3 个关键词（来自后端 tags，即 LangExtract 提取结果），分隔符改为顿号「、」。验收：列表每条显示关键词、仅 2-3 个；`npm run build` 通过。
- **下一步**: 可选继续扩展。

## Session 10 - 2026-02-13
- **完成**: F010 支持每个数据来源进行采集
- **实现**: 后端 `app/services/collector.py` 新增 `run_collection_for_source(db, source_id)`，仅对指定 rss/api 且已配置 URL 的来源执行采集并入库，否则返回明确错误；`app/routers/collect.py` 新增 `POST /collect/run/{source_id}`，来源不存在时返回 404。前端在来源配置列表中，对可采集来源（rss 或 api 且已配置 URL）展示「采集」按钮，点击后调用该 API 并展示结果（新增文章数或错误信息）。验收：单来源采集接口可用、类型/URL 校验与错误提示正确、前端按钮与结果展示生效；`npm run build` 通过。
- **下一步**: 可选继续扩展（如定时按来源采集、采集历史等）。

## Session 9 - 2026-02-13
- **完成**: F009 来源配置界面
- **实现**: 前端在文章列表上方新增「来源配置」区块：展示来源列表（名称、类型、URL/配置），支持「添加来源」表单（名称必填，类型下拉 manual/rss/api，URL 或配置可选）、编辑（同表单预填）、删除（二次确认）；与后端 `POST/GET/PATCH/DELETE /sources` 联动，保存后 `refetch` 来源列表，筛选区「来源」下拉同步更新。验收：配置页面与表单可用、增删改与后端联动、持久化后列表生效；`npm run build` 通过。
- **下一步**: 全部特性 (F001–F009) 已完成。

## Session 8 - 2026-02-13
- **完成**: F008 文章标题跳转原文
- **实现**: 前端文章列表中标题改为可点击链接：有 `url` 时渲染为 `<a href={url} target="_blank" rel="noopener noreferrer">`，点击在新标签打开原文；无 url 时仍显示纯文本。`index.css` 增加 `.article-title-link` 及 hover 下划线样式。验收：标题可点击、新标签打开原文；`npm run build` 通过。
- **下一步**: 实现 F009 来源配置界面

## Session 7 - 2026-02-13
- **完成**: F007 文章列表与筛选界面
- **实现**: 前端 `App.jsx` 增加文章列表展示（标题、标签、来源、日期），使用 `useArticles`/`useSources`/`useTags` 从后端 `GET /articles`、`GET /sources`、`GET /tags` 拉取数据；筛选区提供按来源、标签、日期起止的下拉/日期控件，变更时重新请求文章列表；`index.css` 增加 `--muted`。验收：页面展示列表、筛选控件生效、数据来自后端 API；`npm run build` 通过。
- **下一步**: 实现 F008 文章标题跳转原文

## Session 6 - 2026-02-13
- **完成**: F006 文章展示 API（按日期、标签、来源筛选，分页）
- **实现**: `app/schemas/article.py` 新增 `ArticleListResponse`、`TagInArticle`（含 source_name、tags）；`GET /articles` 支持 `tag_id`、`source_id`、`date_from`、`date_to` 筛选及 `limit`/`offset` 分页，返回标题、标签、来源、原文链接、日期；验收在 `tests/test_articles_api.py` 中新增 `test_articles_list_filter_and_pagination`，全部通过。
- **下一步**: 实现 F007 文章列表与筛选界面（前端）

## Session 5 - 2026-02-13
- **完成**: F005 关键词提取与聚合
- **实现**: 集成 `langextract`，通过 `app/config.py` 读取硅基流动 API（SILICONFLOW_API_KEY/BASE_URL/MODEL）；`app/services/keyword_extract.py` 使用 LangExtract + 硅基流动（OpenAI 兼容 base_url）提取关键词；`POST /articles/{id}/extract-keywords` 对文章提取并关联 Tag；`GET /tags` 列表、`GET /articles?tag_id=` 按关键词聚合查询；验收脚本 `tests/test_keywords_api.py` 通过（mock 提取结果，无 API Key 时返回空列表）。
- **下一步**: 实现 F006 文章展示 API（按日期、标签、来源筛选，分页）

## Session 4 - 2026-02-13
- **完成**: F004 文章采集与入库
- **实现**: `app/schemas/article.py`（ArticleCreate/ArticleResponse/ArticleBatchCreate）、`app/routers/articles.py`（GET /articles 列表、POST /articles 单条、POST /articles/batch 批量）、按 source_id 校验来源存在；验收脚本 `tests/test_articles_api.py` 全部通过。
- **下一步**: 实现 F005 关键词提取与聚合

## Session 3 - 2026-02-13
- **完成**: F003 来源配置 API（CRUD）
- **实现**: `app/schemas/source.py`（SourceCreate/Update/Response）、`app/routers/sources.py`（POST/GET/PATCH/DELETE /sources）、在 main 中挂载路由；验收脚本 `tests/test_sources_api.py`（临时文件 DB + TestClient）全部通过。
- **下一步**: 实现 F004 文章采集与入库

## Session 2 - 2026-02-13
- **完成**: F001 项目基础设施验收；F002 后端数据模型
- **F001**: 用 TestClient 验证后端 GET /health；`npm run build` 验证前端；在 `docs/PROJECT_README.md` 中补充「同时启动前后端」说明。四条验收标准均满足。
- **F002**: 新增 `app/database.py`（引擎、Session、init_db）、`app/models.py`（Source、Article、Tag、article_tag 关联表）；在 `main.py` 使用 lifespan 启动时调用 `init_db()` 自动建表。验收：表 sources、articles、tags、article_tag 已创建，应用启动与 /health 正常。
- **下一步**: 实现 F003 来源配置 API（CRUD）

## Session 1 - 2026-02-13
- **完成**: 初始化模式 — 分析需求、生成特性列表、搭建项目脚手架、创建初始化脚本
- **方法**: 根据 docs/demand.md 拆分为 9 个可验证特性（F001–F009），创建 `agent-state/features.json`；搭建 React (Vite) 前端与 FastAPI + SQLite 后端；编写 `agent-state/init.ps1`；补充 `.env.example`、`.gitignore`、`docs/PROJECT_README.md`
- **测试**: 待运行 init.ps1 并验证后端 /health、前端可访问
- **下一步**: 实现 F001 验收（确保一条命令或文档说明可启动前后端），随后进入 F002 数据模型
