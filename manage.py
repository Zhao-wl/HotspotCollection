#!/usr/bin/env python3
"""
Long-Running Agent Harness - 管理工具

基于 Cursor IDE 的长时间运行 Agent 框架辅助 CLI。
纯 Python 标准库实现，无需安装任何外部依赖。

用法:
    python manage.py init          初始化框架（创建目录、规则文件、模板）
    python manage.py status        查看当前项目进度
    python manage.py validate      验证状态文件格式是否正确
    python manage.py reset         重置所有状态（需确认）
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

# ─── 常量 ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
AGENT_STATE_DIR = BASE_DIR / "agent-state"
FEATURES_FILE = AGENT_STATE_DIR / "features.json"
PROGRESS_FILE = AGENT_STATE_DIR / "progress.md"
CURSOR_RULES_DIR = BASE_DIR / ".cursor" / "rules"
PROMPTS_DIR = BASE_DIR / "prompts"

# ─── ANSI 颜色（Windows 10+ 终端支持） ──────────────────────────────────────

def _enable_ansi_windows():
    """在 Windows 终端启用 ANSI 转义序列支持并修复编码"""
    if os.name == "nt":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
        # 强制使用 UTF-8 输出，避免 GBK 编码错误
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", buffering=1)
            sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace", buffering=1)

_enable_ansi_windows()

class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    DIM = "\033[2m"


def colorize(text: str, color: str) -> str:
    return f"{color}{text}{Color.RESET}"


def print_header(title: str):
    line = "─" * 50
    print(f"\n{colorize(line, Color.DIM)}")
    print(f"  {colorize(title, Color.BOLD + Color.CYAN)}")
    print(f"{colorize(line, Color.DIM)}\n")


def print_success(msg: str):
    print(f"  {colorize('✓', Color.GREEN)} {msg}")


def print_warning(msg: str):
    print(f"  {colorize('!', Color.YELLOW)} {msg}")


def print_error(msg: str):
    print(f"  {colorize('✗', Color.RED)} {msg}")


def print_info(msg: str):
    print(f"  {colorize('→', Color.BLUE)} {msg}")


# ─── init 命令 ───────────────────────────────────────────────────────────────

def cmd_init():
    """初始化框架：创建所有必要的目录和文件"""
    print_header("初始化 Long-Running Agent Harness")

    # 创建目录
    dirs_to_create = [AGENT_STATE_DIR, CURSOR_RULES_DIR, PROMPTS_DIR]
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        print_success(f"目录就绪: {d.relative_to(BASE_DIR)}")

    # 检查规则文件
    rule_files = list(CURSOR_RULES_DIR.glob("*.mdc"))
    if rule_files:
        print_success(f"Cursor 规则文件已存在 ({len(rule_files)} 个)")
    else:
        print_warning("未找到 Cursor 规则文件 (.mdc)")
        print_info("请确保 .cursor/rules/ 下包含以下规则文件:")
        print_info("  - long-running-harness.mdc")
        print_info("  - progress-tracking.mdc")
        print_info("  - feature-management.mdc")

    # 检查示例文件
    example_features = AGENT_STATE_DIR / "features.example.json"
    example_progress = AGENT_STATE_DIR / "progress.example.md"

    if example_features.exists():
        print_success("特性列表示例文件已存在")
    else:
        print_warning("特性列表示例文件不存在 (features.example.json)")

    if example_progress.exists():
        print_success("进度日志示例文件已存在")
    else:
        print_warning("进度日志示例文件不存在 (progress.example.md)")

    # 检查状态文件（实际的，非示例）
    if FEATURES_FILE.exists():
        print_info("features.json 已存在 — 项目已在进行中")
    else:
        print_info("features.json 不存在 — 首次在 Cursor 中对话时将进入初始化模式")

    if PROGRESS_FILE.exists():
        print_info("progress.md 已存在")
    else:
        print_info("progress.md 不存在 — 将在初始化模式中创建")

    # 检查提示词模板
    prompt_files = list(PROMPTS_DIR.glob("*.md"))
    if prompt_files:
        print_success(f"提示词模板已存在 ({len(prompt_files)} 个)")
    else:
        print_warning("提示词模板目录为空")

    print(f"\n{colorize('初始化完成!', Color.BOLD + Color.GREEN)}")
    print(f"\n  下一步:")
    print(f"  1. 在 Cursor 中打开此项目")
    print(f"  2. 开始新的 Agent 会话")
    print(f"  3. 输入你的项目需求，Agent 将自动进入初始化模式\n")


# ─── status 命令 ─────────────────────────────────────────────────────────────

def cmd_status():
    """显示当前项目进度"""
    print_header("项目进度概览")

    # 检查 features.json
    if not FEATURES_FILE.exists():
        print_warning("features.json 不存在 — 项目尚未初始化")
        print_info("在 Cursor 中开始新会话以初始化项目")
        return

    try:
        with open(FEATURES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print_error(f"无法读取 features.json: {e}")
        return

    project_name = data.get("project", "未命名")
    description = data.get("description", "无描述")
    features = data.get("features", [])

    print(f"  项目: {colorize(project_name, Color.BOLD)}")
    print(f"  描述: {description}")
    print()

    # 统计
    total = len(features)
    passed = sum(1 for f in features if f.get("passes", False))
    remaining = total - passed
    progress_pct = (passed / total * 100) if total > 0 else 0

    # 进度条
    bar_width = 30
    filled = int(bar_width * passed / total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_width - filled)

    if progress_pct == 100:
        bar_color = Color.GREEN
    elif progress_pct >= 50:
        bar_color = Color.YELLOW
    else:
        bar_color = Color.BLUE

    print(f"  进度: {colorize(bar, bar_color)} {passed}/{total} ({progress_pct:.0f}%)")
    print()

    # 已完成的特性
    if passed > 0:
        print(f"  {colorize('已完成:', Color.GREEN)}")
        for feat in features:
            if feat.get("passes", False):
                print(f"    {colorize('✓', Color.GREEN)} [{feat['id']}] {feat['description']}")
        print()

    # 未完成的特性（按优先级排序）
    if remaining > 0:
        pending_features = [f for f in features if not f.get("passes", False)]
        pending_features.sort(key=lambda x: x.get("priority", 999))
        print(f"  {colorize('待完成:', Color.YELLOW)} (按优先级排序)")
        for feat in pending_features:
            priority_str = f"P{feat.get('priority', '?')}"
            cat_str = feat.get("category", "unknown")
            print(
                f"    {colorize('○', Color.YELLOW)} [{feat['id']}] "
                f"{colorize(priority_str, Color.DIM)} "
                f"{colorize(cat_str, Color.DIM)} "
                f"{feat['description']}"
            )
        print()

    # 最近的进度记录
    if PROGRESS_FILE.exists():
        try:
            content = PROGRESS_FILE.read_text(encoding="utf-8")
            # 提取最近的一个 Session 记录
            sessions = re.findall(
                r"## Session \d+.*?(?=## Session |\Z)", content, re.DOTALL
            )
            if sessions:
                latest = sessions[0].strip()
                print(f"  {colorize('最近会话:', Color.CYAN)}")
                for line in latest.split("\n"):
                    print(f"    {line}")
                print()
        except IOError:
            pass


# ─── validate 命令 ───────────────────────────────────────────────────────────

def cmd_validate():
    """验证状态文件格式是否正确"""
    print_header("验证状态文件")

    errors = 0
    warnings = 0

    # 验证 features.json
    print(f"  {colorize('检查 features.json ...', Color.BOLD)}")
    if not FEATURES_FILE.exists():
        print_warning("features.json 不存在（项目尚未初始化，这是正常的）")
        warnings += 1
    else:
        try:
            with open(FEATURES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 检查顶层字段
            required_top = ["project", "description", "features"]
            for field in required_top:
                if field not in data:
                    print_error(f"缺少顶层字段: {field}")
                    errors += 1
                else:
                    print_success(f"顶层字段 '{field}' 存在")

            # 检查 features 数组
            features = data.get("features", [])
            if not isinstance(features, list):
                print_error("'features' 不是数组")
                errors += 1
            elif len(features) == 0:
                print_warning("'features' 数组为空")
                warnings += 1
            else:
                print_success(f"特性列表包含 {len(features)} 个条目")

                # 检查每个特性
                seen_ids = set()
                required_feat = ["id", "category", "priority", "description", "acceptance_criteria", "passes"]
                valid_categories = {"core", "ui", "api", "data", "auth", "testing", "docs", "infra"}

                for i, feat in enumerate(features):
                    feat_id = feat.get("id", f"index-{i}")

                    # 字段完整性
                    for field in required_feat:
                        if field not in feat:
                            print_error(f"[{feat_id}] 缺少字段: {field}")
                            errors += 1

                    # ID 唯一性
                    if feat_id in seen_ids:
                        print_error(f"[{feat_id}] ID 重复")
                        errors += 1
                    seen_ids.add(feat_id)

                    # ID 格式
                    if not re.match(r"^F\d{3,}$", str(feat_id)):
                        print_warning(f"[{feat_id}] ID 格式建议为 F001, F002... 格式")
                        warnings += 1

                    # 分类有效性
                    cat = feat.get("category", "")
                    if cat and cat not in valid_categories:
                        print_warning(f"[{feat_id}] 分类 '{cat}' 不在推荐列表中: {valid_categories}")
                        warnings += 1

                    # 优先级
                    pri = feat.get("priority")
                    if pri is not None and (not isinstance(pri, (int, float)) or pri < 1):
                        print_error(f"[{feat_id}] priority 应为 >= 1 的数字，当前为 {pri}")
                        errors += 1

                    # passes 类型
                    passes = feat.get("passes")
                    if passes is not None and not isinstance(passes, bool):
                        print_error(f"[{feat_id}] passes 应为 boolean，当前为 {type(passes).__name__}")
                        errors += 1

                    # acceptance_criteria
                    ac = feat.get("acceptance_criteria")
                    if ac is not None:
                        if not isinstance(ac, list):
                            print_error(f"[{feat_id}] acceptance_criteria 应为数组")
                            errors += 1
                        elif len(ac) == 0:
                            print_warning(f"[{feat_id}] acceptance_criteria 为空")
                            warnings += 1

        except json.JSONDecodeError as e:
            print_error(f"JSON 解析失败: {e}")
            errors += 1
        except IOError as e:
            print_error(f"文件读取失败: {e}")
            errors += 1

    print()

    # 验证 progress.md
    print(f"  {colorize('检查 progress.md ...', Color.BOLD)}")
    if not PROGRESS_FILE.exists():
        print_warning("progress.md 不存在（项目尚未初始化，这是正常的）")
        warnings += 1
    else:
        try:
            content = PROGRESS_FILE.read_text(encoding="utf-8")

            if not content.strip():
                print_warning("progress.md 为空")
                warnings += 1
            else:
                # 检查标题
                if "# 项目进度日志" in content or "# Project Progress" in content:
                    print_success("包含标题行")
                else:
                    print_warning("缺少标题行（建议以 '# 项目进度日志' 开头）")
                    warnings += 1

                # 检查 Session 记录
                sessions = re.findall(r"## Session (\d+)", content)
                if sessions:
                    print_success(f"包含 {len(sessions)} 个 Session 记录")

                    # 检查编号是否连续
                    nums = [int(s) for s in sessions]
                    # Session 记录是倒序排列的（新的在前），所以反转再检查
                    nums_sorted = sorted(nums)
                    expected = list(range(nums_sorted[0], nums_sorted[-1] + 1))
                    if nums_sorted != expected:
                        print_warning(f"Session 编号不连续: {nums_sorted}，期望: {expected}")
                        warnings += 1
                else:
                    print_warning("未找到 Session 记录")
                    warnings += 1

                # 检查必要字段
                required_fields = ["完成", "下一步"]
                for field in required_fields:
                    if f"**{field}**" in content:
                        print_success(f"包含 '{field}' 字段")
                    else:
                        print_warning(f"缺少 '{field}' 字段")
                        warnings += 1

        except IOError as e:
            print_error(f"文件读取失败: {e}")
            errors += 1

    # 汇总
    print()
    if errors == 0 and warnings == 0:
        print(f"  {colorize('验证通过! 所有文件格式正确。', Color.BOLD + Color.GREEN)}\n")
    elif errors == 0:
        print(f"  {colorize(f'验证完成: {warnings} 个警告, 0 个错误。', Color.BOLD + Color.YELLOW)}\n")
    else:
        print(f"  {colorize(f'验证失败: {errors} 个错误, {warnings} 个警告。', Color.BOLD + Color.RED)}\n")

    return errors


# ─── reset 命令 ──────────────────────────────────────────────────────────────

def cmd_reset():
    """重置所有 Agent 状态文件"""
    print_header("重置 Agent 状态")

    # 列出将要删除的文件
    files_to_remove = []
    if FEATURES_FILE.exists():
        files_to_remove.append(FEATURES_FILE)
    if PROGRESS_FILE.exists():
        files_to_remove.append(PROGRESS_FILE)

    # 查找初始化脚本
    for script_name in ["init.sh", "init.ps1", "init.bat"]:
        script_path = AGENT_STATE_DIR / script_name
        if script_path.exists():
            files_to_remove.append(script_path)

    if not files_to_remove:
        print_info("没有需要重置的状态文件")
        return

    print(f"  将要删除以下文件:")
    for f in files_to_remove:
        print(f"    {colorize('•', Color.RED)} {f.relative_to(BASE_DIR)}")

    print()
    confirm = input(f"  {colorize('确认重置?', Color.BOLD + Color.YELLOW)} (输入 yes 确认): ").strip()
    if confirm.lower() != "yes":
        print_info("已取消")
        return

    for f in files_to_remove:
        try:
            f.unlink()
            print_success(f"已删除: {f.relative_to(BASE_DIR)}")
        except IOError as e:
            print_error(f"删除失败 {f.relative_to(BASE_DIR)}: {e}")

    print(f"\n  {colorize('重置完成!', Color.BOLD + Color.GREEN)}")
    print(f"  下次在 Cursor 中对话时，Agent 将重新进入初始化模式\n")


# ─── 帮助信息 ────────────────────────────────────────────────────────────────

def cmd_help():
    """显示帮助信息"""
    print_header("Long-Running Agent Harness")
    print("  基于 Cursor IDE 的长时间运行 Agent 协作框架")
    print()
    print(f"  {colorize('可用命令:', Color.BOLD)}")
    print()
    commands = [
        ("init", "初始化框架（检查并创建必要的目录和文件）"),
        ("status", "查看当前项目进度（特性完成情况、最近会话）"),
        ("validate", "验证状态文件格式是否正确"),
        ("reset", "重置所有 Agent 状态（需确认，不可撤销）"),
        ("help", "显示此帮助信息"),
    ]
    for cmd, desc in commands:
        print(f"    {colorize(cmd, Color.GREEN):20s}  {desc}")

    print()
    print(f"  {colorize('使用方法:', Color.BOLD)}")
    print(f"    python manage.py <命令>")
    print()
    print(f"  {colorize('示例:', Color.BOLD)}")
    print(f"    python manage.py init       # 初始化框架")
    print(f"    python manage.py status     # 查看进度")
    print()


# ─── 主入口 ──────────────────────────────────────────────────────────────────

def main():
    commands = {
        "init": cmd_init,
        "status": cmd_status,
        "validate": cmd_validate,
        "reset": cmd_reset,
        "help": cmd_help,
    }

    if len(sys.argv) < 2:
        cmd_help()
        sys.exit(0)

    cmd_name = sys.argv[1].lower()

    if cmd_name in ("-h", "--help"):
        cmd_help()
        sys.exit(0)

    if cmd_name not in commands:
        print_error(f"未知命令: {cmd_name}")
        print_info(f"可用命令: {', '.join(commands.keys())}")
        sys.exit(1)

    commands[cmd_name]()


if __name__ == "__main__":
    main()
