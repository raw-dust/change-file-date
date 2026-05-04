# change_file_date

Sets file timestamps to match the date/time encoded in the filename. When photos or videos are moved between a phone and a computer, the creation date is often reset, causing files to appear in the wrong order. This script restores the correct timestamp from the filename itself.

Works on **Windows** (sets creation, modified, and accessed times) and **Linux/macOS** (sets modified and accessed times).

## Supported Filename Patterns

| Source | Example |
|---|---|
| Android camera | `IMG_20151021_162900.jpg`, `VID_20151021_162900.mp4` |
| Android variants | `PANO_`, `MVIMG_`, `PORTRAIT_`, `BURST_` |
| Samsung / generic | `20151021_162900.jpg` (no prefix) |
| Android screenshot | `Screenshot_2015-10-21-16-29-00.png` |
| Samsung screenshot | `Screenshot_20151021-162900.png` |
| WhatsApp | `IMG-20151021-WA0001.jpg`, `VID-20151021-WA0001.mp4` |

> **iPhone note:** Stock iOS filenames use sequential numbers (`IMG_0001.HEIC`) with no embedded date, so they cannot be processed by this script.

## Requirements

```
pip install pywin32   # Windows only — needed for setting creation time
```

On Linux/macOS no extra packages are required.

## Usage

```
python change_file_date.py [directory] [options]
```

| Option | Description |
|---|---|
| `directory` | Folder to scan (default: current directory) |
| `-r`, `--recursive` | Process subdirectories recursively |
| `-n`, `--dry-run` | Preview changes without modifying any files |
| `-v`, `--verbose` | Show files that were skipped (no pattern match) |
| `--utc` | Treat filename timestamps as UTC instead of local time |

## Examples

```bash
# Process a single folder
python change_file_date.py "C:\Photos\Vacation"        # Windows
python change_file_date.py ~/Photos/Vacation           # Linux/macOS

# Preview what would change
python change_file_date.py "C:\Photos\Vacation" --dry-run
python change_file_date.py ~/Photos/Vacation --dry-run

# Process all subfolders
python change_file_date.py "C:\Photos" --recursive
python change_file_date.py ~/Photos --recursive

# Show skipped files too
python change_file_date.py "C:\Photos\Vacation" --verbose

# Timestamps are stored in UTC in the filename
python change_file_date.py "C:\Photos\Vacation" --utc
```
