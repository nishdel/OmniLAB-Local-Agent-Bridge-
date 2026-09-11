"""Bounded lexical repository search. No shell, index, embeddings or model file access."""
import heapq
import itertools
import os
import re
import time
from pathspec import GitIgnoreSpec
from .bridge import BridgeError
from .files import resolve_selected
from .schemas import compact

EXTENSIONS = set(".py .pyi .js .jsx .ts .tsx .mjs .cjs .cs .go .rs .java .kt .c .h .cpp .hpp .rb .php .swift .sql .sh .ps1 .md .rst .txt .toml .yaml .yml .json .xml .html .css .scss .vue .svelte".split())
BLOCKED_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "__pycache__", ".codex", ".agents", ".idea", ".vscode", "dist", "build", "coverage", "vendor", "bin", "obj"}
SECRET = re.compile(r"(^\.env($|\.)|(^|[._-])(secrets?|credentials?|id_rsa|id_ed25519)([._-]|$)|\.(pem|key|pfx|p12)$)", re.I)
SYMBOL = re.compile(r"^\s*(?:(?:export|default|async|pub|public|private|static)\s+)*(?:def|class|function|interface|enum|struct|trait|fn|func|const|let|var|type)\s+([A-Za-z_$][\w$]*)")
STOP = set("a an the this that for and or to of in on is are with where what how find relevant code files function task please inspect explain identify".split())


def terms(query):
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", query)
    return list(dict.fromkeys(w for w in re.findall(r"[a-z0-9]{2,40}", expanded.lower()) if w not in STOP))[:20]


def scan_repository(config, query, scope=""):
    if config.source_root is None:
        raise BridgeError("Configure source_root before searching repository contents.")
    root, limits = config.source_root, config.search
    if not query.strip() or len(query) > 2000 or not terms(query):
        raise BridgeError("Supply a focused search query with meaningful identifiers or terms (at most 2000 characters).")
    scope = scope.replace("\\", "/").strip("/") if not scope.startswith(("/", "\\")) else scope
    if scope and (scope.startswith(("/", "\\")) or ":" in scope or ".." in scope.split("/")):
        raise BridgeError("Search scope must be a relative directory under source_root.")
    words = terms(query)
    excludes = GitIgnoreSpec.from_lines(limits.exclude)
    coverage = {"files_scanned": 0, "bytes_scanned": 0, "entries_seen": 0, "files_skipped": 0, "limit_reached": False}
    deadline = time.monotonic() + limits.max_seconds
    candidates = []
    stack = [(root, [])]
    while stack:
        if time.monotonic() >= deadline:
            coverage["limit_reached"] = True
            break
        directory, ignores = stack.pop()
        local_ignores = list(ignores)
        try:
            ignore = resolve_selected(root, (directory / ".gitignore").relative_to(root).as_posix())
            with ignore.open("rb") as f:
                rules = f.read(16385)
            if len(rules) <= 16384:
                local_ignores.append((directory, GitIgnoreSpec.from_lines(rules.decode("utf-8-sig").splitlines())))
            else:
                # Cannot safely interpret this directory's ignore policy.
                coverage["limit_reached"] = True
                continue
        except FileNotFoundError:
            pass
        except (OSError, UnicodeError, BridgeError, ValueError):
            coverage["files_skipped"] += 1
            continue
        try:
            remaining = limits.max_entries - coverage["entries_seen"]
            with os.scandir(directory) as iterator:
                entries = list(itertools.islice(iterator, remaining + 1))
            if len(entries) > remaining:
                coverage["limit_reached"] = True
                entries = entries[:remaining]
            coverage["entries_seen"] += len(entries)
            for entry in sorted(entries, key=lambda e: e.name.lower()):
                if time.monotonic() >= deadline or coverage["files_scanned"] >= limits.max_files or coverage["bytes_scanned"] >= limits.max_total_bytes:
                    coverage["limit_reached"] = True
                    break
                try:
                    info = entry.stat(follow_symlinks=False)
                    if entry.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                        coverage["files_skipped"] += 1
                        continue
                    path = directory / entry.name
                    relative = path.relative_to(root).as_posix()
                    is_dir = entry.is_dir(follow_symlinks=False)
                    marked = relative + ("/" if is_dir else "")
                    if (is_dir and (entry.name.lower() in BLOCKED_DIRS or entry.name.startswith("."))) or SECRET.search(entry.name) or excludes.match_file(marked):
                        continue
                    if path == config.data_dir or config.data_dir in path.parents:
                        continue
                    ignored = False
                    for base, spec in local_ignores:
                        match = spec.check_file(path.relative_to(base).as_posix() + ("/" if is_dir else ""))
                        if match.include is not None:
                            ignored = match.include
                    if ignored:
                        continue
                    if scope and not (relative == scope or relative.startswith(scope + "/") or (is_dir and scope.startswith(relative + "/"))):
                        continue
                    if is_dir:
                        stack.append((path, local_ignores))
                        continue
                    if path.suffix.lower() not in EXTENSIONS or entry.name.startswith(".") or len(relative) > 240:
                        continue
                    if info.st_size > limits.max_file_bytes or info.st_size > limits.max_total_bytes - coverage["bytes_scanned"]:
                        coverage["files_skipped"] += 1
                        continue
                    resolved = resolve_selected(root, relative)
                    with resolved.open("rb") as f:
                        raw = f.read(min(limits.max_file_bytes, limits.max_total_bytes - coverage["bytes_scanned"]) + 1)
                    coverage["bytes_scanned"] += len(raw)
                    coverage["files_scanned"] += 1
                    if len(raw) > limits.max_file_bytes or b"\0" in raw:
                        coverage["files_skipped"] += 1
                        continue
                    text = raw.decode("utf-8-sig")
                    evidence, symbols, matches, symbol_matches = [], [], set(), set()
                    path_hits = {w for w in words if w in relative.lower()}
                    for number, line in enumerate(text.splitlines(), 1):
                        hits = {w for w in words if w in line.lower()}
                        symbol = SYMBOL.match(line)
                        if symbol:
                            symbol_matches |= {w for w in words if w in symbol.group(1).lower()}
                        if symbol and (hits or path_hits) and len(symbols) < 3:
                            symbols.append({"name": symbol.group(1)[:100], "line": number})
                        if hits:
                            matches |= hits
                            first = min(line.lower().find(w) for w in hits)
                            excerpt = line[max(0, first - 40):max(0, first - 40) + 140].strip()
                            evidence.append((len(hits) + (2 if symbol else 0), number, excerpt))
                    # Definitions and named implementation paths beat query text
                    # copied into examples/comments. Still bounded lexical search.
                    score = 12 * len(path_hits) + 6 * len(symbol_matches) + 3 * len(matches) + min(4, len(evidence))
                    if score:
                        best = heapq.nlargest(2, evidence, key=lambda e: (e[0], -e[1]))
                        item = {"path": relative, "score": score, "symbols": symbols,
                                "evidence": [{"line": n, "text": s} for _, n, s in best]}
                        candidates.append(item)
                        candidates.sort(key=lambda c: (-c["score"], c["path"]))
                        del candidates[limits.max_candidates:]
                except (OSError, UnicodeError, BridgeError):
                    coverage["files_skipped"] += 1
            if coverage["limit_reached"]:
                break
        except OSError:
            coverage["files_skipped"] += 1
    return candidates, coverage


def candidate_prompt(config, candidates, objective=""):
    kept = []
    for candidate in candidates:
        item = {"id": len(kept), **candidate}
        # Leave room for the task/objective and framing within the model budget.
        if len(compact(kept + [item])) > config.max_input_chars - len(objective) - 32:
            break
        kept.append(item)
    return kept


def evidence_result(candidates, coverage, selection, limit):
    ids = list(dict.fromkeys(selection.get("candidate_ids", [])))
    valid = [i for i in ids if type(i) is int and 0 <= i < len(candidates)]
    uncertainty = selection.get("uncertainties", [])[:3]
    if len(valid) != len(ids):
        uncertainty = ["Model returned unsupported candidate IDs; those IDs were discarded.", *uncertainty][:3]
    result = {"files": [{k: v for k, v in candidates[i].items() if k != "id"} for i in valid[:limit]],
              "coverage": coverage, "uncertainties": uncertainty,
              "next_action": "Codex should inspect the cited lines before deciding or editing.", "truncated": False}
    return result


def fit_evidence(result, budget):
    while len(compact(result).encode()) > budget and result["files"]:
        result["files"].pop()
        result["truncated"] = True
    if len(compact(result).encode()) > budget:
        result["uncertainties"] = []
        result["truncated"] = True
    return result
