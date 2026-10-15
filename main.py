#!/usr/bin/env python3
"""
Automated File Organizer  -  Systems Utility & Automation
Organizes files into Images / Documents / Archives / Media / Code (+ Others)
with safe duplicate handling, dry-run preview, logging and error handling.

Examples
  python file_organizer.py                          # interactive mode
  python file_organizer.py ~/Downloads --dry-run    # preview only (no changes)
  python file_organizer.py ~/Downloads -t ~/Sorted  # organize into another folder
  python file_organizer.py ~/Downloads -r -d timestamp
  python file_organizer.py --make-test-dir ./test_dir   # create demo mess
"""

import argparse
import os
import shutil
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------------ rules
CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
               ".svg", ".heic", ".ico", ".raw"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls",
                  ".xlsx", ".csv", ".ppt", ".pptx", ".md", ".epub"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"},
    "Media": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".mp4", ".mkv",
              ".avi", ".mov", ".wmv", ".webm"},
    "Code": {".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".cs", ".go",
             ".rs", ".php", ".rb", ".html", ".css", ".json", ".xml", ".yml",
             ".yaml", ".sh", ".sql", ".ipynb"},
}
OTHER = "Others"
ALL_FOLDERS = list(CATEGORIES) + [OTHER]
EXT_MAP = {ext: cat for cat, exts in CATEGORIES.items() for ext in exts}


def categorize(path: Path) -> str:
    return EXT_MAP.get(path.suffix.lower(), OTHER)


# ------------------------------------------------------------------ logging
class Log:
    """Prints to the console and (optionally) appends to a log file."""

    def __init__(self, path=None):
        self.path = path
        self.fh = open(path, "a", encoding="utf-8") if path else None

    def write(self, msg=""):
        print(msg)
        if self.fh:
            self.fh.write(msg + "\n")
            self.fh.flush()

    def close(self):
        if self.fh:
            self.fh.close()


# ------------------------------------------------------------------ planning
@dataclass
class Op:
    src: Path
    dest: Path
    category: str
    renamed: bool = False


def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def unique_path(dest: Path, strategy: str, reserved: set):
    """Return (path, renamed). Never returns a path that exists or is reserved."""
    def taken(p):
        return p.exists() or str(p).lower() in reserved

    if not taken(dest):
        return dest, False
    stem, suffix = dest.stem, dest.suffix
    if strategy == "timestamp":
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cand = dest.with_name(f"{stem}_{stamp}{suffix}")
        if not taken(cand):
            return cand, True
        stem = f"{stem}_{stamp}"           # same second -> add counter too
    n = 1
    while True:
        cand = dest.with_name(f"{stem}_{n}{suffix}")
        if not taken(cand):
            return cand, True
        n += 1


def scan(source: Path, target: Path, recursive: bool, include_hidden: bool,
         exclude: set):
    """Collect files to organize. Returns (files, skipped, errors)."""
    files, skipped, errors = [], [], []
    skip_dirs = {(target / c).resolve() for c in ALL_FOLDERS}

    def consider(p: Path):
        if p.is_symlink():
            skipped.append((p, "symbolic link"))
        elif p.name.startswith(".") and not include_hidden:
            skipped.append((p, "hidden file"))
        elif p.resolve() in exclude:
            skipped.append((p, "log/script file"))
        elif not p.is_file():
            skipped.append((p, "not a regular file"))
        else:
            files.append(p)

    def on_error(e):
        errors.append((Path(e.filename or "?"), f"cannot read folder: {e.strerror}"))

    if recursive:
        for root, dirs, names in os.walk(source, onerror=on_error):
            root_p = Path(root)
            keep = []
            for d in sorted(dirs):
                dp = root_p / d
                if dp.is_symlink():
                    skipped.append((dp, "symlinked directory"))
                elif dp.resolve() in skip_dirs:
                    continue                      # already-organized folders
                elif d.startswith(".") and not include_hidden:
                    skipped.append((dp, "hidden directory"))
                else:
                    keep.append(d)
            dirs[:] = keep
            for n in sorted(names):
                consider(root_p / n)
    else:
        try:
            entries = sorted(source.iterdir(), key=lambda p: p.name.lower())
        except OSError as e:
            errors.append((source, f"cannot read folder: {e.strerror}"))
            return files, skipped, errors
        for p in entries:
            if p.is_dir() and not p.is_symlink():
                if p.resolve() not in skip_dirs:
                    skipped.append((p, "subdirectory (use --recursive)"))
            else:
                consider(p)
    return files, skipped, errors


def build_plan(files, target: Path, strategy: str):
    """Plan every move. 'reserved' makes planned names unique among themselves,
    so a dry-run predicts exactly what the real run will do."""
    reserved, ops = set(), []
    for src in files:
        cat = categorize(src)
        dest, renamed = unique_path(target / cat / src.name, strategy, reserved)
        reserved.add(str(dest).lower())
        ops.append(Op(src, dest, cat, renamed))
    return ops


# ------------------------------------------------------------------ output
def show_plan(ops, skipped, errors, source, target, log, label):
    log.write(f"\n{label} planned operations ({len(ops)} file(s)):")
    log.write("-" * 70)
    for op in ops:
        note = "  (renamed: name already exists)" if op.renamed else ""
        log.write(f"  MOVE  {rel(op.src, source)}  ->  {rel(op.dest, target)}{note}")
    if not ops:
        log.write("  (nothing to move)")
    if skipped:
        log.write(f"\nSkipped ({len(skipped)}):")
        for p, why in skipped:
            log.write(f"  SKIP  {rel(p, source)}  [{why}]")
    for p, why in errors:
        log.write(f"  ERROR {p}  [{why}]")
    counts = Counter(op.category for op in ops)
    if counts:
        log.write("\nBy category: " +
                  ", ".join(f"{c}: {counts[c]}" for c in ALL_FOLDERS if counts[c]))


def execute(ops, strategy, source, target, log):
    stats = Counter()
    for op in ops:
        try:
            op.dest.parent.mkdir(parents=True, exist_ok=True)
            dest = op.dest
            if dest.exists():                   # changed since planning
                dest, _ = unique_path(dest, strategy, set())
            shutil.move(str(op.src), str(dest))
            stats["moved"] += 1
            if dest != op.dest or op.renamed:
                stats["renamed"] += 1
            log.write(f"  MOVED   {rel(op.src, source)}  ->  {rel(dest, target)}"
                      + ("  (renamed)" if dest != op.dest or op.renamed else ""))
        except PermissionError as e:
            stats["failed"] += 1
            log.write(f"  FAILED  {rel(op.src, source)}  [permission denied / "
                      f"file locked: {e.strerror or e}]")
        except FileNotFoundError:
            stats["failed"] += 1
            log.write(f"  FAILED  {rel(op.src, source)}  [file no longer exists]")
        except OSError as e:
            stats["failed"] += 1
            log.write(f"  FAILED  {rel(op.src, source)}  [{e.strerror or e}]")
    return stats


# ------------------------------------------------------------------ test dir
def make_test_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "Images").mkdir(exist_ok=True)
    (path / "Images" / "photo.jpg").write_text("existing photo (already organized)")
    (path / "sub").mkdir(exist_ok=True)
    (path / "sub" / "nested").mkdir(exist_ok=True)
    files = {
        "photo.jpg": "new photo", "logo.png": "png", "holiday.heic": "heic",
        "report.pdf": "report v1", "notes.txt": "notes", "budget.xlsx": "xlsx",
        "backup.zip": "zip", "old_files.7z": "7z",
        "song.mp3": "mp3", "movie.mp4": "mp4",
        "script.py": "print('hi')", "app.js": "console.log(1)",
        "index.html": "<html></html>",
        "README": "no extension", "data.unknownext": "mystery",
        ".hidden_config": "hidden file",
        "sub/report.pdf": "report v2 (same name as root one)",
        "sub/nested/photo.jpg": "another photo.jpg",
        "sub/nested/song.mp3": "nested song",
        "UPPER.JPG": "uppercase extension",
    }
    for name, content in files.items():
        (path / name).write_text(content)
    print(f"Test directory created at: {path.resolve()}")
    print(f"Try:  python file_organizer.py \"{path}\" --dry-run")
    print(f"Then: python file_organizer.py \"{path}\" --recursive")


# ------------------------------------------------------------------ CLI
def prompt_yes_no(question, default=False):
    hint = "Y/n" if default else "y/N"
    ans = input(f"{question} [{hint}]: ").strip().lower()
    return default if not ans else ans.startswith("y")


def interactive(args):
    print("=== Automated File Organizer (interactive) ===")
    while True:
        s = input("Source folder to organize: ").strip().strip('"')
        if s and Path(s).expanduser().is_dir():
            args.source = s
            break
        print("  ! Not a valid folder, try again.")
    t = input("Target folder (Enter = same as source): ").strip().strip('"')
    args.target = t or None
    d = input("Duplicate names - 'counter' (file_1) or 'timestamp' "
              "[counter]: ").strip().lower()
    args.duplicates = d if d in ("counter", "timestamp") else "counter"
    args.recursive = prompt_yes_no("Include subfolders?", False)
    args.dry_run = prompt_yes_no("Dry-run only (preview, no changes)?", True)
    return args


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Organize files into Images, Documents, Archives, Media, "
                    "Code (and Others) with safe duplicate handling.")
    p.add_argument("source", nargs="?", help="folder to organize "
                   "(omit for interactive mode)")
    p.add_argument("-t", "--target", help="destination root (default: source)")
    p.add_argument("-n", "--dry-run", action="store_true",
                   help="preview planned moves; do not change anything")
    p.add_argument("-r", "--recursive", action="store_true",
                   help="also organize files inside subfolders")
    p.add_argument("-d", "--duplicates", choices=["counter", "timestamp"],
                   default="counter",
                   help="how to rename clashing names (default: counter)")
    p.add_argument("--include-hidden", action="store_true",
                   help="also move hidden (dot) files")
    p.add_argument("--log", metavar="FILE",
                   help="log file path (default for real runs: "
                        "organizer_log_<time>.txt in current folder)")
    p.add_argument("--no-log", action="store_true", help="do not write a log file")
    p.add_argument("-y", "--yes", action="store_true",
                   help="do not ask for confirmation before moving")
    p.add_argument("--make-test-dir", metavar="PATH",
                   help="create a sample messy folder for testing, then exit")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.make_test_dir:
        make_test_dir(Path(args.make_test_dir).expanduser())
        return 0

    interactive_mode = args.source is None
    if interactive_mode:
        args = interactive(args)

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        print(f"Error: source '{source}' is not a folder.")
        return 2
    if source == Path(source.anchor):
        print("Error: refusing to organize a filesystem root.")
        return 2
    target = Path(args.target).expanduser().resolve() if args.target else source
    if target.exists() and not target.is_dir():
        print(f"Error: target '{target}' is not a folder.")
        return 2

    # Log file: real runs log by default; dry-runs only when --log is given
    # (so a dry-run leaves the disk untouched).
    log_path = None
    if not args.no_log:
        if args.log:
            log_path = Path(args.log).expanduser().resolve()
        elif not args.dry_run:
            log_path = Path.cwd() / f"organizer_log_{datetime.now():%Y%m%d_%H%M%S}.txt"
    log = Log(log_path)
    exclude = {Path(__file__).resolve()}
    if log_path:
        exclude.add(log_path)

    mode = "DRY-RUN" if args.dry_run else "EXECUTE"
    log.write(f"File Organizer  |  {datetime.now():%Y-%m-%d %H:%M:%S}  |  mode: {mode}")
    log.write(f"Source : {source}")
    log.write(f"Target : {target}")
    log.write(f"Options: recursive={args.recursive}, duplicates={args.duplicates}, "
              f"hidden={args.include_hidden}")

    files, skipped, errors = scan(source, target, args.recursive,
                                  args.include_hidden, exclude)
    ops = build_plan(files, target, args.duplicates)
    show_plan(ops, skipped, errors, source, target, log,
              "DRY-RUN" if args.dry_run else "PLAN:")

    if args.dry_run:
        log.write("\nDry-run complete. No files were modified.")
        log.close()
        return 0

    if not ops:
        log.write("\nNothing to do.")
        log.close()
        return 0

    if not args.yes and sys.stdin.isatty():
        if not prompt_yes_no(f"\nMove {len(ops)} file(s) now?", False):
            log.write("Cancelled by user. No files were modified.")
            log.close()
            return 0

    log.write("\nEXECUTING:")
    log.write("-" * 70)
    stats = execute(ops, args.duplicates, source, target, log)
    log.write("-" * 70)
    log.write(f"Done. Moved: {stats['moved']}  |  Renamed to avoid overwrite: "
              f"{stats['renamed']}  |  Failed: {stats['failed']}  |  "
              f"Skipped: {len(skipped)}  |  Read errors: {len(errors)}")
    if log_path:
        log.write(f"Log saved to: {log_path}")
    log.close()
    return 1 if (stats["failed"] or errors) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted. Files already moved were not lost.")
        sys.exit(130)