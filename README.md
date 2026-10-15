# 📁 Automated File Organizer

A command-line utility that cleans up messy folders by automatically sorting files into category folders — **Images, Documents, Archives, Media, Code** (and **Others**) — with safe duplicate handling, a dry-run preview, logging, and robust error handling.

---

## ✨ Features

- **Automatic categorization** by file extension (case-insensitive, so `.JPG` and `.jpg` are treated the same)
- **Dry-run mode** – preview every planned move without touching a single file
- **Safe duplicate handling** – never overwrites existing files; renames clashes using a counter (`photo_1.jpg`) or a timestamp (`photo_20261015_103000.jpg`)
- **Recursive mode** – optionally organize files inside subfolders
- **Custom target folder** – organize files into a different location than the source
- **Interactive mode** – guided prompts when run without arguments
- **Detailed logging** – every real run writes a timestamped log file
- **Confirmation prompt** – asks before moving files (skip with `--yes`)
- **Skips risky items** – symbolic links, hidden files, the script itself, and its own log file
- **Error handling** – gracefully reports permission errors, locked files, and missing files without crashing
- **Built-in test generator** – create a sample messy folder to try the tool safely
- **Safety guard** – refuses to run on a filesystem root (e.g. `C:\`)

---

## 🗂️ File Categories

| Folder        | Extensions |
|---------------|------------|
| **Images**    | `.jpg` `.jpeg` `.png` `.gif` `.bmp` `.tiff` `.webp` `.svg` `.heic` `.ico` `.raw` |
| **Documents** | `.pdf` `.doc` `.docx` `.txt` `.rtf` `.odt` `.xls` `.xlsx` `.csv` `.ppt` `.pptx` `.md` `.epub` |
| **Archives**  | `.zip` `.rar` `.7z` `.tar` `.gz` `.bz2` `.xz` `.tgz` |
| **Media**     | `.mp3` `.wav` `.flac` `.aac` `.ogg` `.m4a` `.mp4` `.mkv` `.avi` `.mov` `.wmv` `.webm` |
| **Code**      | `.py` `.js` `.ts` `.java` `.c` `.cpp` `.h` `.cs` `.go` `.rs` `.php` `.rb` `.html` `.css` `.json` `.xml` `.yml` `.yaml` `.sh` `.sql` `.ipynb` |
| **Others**    | Anything not listed above |

Categories are defined in the `CATEGORIES` dictionary at the top of the script and are easy to customize.

---

## 🛠️ Tech Stack

| Component | Details |
|-----------|---------|
| **Language** | Python 3.8+ |
| **Libraries** | Standard library only — `argparse`, `os`, `shutil`, `sys`, `pathlib`, `datetime`, `collections`, `dataclasses` |
| **Interface** | Command-line (CLI) with an interactive mode |
| **Platform** | Windows, macOS, Linux |
| **Dependencies** | None — no `pip install` required |

---

## ⚙️ Setup

### 1. Prerequisites

Make sure Python 3.8 or newer is installed:

```bash
python --version
```

If it isn't, download it from [python.org](https://www.python.org/downloads/).

### 2. Get the project

```bash
git clone <your-repository-url>
cd <project-folder>
```

Or simply download `main.py` into a folder of your choice.

### 3. Run it

No installation needed:

```bash
python main.py
```

---

## 🚀 Usage

### Interactive mode

Run without arguments and follow the prompts:

```bash
python main.py
```

You will be asked for:
1. Source folder to organize
2. Target folder (press Enter to use the source folder)
3. Duplicate naming style (`counter` or `timestamp`)
4. Include subfolders? (`y`/`n`)
5. Dry-run only? (`y`/`n`)

### Command-line mode

```bash
# Preview only (no changes made)
python main.py "C:\Users\You\Downloads" --dry-run

# Organize into a different folder
python main.py "C:\Users\You\Downloads" -t "C:\Users\You\Sorted"

# Include subfolders and use timestamps for duplicates
python main.py "C:\Users\You\Downloads" -r -d timestamp

# Skip the confirmation prompt
python main.py "C:\Users\You\Downloads" -y
```

### Try it safely first

Generate a sample messy folder, preview, then run for real:

```bash
python main.py --make-test-dir test_dir
python main.py test_dir --dry-run
python main.py test_dir --recursive
```

---

## 🔧 Command-Line Options

| Option | Description |
|--------|-------------|
| `source` | Folder to organize (omit for interactive mode) |
| `-t`, `--target` | Destination root folder (default: same as source) |
| `-n`, `--dry-run` | Preview planned moves; nothing is changed |
| `-r`, `--recursive` | Also organize files inside subfolders |
| `-d`, `--duplicates` | Rename style for name clashes: `counter` (default) or `timestamp` |
| `--include-hidden` | Also move hidden (dot) files |
| `--log FILE` | Custom log file path |
| `--no-log` | Do not write a log file |
| `-y`, `--yes` | Skip the confirmation prompt |
| `--make-test-dir PATH` | Create a sample messy folder for testing, then exit |

---

## 📋 Example Output

```text
File Organizer  |  2026-10-15 10:30:00  |  mode: DRY-RUN
Source : C:\Users\You\test_dir
Target : C:\Users\You\test_dir
Options: recursive=False, duplicates=counter, hidden=False

DRY-RUN planned operations (14 file(s)):
----------------------------------------------------------------------
  MOVE  logo.png      ->  Images\logo.png
  MOVE  report.pdf    ->  Documents\report.pdf
  MOVE  backup.zip    ->  Archives\backup.zip
  MOVE  song.mp3      ->  Media\song.mp3
  MOVE  script.py     ->  Code\script.py
  MOVE  photo.jpg     ->  Images\photo_1.jpg  (renamed: name already exists)

Skipped (2):
  SKIP  .hidden_config  [hidden file]
  SKIP  sub             [subdirectory (use --recursive)]

Dry-run complete. No files were modified.
```

---

## 🧱 Project Structure

```text
.
├── main.py          # File organizer script
├── README.md        # Project documentation
└── organizer_log_*.txt   # Generated log files (created on real runs)
```

---

## 🔒 Safety Notes

- Always run with `--dry-run` first to review what will happen.
- Existing files are **never overwritten**; clashing names are renamed.
- Symbolic links and hidden files are skipped by default.
- Moves are not automatically undoable — check the generated log file if you need to trace where a file went.

---

## 📄 Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | Completed with failed moves or read errors |
| `2` | Invalid source or target folder |
| `130` | Interrupted by the user (Ctrl+C) |

---

## 🤝 Contributing

Suggestions and improvements are welcome. Fork the repository, create a feature branch, and open a pull request.

## 📜 License

This project is released under the MIT License. Feel free to use and modify it.

---

**Author:** SIHANA FATHIMA AK
