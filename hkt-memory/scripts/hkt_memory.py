import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path.cwd() / "memory"


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fa5]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


FORBIDDEN_BRANCH_SLUGS = {
    slugify("对话记录"),
    slugify("临时"),
    slugify("其他"),
    slugify("misc"),
    slugify("temp"),
    slugify("conversation"),
}

TAXONOMY = {
    slugify("HKT记忆系统"): {
        "summary": "HKT 树状记忆系统（渐进式披露 + 主动发现）",
        "branches": [
            {
                "branch": slugify("验收与测试"),
                "summary": "验收标准、测试流程与示例结果",
                "keywords": ["验收", "测试", "validate", "示例", "demo", "回归", "验证"],
            },
            {
                "branch": slugify("工具与脚本"),
                "summary": "CLI/脚本实现、命令使用与行为约束",
                "keywords": ["脚本", "python", "cli", "命令", "参数", "reclassify", "query", "add"],
            },
            {
                "branch": slugify("存储结构"),
                "summary": "目录结构、索引文件与持久化约束",
                "keywords": ["memory/", "index.md", "root", "branch", "leaf", "目录", "索引", "存储"],
            },
            {
                "branch": slugify("检索与披露"),
                "summary": "渐进式披露检索策略与返回控制",
                "keywords": ["渐进", "披露", "depth", "limit", "检索", "返回", "root", "branch", "leaf"],
            },
            {
                "branch": slugify("格式与约束"),
                "summary": "字段模板、规范化输出与冲突处理",
                "keywords": ["字段", "模板", "格式", "status", "confidence", "scope", "source", "规范化", "冲突"],
            },
            {
                "branch": slugify("知识管理"),
                "summary": "分类、裁剪、归档与持续维护规则",
                "keywords": ["分类", "裁剪", "归档", "维护", "规则", "taxonomy"],
            },
        ],
    }
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def update_line(lines: list[str], pattern: re.Pattern, newline: str) -> list[str]:
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = newline
            return lines
    lines.append(newline)
    return lines


def normalize_lines(lines: list[str]) -> str:
    text = "\n".join(lines).strip("\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text + "\n"


def ensure_root_index(root: str, summary: str) -> None:
    ensure_dir(BASE_DIR)
    root_index = BASE_DIR / "index.md"
    content = read_text(root_index)
    lines = content.split("\n") if content else ["# HKT Memory Root Index", ""]
    pattern = re.compile(rf"^- Root: {re.escape(root)} \| Summary: .*$")
    newline = f"- Root: {root} | Summary: {summary}"
    write_text(root_index, normalize_lines(update_line(lines, pattern, newline)))


def ensure_branch_index(root: str, branch: str, summary: str) -> None:
    root_dir = BASE_DIR / root
    ensure_dir(root_dir)
    root_index = root_dir / "index.md"
    content = read_text(root_index)
    lines = content.split("\n") if content else [f"# Root: {root}", "", "## Branches", ""]
    pattern = re.compile(rf"^- Branch: {re.escape(branch)} \| Summary: .*$")
    newline = f"- Branch: {branch} | Summary: {summary}"
    write_text(root_index, normalize_lines(update_line(lines, pattern, newline)))


def ensure_leaf_index(root: str, branch: str, leaf_id: str, title: str, status: str, updated_at: str) -> None:
    branch_dir = BASE_DIR / root / branch
    ensure_dir(branch_dir)
    branch_index = branch_dir / "index.md"
    content = read_text(branch_index)
    lines = content.split("\n") if content else [f"# Branch: {branch}", "", "## Leaves", ""]
    pattern = re.compile(rf"^- Leaf: {re.escape(leaf_id)} \| Title: .*$")
    newline = f"- Leaf: {leaf_id} | Title: {title} | Status: {status} | Updated: {updated_at}"
    write_text(branch_index, normalize_lines(update_line(lines, pattern, newline)))


def handle_init() -> None:
    ensure_dir(BASE_DIR)
    root_index = BASE_DIR / "index.md"
    if not root_index.exists():
        write_text(root_index, "# HKT Memory Root Index\n\n")
    print(f"初始化完成: {root_index}")


def handle_add(args: argparse.Namespace) -> None:
    if not args.root or not args.title or not args.content:
        raise ValueError("缺少必要参数: --root --title --content")

    root = slugify(args.root)
    title = args.title.strip()
    content_items = [item.strip() for item in args.content if item.strip()]

    suggested = suggest_category(root, title, content_items)
    root_summary = args.root_summary or suggested["root_summary"] or args.root

    if args.branch:
        candidate_branch = slugify(args.branch)
    elif args.auto_classify:
        candidate_branch = suggested["branch"]
    else:
        raise ValueError("缺少必要参数: --branch（或使用 --auto-classify 自动分类）")

    if candidate_branch in FORBIDDEN_BRANCH_SLUGS:
        candidate_branch = suggested["branch"]

    branch = candidate_branch
    branch_summary = args.branch_summary or suggested["branch_summary"] or (args.branch if args.branch else branch)
    status = args.status or "现行"
    confidence = args.confidence or "中"
    scope = args.scope or "默认"
    source = args.source or "conversation"
    created_at = datetime.utcnow().isoformat()
    leaf_id = args.id or f"leaf-{created_at.replace('-', '').replace(':', '')[:13]}-{slugify(title)}"

    root_dir = BASE_DIR / root
    branch_dir = root_dir / branch
    ensure_dir(branch_dir)

    ensure_root_index(root, root_summary)
    ensure_branch_index(root, branch, branch_summary)
    ensure_leaf_index(root, branch, leaf_id, title, status, created_at)

    leaf_path = branch_dir / f"{leaf_id}.md"
    leaf_lines = [
        f"id: {leaf_id}",
        f"title: {title}",
        f"status: {status}",
        f"confidence: {confidence}",
        f"scope: {scope}",
        f"created_at: {created_at}",
        f"source: {source}",
        "content:",
    ] + [f"- {item}" for item in content_items] + [""]
    write_text(leaf_path, "\n".join(leaf_lines))
    print(f"已写入 Leaf: {leaf_path}")


def suggest_category(root: str, title: str, content_items: list[str]) -> dict:
    fallback = {
        "root": root,
        "root_summary": root,
        "branch": slugify("知识管理"),
        "branch_summary": "分类、裁剪、归档与持续维护规则",
        "reason": "fallback",
    }
    taxonomy = TAXONOMY.get(root)
    if not taxonomy:
        return fallback

    text = (title + "\n" + "\n".join(content_items)).lower()
    best = None
    best_score = 0
    for item in taxonomy["branches"]:
        score = 0
        for kw in item["keywords"]:
            if kw.lower() in text:
                score += 1
        if score > best_score:
            best_score = score
            best = item

    if not best:
        best = next((b for b in taxonomy["branches"] if b["branch"] == fallback["branch"]), taxonomy["branches"][0])
        return {
            "root": root,
            "root_summary": taxonomy["summary"],
            "branch": best["branch"],
            "branch_summary": best["summary"],
            "reason": "no-keyword-match",
        }

    return {
        "root": root,
        "root_summary": taxonomy["summary"],
        "branch": best["branch"],
        "branch_summary": best["summary"],
        "reason": f"keyword-score={best_score}",
    }


def remove_leaf_from_branch_index(branch_index_path: Path, leaf_id: str) -> None:
    content = read_text(branch_index_path)
    if not content:
        return
    lines = [line for line in content.split("\n") if not line.startswith(f"- Leaf: {leaf_id} | ")]
    write_text(branch_index_path, normalize_lines(lines))


def remove_branch_from_root_index(root_index_path: Path, branch: str) -> None:
    content = read_text(root_index_path)
    if not content:
        return
    lines = [line for line in content.split("\n") if not line.startswith(f"- Branch: {branch} | ")]
    write_text(root_index_path, normalize_lines(lines))


def find_leaf_path_by_id(leaf_id: str) -> Path | None:
    if not BASE_DIR.exists():
        return None
    for path in BASE_DIR.rglob(f"{leaf_id}.md"):
        if path.name == "index.md":
            continue
        return path
    return None


def handle_suggest(args: argparse.Namespace) -> None:
    root = slugify(args.root)
    title = args.title.strip()
    content_items = [item.strip() for item in (args.content or []) if item.strip()]
    suggested = suggest_category(root, title, content_items)
    print(f"Root: {suggested['root']} | 摘要: {suggested['root_summary']}")
    print(f"Branch: {suggested['branch']} | 摘要: {suggested['branch_summary']}")
    print(f"Reason: {suggested['reason']}")


def handle_reclassify(args: argparse.Namespace) -> None:
    leaf_id = args.id.strip()
    leaf_path = find_leaf_path_by_id(leaf_id)
    if not leaf_path:
        raise ValueError(f"未找到 Leaf 文件: {leaf_id}")

    rel = leaf_path.relative_to(BASE_DIR)
    if len(rel.parts) < 3:
        raise ValueError(f"Leaf 路径不符合 memory/<root>/<branch>/<leaf>.md: {leaf_path}")

    old_root = rel.parts[0]
    old_branch = rel.parts[1]

    new_root = slugify(args.root) if args.root else old_root
    new_branch = slugify(args.branch)
    if new_branch in FORBIDDEN_BRANCH_SLUGS:
        raise ValueError("不允许将 Branch 归类为对话记录/临时/其他等泛化分支")

    leaf_content = read_text(leaf_path)
    title = extract_field(leaf_content, "title") or leaf_id
    status = extract_field(leaf_content, "status") or "现行"
    updated_at = datetime.utcnow().isoformat()

    root_summary = args.root_summary or TAXONOMY.get(new_root, {}).get("summary") or new_root
    branch_summary = args.branch_summary
    if not branch_summary:
        taxonomy = TAXONOMY.get(new_root)
        if taxonomy:
            match = next((b for b in taxonomy["branches"] if b["branch"] == new_branch), None)
            if match:
                branch_summary = match["summary"]
    branch_summary = branch_summary or new_branch

    ensure_root_index(new_root, root_summary)
    ensure_branch_index(new_root, new_branch, branch_summary)
    ensure_leaf_index(new_root, new_branch, leaf_id, title, status, updated_at)

    new_dir = BASE_DIR / new_root / new_branch
    ensure_dir(new_dir)
    new_path = new_dir / leaf_path.name
    leaf_path.replace(new_path)

    remove_leaf_from_branch_index(BASE_DIR / old_root / old_branch / "index.md", leaf_id)

    old_branch_dir = BASE_DIR / old_root / old_branch
    remaining = [p for p in old_branch_dir.iterdir() if p.is_file() and p.name.endswith(".md") and p.name != "index.md"]
    if len(remaining) == 0 and (old_branch_dir / "index.md").exists():
        (old_branch_dir / "index.md").unlink()
        old_branch_dir.rmdir()
        remove_branch_from_root_index(BASE_DIR / old_root / "index.md", old_branch)

    print(f"已重新归类 Leaf: {leaf_id}")
    print(f"  from: {old_root}/{old_branch}")
    print(f"  to:   {new_root}/{new_branch}")


def list_dirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [entry.name for entry in path.iterdir() if entry.is_dir()]


def list_leaf_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return [
        entry
        for entry in path.iterdir()
        if entry.is_file() and entry.suffix == ".md" and entry.name != "index.md"
    ]


def read_summary_from_index(path: Path, prefix: str, name: str) -> str | None:
    content = read_text(path)
    match = re.search(
        rf"^- {re.escape(prefix)}: {re.escape(name)} \| Summary: (.*)$", content, re.M
    )
    if not match:
        return None
    return match.group(1).strip()


def extract_field(content: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}:\s*(.*)$", content, re.M)
    if not match:
        return None
    return match.group(1).strip()


def handle_query(args: argparse.Namespace) -> None:
    depth = args.depth
    limit = args.limit
    root_filter = slugify(args.root) if args.root else None
    branch_filter = slugify(args.branch) if args.branch else None
    keyword = args.keyword

    roots = list_dirs(BASE_DIR)
    if root_filter:
        roots = [root for root in roots if root == root_filter]

    count = 0
    for root in roots:
        if count >= limit:
            break
        root_summary = read_summary_from_index(BASE_DIR / "index.md", "Root", root) or root
        print(f"Root: {root} | 摘要: {root_summary}")
        count += 1
        if depth <= 1 or count >= limit:
            continue

        branches = list_dirs(BASE_DIR / root)
        if branch_filter:
            branches = [branch for branch in branches if branch == branch_filter]
        for branch in branches:
            if count >= limit:
                break
            branch_summary = (
                read_summary_from_index(BASE_DIR / root / "index.md", "Branch", branch) or branch
            )
            print(f"  Branch: {branch} | 摘要: {branch_summary}")
            count += 1
            if depth <= 2 or count >= limit:
                continue

            leaf_files = list_leaf_files(BASE_DIR / root / branch)
            for leaf_path in leaf_files:
                if count >= limit:
                    break
                content = read_text(leaf_path)
                if keyword and keyword not in content:
                    continue
                leaf_id = extract_field(content, "id") or leaf_path.stem
                title = extract_field(content, "title") or leaf_path.stem
                status = extract_field(content, "status") or "未知"
                confidence = extract_field(content, "confidence") or "中"
                scope = extract_field(content, "scope") or "默认"
                print(
                    f"    Leaf: {leaf_id} | 标题: {title} | 状态: {status} | 可信度: {confidence} | 适用范围: {scope}"
                )
                count += 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hkt-memory", add_help=True)
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init")

    suggest_parser = subparsers.add_parser("suggest")
    suggest_parser.add_argument("--root", required=True)
    suggest_parser.add_argument("--title", required=True)
    suggest_parser.add_argument("--content", action="append")

    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("--root", required=True)
    add_parser.add_argument("--branch")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--content", action="append", required=True)
    add_parser.add_argument("--root-summary")
    add_parser.add_argument("--branch-summary")
    add_parser.add_argument("--auto-classify", action="store_true")
    add_parser.add_argument("--status")
    add_parser.add_argument("--confidence")
    add_parser.add_argument("--scope")
    add_parser.add_argument("--source")
    add_parser.add_argument("--id")

    reclassify_parser = subparsers.add_parser("reclassify")
    reclassify_parser.add_argument("--id", required=True)
    reclassify_parser.add_argument("--branch", required=True)
    reclassify_parser.add_argument("--root")
    reclassify_parser.add_argument("--root-summary")
    reclassify_parser.add_argument("--branch-summary")

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--root")
    query_parser.add_argument("--branch")
    query_parser.add_argument("--keyword")
    query_parser.add_argument("--depth", type=int, default=1)
    query_parser.add_argument("--limit", type=int, default=20)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "init":
        handle_init()
    elif args.command == "suggest":
        handle_suggest(args)
    elif args.command == "add":
        handle_add(args)
    elif args.command == "reclassify":
        handle_reclassify(args)
    elif args.command == "query":
        handle_query(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
