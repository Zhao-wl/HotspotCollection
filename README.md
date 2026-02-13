# Long-Running Agent Harness for Cursor

基于 [Anthropic 文章](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) 的核心思想，为 Cursor IDE 构建的长时间运行 Agent 协作框架。

## 解决什么问题

当 AI Agent 需要完成跨多个会话的复杂编码项目时，面临两大挑战：

1. **Agent 试图一次性完成所有工作** — 导致上下文溢出，代码半途而废
2. **Agent 在新会话中丢失记忆** — 不知道之前做了什么，重复劳动或宣布过早完成

本框架通过 **Cursor Rules + 状态文件** 解决这两个问题，让 Cursor Agent 能够：
- 将大项目拆分为细粒度特性，每次只做一个
- 跨会话保持记忆（进度日志 + Git 历史）
- 按优先级有序推进，不遗漏功能

## 工作原理

```
                    ┌─────────────────────────┐
                    │      Cursor IDE         │
                    │                         │
  用户聊天 ──────────▶  Agent + Rules ──┐      │
                    │                  │      │
                    └──────────────────┼──────┘
                                       │
                          读写状态文件   ▼
                    ┌─────────────────────────┐
                    │    agent-state/          │
                    │    ├── features.json     │  ◀── 特性清单
                    │    ├── progress.md       │  ◀── 进度日志
                    │    └── init.sh/ps1       │  ◀── 环境脚本
                    └─────────────────────────┘
```

**两阶段工作模式：**

| 阶段 | 触发条件 | Agent 行为 |
|------|----------|-----------|
| 初始化模式 | `features.json` 不存在 | 分析需求 → 生成特性列表 → 搭建脚手架 → 初始提交 |
| 编码模式 | `features.json` 已存在 | 恢复上下文 → 健康检查 → 选择特性 → 增量实现 → 验证提交 |

## 快速开始

### 1. 初始化框架

```bash
python manage.py init
```

这会检查并创建所有必要的目录和文件。

### 2. 开始新项目

在 Cursor 中打开本项目目录，开始一个新的 Agent 会话，输入：

```
我要开始一个新的长期项目。

## 项目描述
构建一个全栈待办事项应用，使用 React + FastAPI + SQLite。
支持用户登录、创建/编辑/删除待办事项、设置优先级。

请按照 long-running-harness 规则进入初始化模式。
```

Agent 会自动：
- 生成 `agent-state/features.json` 特性清单
- 创建项目脚手架和初始化脚本
- 记录进度并做 Git 提交

### 3. 继续开发

每次开始新的 Cursor Agent 会话时：

```
继续开发。请按照 long-running-harness 规则：
1. 读取 agent-state/ 了解当前进度
2. 选择下一个未完成特性
3. 增量实现并验证
```

### 4. 查看进度

```bash
python manage.py status
```

## 项目结构

```
.cursor/rules/
├── long-running-harness.mdc    # 核心规则：两阶段行为逻辑
├── progress-tracking.mdc       # 进度文件读写规范
└── feature-management.mdc      # 特性列表管理规范

agent-state/
├── features.json               # 特性清单（Agent 自动生成）
├── features.example.json       # 特性清单格式示例
├── progress.md                 # 进度日志（Agent 自动维护）
├── progress.example.md         # 进度日志格式示例
└── init.sh / init.ps1          # 环境初始化脚本（Agent 自动生成）

prompts/
├── start-project.md            # "开始新项目"提示词模板
└── continue-work.md            # "继续开发"提示词模板

manage.py                       # 辅助 CLI 工具
```

## CLI 工具

`manage.py` 是一个纯 Python 标准库实现的管理工具，无需安装任何依赖：

| 命令 | 说明 |
|------|------|
| `python manage.py init` | 初始化框架（检查目录和文件） |
| `python manage.py status` | 查看项目进度（特性完成率、最近会话） |
| `python manage.py validate` | 验证状态文件格式是否正确 |
| `python manage.py reset` | 重置所有状态（需确认） |
| `python manage.py help` | 显示帮助信息 |

## 核心设计原则

来自 [Anthropic 的文章](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)：

1. **一次一个特性** — 防止 Agent 贪多嚼不烂，每次只实现一个功能点
2. **不可修改特性定义** — `features.json` 中的特性描述创建后不可修改或删除，只能改 `passes` 字段
3. **先检查后开发** — 每次新会话先恢复上下文、做健康检查，再开始新工作
4. **先修 bug 后开发** — 发现已有功能有问题时，先修复再继续
5. **验证后才标记完成** — 必须通过端到端测试才能将特性标记为 `passes: true`
6. **每个特性都提交** — 完成一个特性后立即 Git commit，保持代码可回退
7. **只追加进度记录** — `progress.md` 只追加不删除，保留完整历史

## 自定义

### 修改规则

编辑 `.cursor/rules/` 下的 `.mdc` 文件来调整 Agent 行为。例如：
- 修改特性分类的定义
- 调整测试验证的严格程度
- 添加特定技术栈的编码规范

### 添加新规则

创建新的 `.mdc` 文件来添加项目特定的规则：

```yaml
---
description: 你的自定义规则描述
alwaysApply: true  # 或 false + globs 限定文件范围
---

你的规则内容...
```

## 灵感来源

- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) - Anthropic Engineering Blog, 2025

## License

MIT
