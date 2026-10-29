"""Static analysis of a submission folder.

Nothing here executes submitted code. Files are only read as text and parsed
with the standard library (ast, tokenize, json).
"""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

JUNK_DIRS = {
    "node_modules", "venv", ".venv", "__pycache__", ".pytest_cache",
    "dist", "build", ".idea", ".vscode", ".mypy_cache",
}
COMMITTED_JUNK = {"node_modules", "venv", ".venv", "__pycache__"}
MAX_FILES = 3000
MAX_FILE_BYTES = 500_000

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key id"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "API key (sk-...)"),
    (
        re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[=:]\s*['\"][A-Za-z0-9_\-/+=]{16,}['\"]"),
        "hard-coded credential",
    ),
]
PLACEHOLDER_RE = re.compile(
    r"lorem ipsum|your project (name|title)|add (a )?description here|coming soon|todo: write|insert text here",
    re.I,
)
README_SECTIONS = {
    "overview": ("overview", "about", "introduction", "description", "what it does", "problem"),
    "setup": ("install", "setup", "set up", "getting started", "requirements", "quickstart"),
    "usage": ("usage", "run", "how to", "demo", "example"),
    "approach": ("approach", "architecture", "design", "how it works", "method"),
    "results": ("result", "evaluation", "metrics", "performance", "accuracy"),
    "limits": ("limitation", "future", "next steps", "trade-off", "tradeoff", "known issues"),
}
ENTRYPOINTS = {"app.py", "main.py", "cli.py", "run.py", "__main__.py", "manage.py", "server.py"}
DEP_FILES = {"requirements.txt", "pyproject.toml", "package.json", "environment.yml", "pipfile", "setup.py"}
GENERIC_MESSAGES = {"update", "updates", "fix", "fixes", "final", "done", "changes", "commit", "initial", "wip", "test", "asdf"}


@dataclass
class PyStats:
    files: int = 0
    parse_errors: int = 0
    functions: int = 0
    classes: int = 0
    documented: int = 0
    typed_funcs: int = 0
    long_functions: int = 0
    max_func_len: int = 0
    bare_excepts: int = 0
    total_lines: int = 0
    todo_count: int = 0

    @property
    def definitions(self) -> int:
        return self.functions + self.classes


@dataclass
class Signals:
    name: str
    root: str
    file_count: int = 0
    file_names: list[str] = field(default_factory=list)
    py: PyStats = field(default_factory=PyStats)
    py_texts: dict[str, str] = field(default_factory=dict)
    test_files: int = 0
    test_funcs: int = 0
    asserts: int = 0
    readme_text: str = ""
    readme_words: int = 0
    readme_headings: list[str] = field(default_factory=list)
    readme_sections: set[str] = field(default_factory=set)
    readme_code_blocks: int = 0
    readme_mentions_tests: bool = False
    md_headings: list[str] = field(default_factory=list)
    text_blob: str = ""
    has_dep_file: bool = False
    has_gitignore: bool = False
    has_entrypoint: bool = False
    has_env_example: bool = False
    uses_env_vars: bool = False
    junk_dirs: list[str] = field(default_factory=list)
    committed_env_file: bool = False
    secrets: list[str] = field(default_factory=list)
    placeholders: int = 0
    commits: list[str] | None = None


def _split_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", text))


def _sections(text: str) -> list[tuple[str, int, bool]]:
    """(heading, words in body, body has a fenced code block) for each heading."""
    heads = list(re.finditer(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", text, re.M))
    out = []
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[m.end():end]
        out.append((m.group(1), _split_words(body), "```" in body))
    return out


def _git_commits(root: Path) -> list[str] | None:
    """Commit subjects from git, or from a _commits.txt fixture, or None."""
    if (root / ".git").exists():
        try:
            out = subprocess.run(
                ["git", "-C", str(root), "log", "--format=%s"],
                capture_output=True, text=True, timeout=20, check=True,
            ).stdout
            return [line.strip() for line in out.splitlines() if line.strip()]
        except (subprocess.SubprocessError, OSError):
            return None
    fixture = root / "_commits.txt"
    if fixture.exists():
        return [l.strip() for l in fixture.read_text(errors="ignore").splitlines() if l.strip()]
    return None


def _notebook_code(text: str) -> str:
    try:
        nb = json.loads(text)
    except json.JSONDecodeError:
        return ""
    chunks = []
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            lines = ["pass" if l.lstrip().startswith(("%", "!")) else l for l in src.splitlines()]
            chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


def _scan_python(name: str, text: str, stats: PyStats, long_limit: int, is_test: bool, sig: Signals) -> None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        if not is_test:
            stats.files += 1
        stats.parse_errors += 1
        return
    if is_test:
        # Test files only feed the testing criterion, not code-quality stats.
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                sig.test_funcs += 1
            elif isinstance(node, ast.Assert):
                sig.asserts += 1
            elif isinstance(node, ast.Attribute) and node.attr.startswith("assert"):
                sig.asserts += 1
        return
    stats.files += 1
    stats.total_lines += len(text.splitlines())
    stats.todo_count += len(re.findall(r"\b(TODO|FIXME)\b", text))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            stats.functions += 1
            stats.max_func_len = max(stats.max_func_len, length)
            if length > long_limit:
                stats.long_functions += 1
            if ast.get_docstring(node):
                stats.documented += 1
            if node.returns is not None or any(a.annotation is not None for a in node.args.args):
                stats.typed_funcs += 1
        elif isinstance(node, ast.ClassDef):
            stats.classes += 1
            if ast.get_docstring(node):
                stats.documented += 1
        elif isinstance(node, ast.ExceptHandler) and node.type is None:
            stats.bare_excepts += 1


def analyze(root: str | Path, long_function_lines: int = 40) -> Signals:
    root = Path(root).resolve()
    sig = Signals(name=root.name, root=str(root))
    md_text_parts: list[str] = []
    found_junk: set[str] = set()
    count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        keep = []
        for d in dirnames:
            if d == ".git":
                continue
            if d in JUNK_DIRS:
                found_junk.add(d)
                continue
            keep.append(d)
        dirnames[:] = keep
        for fname in sorted(filenames):
            count += 1
            if count > MAX_FILES:
                break
            path = Path(dirpath) / fname
            rel = path.relative_to(root).as_posix()
            if fname == "_commits.txt":
                continue
            sig.file_names.append(rel)
            low = fname.lower()
            if low in DEP_FILES:
                sig.has_dep_file = True
            if low == ".gitignore":
                sig.has_gitignore = True
            if low == ".env.example":
                sig.has_env_example = True
            if low == ".env":
                sig.committed_env_file = True
            if fname in ENTRYPOINTS or low.endswith(".ipynb"):
                sig.has_entrypoint = True
            try:
                if path.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            suffix = path.suffix.lower()
            if suffix not in {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".ipynb", ".js", ".ts", ".env", ""}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(text):
                    sig.secrets.append(f"{label} in {rel}")
                    break
            if suffix in {".py", ".ipynb"}:
                code = _notebook_code(text) if suffix == ".ipynb" else text
                is_test = bool(re.match(r"test_.*\.py$|.*_test\.py$", fname)) or "tests/" in rel
                if is_test:
                    sig.test_files += 1
                _scan_python(rel, code, sig.py, long_function_lines, is_test, sig)
                if not is_test:
                    sig.py_texts[rel] = code
                if re.search(r"os\.environ|getenv|load_dotenv", code):
                    sig.uses_env_vars = True
            elif suffix == ".md":
                md_text_parts.append(text)
                heads = re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", text, re.M)
                sig.md_headings.extend(heads)
                if low.startswith("readme") and (not sig.readme_text or "/" not in rel):
                    sig.readme_text = text
            if PLACEHOLDER_RE.search(text):
                sig.placeholders += 1

    sig.file_count = count
    ignored = set()
    gi = root / ".gitignore"
    if gi.exists():
        for line in gi.read_text(errors="ignore").splitlines():
            ignored.add(line.strip().strip("/*"))
    # A junk folder only counts against the submission if its own .gitignore does not exclude it.
    sig.junk_dirs = sorted((found_junk & COMMITTED_JUNK) - ignored)

    if sig.readme_text:
        sig.readme_words = _split_words(sig.readme_text)
        sig.readme_headings = re.findall(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", sig.readme_text, re.M)
        sig.readme_code_blocks = sig.readme_text.count("```") // 2
        # A heading only counts as a section if something real sits under it.
        real = [h for h, n, code in _sections(sig.readme_text) if n >= 4 or code]
        heading_blob = " ".join(real).lower()
        for key, words in README_SECTIONS.items():
            if any(w in heading_blob for w in words):
                sig.readme_sections.add(key)
        sig.readme_mentions_tests = bool(re.search(r"pytest|unittest|npm test|run the tests", sig.readme_text, re.I))

    sig.text_blob = ("\n".join(md_text_parts)).lower()
    sig.commits = _git_commits(root)
    return sig
