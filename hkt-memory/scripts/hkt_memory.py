import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(os.environ.get("HKT_MEMORY_DIR", Path.cwd() / "memory"))


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

ALLOWED_STATUS = {"现行", "过期", "未知"}
ALLOWED_CONFIDENCE = {"高", "中", "低"}

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


def list_dirs(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(entry.name for entry in path.iterdir() if entry.is_dir())


def list_leaf_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(
        entry
        for entry in path.iterdir()
        if entry.is_file() and entry.suffix == ".md" and entry.name != "index.md"
    )


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def leaf_sort_key(leaf_path: Path) -> tuple[bool, datetime]:
    content = read_text(leaf_path)
    updated_at = extract_field(content, "updated_at")
    parsed = parse_datetime(updated_at)
    if parsed:
        return (False, parsed)
    created_at = extract_field(content, "created_at")
    parsed = parse_datetime(created_at)
    if parsed:
        return (False, parsed)
    return (True, datetime.utcfromtimestamp(leaf_path.stat().st_mtime))


def upsert_field(content: str, field: str, value: str) -> str:
    lines = content.split("\n")
    pattern = re.compile(rf"^{re.escape(field)}:\s*.*$")
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = f"{field}: {value}"
            return "\n".join(lines)
    insert_index = None
    for index, line in enumerate(lines):
        if line.strip() == "content:":
            insert_index = index
            break
    if insert_index is None:
        lines.append(f"{field}: {value}")
    else:
        lines.insert(insert_index, f"{field}: {value}")
    return "\n".join(lines)


def find_duplicate_leaf(branch_dir: Path, title: str, content_items: list[str]) -> Path | None:
    if not branch_dir.exists():
        return None
    normalized_title = title.strip().lower()
    normalized_items = {item.strip().lower() for item in content_items if item.strip()}
    for leaf_path in list_leaf_files(branch_dir):
        content = read_text(leaf_path)
        existing_title = (extract_field(content, "title") or "").strip().lower()
        if existing_title and existing_title == normalized_title:
            return leaf_path
        existing_items = {
            line[2:].strip().lower()
            for line in content.split("\n")
            if line.startswith("- ")
        }
        if normalized_items and normalized_items.issubset(existing_items):
            return leaf_path
    return None


def extract_content_items(content: str) -> list[str]:
    items = []
    in_content = False
    for line in content.split("\n"):
        if line.strip() == "content:":
            in_content = True
            continue
        if in_content:
            if line.startswith("- "):
                items.append(line[2:].strip())
            elif line.strip() == "":
                continue
            else:
                break
    return items


def replace_content_items(content: str, items: list[str]) -> str:
    lines = content.split("\n")
    new_lines = []
    in_content = False
    replaced = False
    for line in lines:
        if line.strip() == "content:":
            in_content = True
            replaced = True
            new_lines.append("content:")
            new_lines.extend([f"- {item}" for item in items])
            continue
        if in_content:
            if line.startswith("- "):
                continue
            if line.strip() == "":
                continue
            in_content = False
        if not in_content:
            new_lines.append(line)
    if not replaced:
        new_lines.append("content:")
        new_lines.extend([f"- {item}" for item in items])
    return "\n".join(new_lines)


def validate_status(value: str) -> str:
    if value not in ALLOWED_STATUS:
        raise ValueError(f"status 必须为: {', '.join(sorted(ALLOWED_STATUS))}")
    return value


def validate_confidence(value: str) -> str:
    if value not in ALLOWED_CONFIDENCE:
        raise ValueError(f"confidence 必须为: {', '.join(sorted(ALLOWED_CONFIDENCE))}")
    return value


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
    status = validate_status(args.status or "现行")
    confidence = validate_confidence(args.confidence or "中")
    scope = args.scope or "默认"
    source = args.source or "conversation"
    created_at = datetime.utcnow().isoformat()
    updated_at = created_at
    leaf_id = args.id or f"leaf-{created_at.replace('-', '').replace(':', '')[:13]}-{slugify(title)}"

    root_dir = BASE_DIR / root
    branch_dir = root_dir / branch
    ensure_dir(branch_dir)

    duplicate = find_duplicate_leaf(branch_dir, title, content_items)
    if duplicate:
        if args.merge_duplicate:
            existing = read_text(duplicate)
            existing_items = extract_content_items(existing)
            new_items = [item for item in content_items if item not in existing_items]
            if new_items:
                merged_items = existing_items + new_items
                updated = replace_content_items(existing, merged_items)
                updated = upsert_field(updated, "updated_at", datetime.utcnow().isoformat())
                write_text(duplicate, updated)
                rel = duplicate.relative_to(BASE_DIR)
                root = rel.parts[0]
                branch = rel.parts[1]
                existing_leaf_id = extract_field(updated, "id") or duplicate.stem
                title = extract_field(updated, "title") or existing_leaf_id
                status = extract_field(updated, "status") or status
                ensure_leaf_index(root, branch, existing_leaf_id, title, status, datetime.utcnow().isoformat())
                print(f"检测到重复 Leaf，已合并内容: {duplicate}")
                return
            print(f"检测到重复 Leaf，内容无新增: {duplicate}")
            return
        if args.dedupe:
            print(f"检测到重复 Leaf，已跳过写入: {duplicate}")
            return

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
        f"updated_at: {updated_at}",
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


def remove_root_from_index(root_index_path: Path, root: str) -> None:
    content = read_text(root_index_path)
    if not content:
        return
    lines = [line for line in content.split("\n") if not line.startswith(f"- Root: {root} | ")]
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


def handle_expire(args: argparse.Namespace) -> None:
    leaf_id = args.id.strip()
    leaf_path = find_leaf_path_by_id(leaf_id)
    if not leaf_path:
        raise ValueError(f"未找到 Leaf 文件: {leaf_id}")

    content = read_text(leaf_path)
    new_status = validate_status(args.status or "过期")
    updated_content = upsert_field(content, "status", new_status)
    updated_content = upsert_field(updated_content, "updated_at", datetime.utcnow().isoformat())
    write_text(leaf_path, updated_content)

    rel = leaf_path.relative_to(BASE_DIR)
    root = rel.parts[0]
    branch = rel.parts[1]
    title = extract_field(updated_content, "title") or leaf_id
    updated_at = datetime.utcnow().isoformat()
    ensure_leaf_index(root, branch, leaf_id, title, new_status, updated_at)

    print(f"已更新 Leaf 状态: {leaf_path}")
    print(f"  status: {new_status}")


def handle_prune(args: argparse.Namespace) -> None:
    if not BASE_DIR.exists():
        print("memory 目录不存在")
        return

    before_days = args.before_days
    status_filter = validate_status(args.status) if args.status else "过期"
    cutoff = datetime.utcnow().timestamp() - (before_days * 86400)
    removed = 0

    for root_dir in list_dirs(BASE_DIR):
        root_path = BASE_DIR / root_dir
        for branch_dir in list_dirs(root_path):
            branch_path = root_path / branch_dir
            for leaf_path in list_leaf_files(branch_path):
                content = read_text(leaf_path)
                status = extract_field(content, "status") or "未知"
                if status != status_filter:
                    continue
                updated_at = parse_datetime(extract_field(content, "updated_at"))
                created_at = parse_datetime(extract_field(content, "created_at"))
                timestamp = None
                if updated_at:
                    timestamp = updated_at.timestamp()
                elif created_at:
                    timestamp = created_at.timestamp()
                else:
                    timestamp = leaf_path.stat().st_mtime
                if timestamp > cutoff:
                    continue
                if args.dry_run:
                    print(f"将删除: {leaf_path}")
                else:
                    leaf_id = extract_field(content, "id") or leaf_path.stem
                    leaf_path.unlink()
                    remove_leaf_from_branch_index(branch_path / "index.md", leaf_id)
                    remaining = [p for p in branch_path.iterdir() if p.is_file() and p.name.endswith(".md") and p.name != "index.md"]
                    if len(remaining) == 0 and (branch_path / "index.md").exists():
                        (branch_path / "index.md").unlink()
                        branch_path.rmdir()
                        remove_branch_from_root_index(root_path / "index.md", branch_dir)
                    if not any(entry.is_dir() for entry in root_path.iterdir()):
                        root_index = root_path / "index.md"
                        if root_index.exists():
                            root_index.unlink()
                        remove_root_from_index(BASE_DIR / "index.md", root_dir)
                        root_path.rmdir()
                    removed += 1
    if args.dry_run:
        print("dry-run 完成")
    else:
        print(f"已删除 Leaf: {removed}")


def handle_query(args: argparse.Namespace) -> None:
    depth = args.depth
    limit = args.limit
    root_filter = slugify(args.root) if args.root else None
    branch_filter = slugify(args.branch) if args.branch else None
    keywords = [kw for kw in (args.keyword or []) if kw]
    keywords_norm = [kw.lower() for kw in keywords]
    status_filter = validate_status(args.status) if args.status else None
    strict_keyword = args.strict_keyword
    fallback_leaf_limit = args.fallback_leaf_limit

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
            scored = []
            for leaf_path in leaf_files:
                if count >= limit:
                    break
                content = read_text(leaf_path)
                content_lower = content.lower()
                if status_filter:
                    status_value = extract_field(content, "status") or "未知"
                    if status_value != status_filter:
                        continue
                matched = [keywords[index] for index, kw in enumerate(keywords_norm) if kw in content_lower]
                keyword_score = len(matched)
                keyword_ratio = keyword_score / len(keywords_norm) if keywords_norm else 0
                if keywords_norm and keyword_score == 0:
                    continue
                status_value = extract_field(content, "status") or "未知"
                status_rank = {"现行": 2, "未知": 1, "过期": 0}.get(status_value, 0)
                scored.append(
                    (status_rank, keyword_ratio, keyword_score, leaf_sort_key(leaf_path), leaf_path, content, matched, False)
                )
            if not scored and keywords_norm and not strict_keyword:
                fallback_count = 0
                for leaf_path in leaf_files:
                    if count >= limit or fallback_count >= fallback_leaf_limit:
                        break
                    content = read_text(leaf_path)
                    if status_filter:
                        status_value = extract_field(content, "status") or "未知"
                        if status_value != status_filter:
                            continue
                    status_value = extract_field(content, "status") or "未知"
                    status_rank = {"现行": 2, "未知": 1, "过期": 0}.get(status_value, 0)
                    scored.append((status_rank, 0, 0, leaf_sort_key(leaf_path), leaf_path, content, [], True))
                    fallback_count += 1
            scored = sorted(scored, key=lambda item: (item[0], item[1], item[2], item[3]), reverse=True)
            for _, _, _, _, leaf_path, content, matched, is_fallback in scored:
                if count >= limit:
                    break
                leaf_id = extract_field(content, "id") or leaf_path.stem
                title = extract_field(content, "title") or leaf_path.stem
                status = extract_field(content, "status") or "未知"
                confidence = extract_field(content, "confidence") or "中"
                scope = extract_field(content, "scope") or "默认"
                if is_fallback:
                    reason = "兜底: 最新"
                else:
                    reason = f"命中关键词: {', '.join(matched)}" if matched else "命中关键词: -"
                print(
                    f"    Leaf: {leaf_id} | 标题: {title} | 状态: {status} | 可信度: {confidence} | 适用范围: {scope} | 线索: {reason}"
                )
                count += 1


def handle_tree(args: argparse.Namespace) -> None:
    depth = args.depth
    limit = args.limit
    root_filter = slugify(args.root) if args.root else None
    branch_filter = slugify(args.branch) if args.branch else None

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
            leaf_files = sorted(leaf_files, key=leaf_sort_key, reverse=True)
            for leaf_path in leaf_files:
                if count >= limit:
                    break
                content = read_text(leaf_path)
                leaf_id = extract_field(content, "id") or leaf_path.stem
                title = extract_field(content, "title") or leaf_path.stem
                status = extract_field(content, "status") or "未知"
                print(f"    Leaf: {leaf_id} | 标题: {title} | 状态: {status}")
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
    add_parser.add_argument("--dedupe", action="store_true")
    add_parser.add_argument("--merge-duplicate", action="store_true")

    reclassify_parser = subparsers.add_parser("reclassify")
    reclassify_parser.add_argument("--id", required=True)
    reclassify_parser.add_argument("--branch", required=True)
    reclassify_parser.add_argument("--root")
    reclassify_parser.add_argument("--root-summary")
    reclassify_parser.add_argument("--branch-summary")

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--root")
    query_parser.add_argument("--branch")
    query_parser.add_argument("--keyword", action="append")
    query_parser.add_argument("--depth", type=int, default=1)
    query_parser.add_argument("--limit", type=int, default=20)
    query_parser.add_argument("--fallback-leaf-limit", type=int, default=3)
    query_parser.add_argument("--status")
    query_parser.add_argument("--strict-keyword", action="store_true")

    tree_parser = subparsers.add_parser("tree")
    tree_parser.add_argument("--root")
    tree_parser.add_argument("--branch")
    tree_parser.add_argument("--depth", type=int, default=3)
    tree_parser.add_argument("--limit", type=int, default=200)

    expire_parser = subparsers.add_parser("expire")
    expire_parser.add_argument("--id", required=True)
    expire_parser.add_argument("--status")

    prune_parser = subparsers.add_parser("prune")
    prune_parser.add_argument("--before-days", type=int, default=30)
    prune_parser.add_argument("--status")
    prune_parser.add_argument("--dry-run", action="store_true")

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
    elif args.command == "tree":
        handle_tree(args)
    elif args.command == "expire":
        handle_expire(args)
    elif args.command == "prune":
        handle_prune(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
