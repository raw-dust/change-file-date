"""
change_file_date.py

Sets file timestamps to match the date/time encoded in the filename.
Supports naming conventions used by Android, Samsung, WhatsApp, and more.

Works on Windows (sets creation, modified, and accessed times) and
Linux/macOS (sets modified and accessed times).

Supported filename patterns:
  Android camera:     IMG_20151021_162900.jpg, VID_20151021_162900.mp4
  Android variants:   PANO_, MVIMG_, PORTRAIT_, BURST_
  Samsung/generic:    20151021_162900.jpg  (no prefix)
  Android screenshot: Screenshot_2015-10-21-16-29-00.png
  Samsung screenshot: Screenshot_20151021-162900.png
  WhatsApp:           IMG-20151021-WA0001.jpg, VID-20151021-WA0001.mp4
"""

import argparse
import logging
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Filename patterns
# Each regex must use named groups: year, month, day, hour, minute, second.
# Patterns without time groups (e.g. WhatsApp) will default to 00:00:00.
# ---------------------------------------------------------------------------
PATTERNS = [
    # Android camera: IMG_20151021_162900, VID_20151021_162900
    # Variants: PANO_, MVIMG_, PORTRAIT_, BURST_
    re.compile(
        r"^(?:IMG|VID|PANO|MVIMG|PORTRAIT|BURST)_"
        r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
        r"_(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})",
        re.IGNORECASE,
    ),
    # Samsung / generic (no prefix): 20151021_162900
    re.compile(
        r"^(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
        r"_(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})",
        re.IGNORECASE,
    ),
    # Android screenshot (all dashes): Screenshot_2015-10-21-16-29-00
    re.compile(
        r"^Screenshot_"
        r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
        r"-(?P<hour>\d{2})-(?P<minute>\d{2})-(?P<second>\d{2})",
        re.IGNORECASE,
    ),
    # Samsung screenshot (compact): Screenshot_20151021-162900
    re.compile(
        r"^Screenshot_"
        r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})"
        r"-(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})",
        re.IGNORECASE,
    ),
    # WhatsApp (date only): IMG-20151021-WA0001, VID-20151021-WA0001
    # Also: PTT (voice), DOC (document), AUD (audio)
    re.compile(
        r"^(?:IMG|VID|PTT|DOC|AUD)-"
        r"(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})-WA",
        re.IGNORECASE,
    ),
]


def parse_datetime_from_filename(filename: str, use_utc: bool) -> Optional[datetime]:
    """Return a datetime parsed from the filename, or None if no pattern matches."""
    stem = Path(filename).stem
    for pattern in PATTERNS:
        match = pattern.match(stem)
        if not match:
            continue
        groups = match.groupdict()
        try:
            tz = timezone.utc if use_utc else None
            return datetime(
                year=int(groups["year"]),
                month=int(groups["month"]),
                day=int(groups["day"]),
                hour=int(groups.get("hour") or 0),
                minute=int(groups.get("minute") or 0),
                second=int(groups.get("second") or 0),
                tzinfo=tz,
            )
        except ValueError:
            return None
    return None


def set_file_times(path: Path, dt: datetime, dry_run: bool) -> None:
    """Update the file's timestamps. On Windows, also sets the creation time."""
    if dry_run:
        logging.info("[DRY RUN] %s  →  %s", path.name, dt.strftime("%Y-%m-%d %H:%M:%S"))
        return

    timestamp = dt.timestamp()

    # Set modified and accessed times (works on all platforms)
    os.utime(path, (timestamp, timestamp))

    # On Windows, also set creation time via pywin32
    if sys.platform == "win32":
        try:
            import pywintypes
            import win32con
            import win32file

            wintime = pywintypes.Time(dt)
            handle = win32file.CreateFile(
                str(path),
                win32con.GENERIC_WRITE,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                win32con.FILE_ATTRIBUTE_NORMAL,
                None,
            )
            win32file.SetFileTime(handle, wintime, wintime, wintime)
            handle.close()
        except ImportError:
            logging.warning(
                "pywin32 not installed — creation time not updated (modified time was set). "
                "Install with: pip install pywin32"
            )


def process_directory(
    directory: Path, recursive: bool, dry_run: bool, use_utc: bool
) -> tuple:
    """Walk the directory and update timestamps. Returns (matched, skipped, errors)."""
    matched = skipped = errors = 0
    glob_pattern = "**/*" if recursive else "*"

    for file_path in sorted(directory.glob(glob_pattern)):
        if not file_path.is_file():
            continue

        dt = parse_datetime_from_filename(file_path.name, use_utc)
        if dt is None:
            logging.debug("No pattern match: %s", file_path.name)
            skipped += 1
            continue

        try:
            set_file_times(file_path, dt, dry_run)
            if not dry_run:
                logging.info(
                    "%-40s  →  %s",
                    file_path.name,
                    dt.strftime("%Y-%m-%d %H:%M:%S") + (" UTC" if use_utc else ""),
                )
            matched += 1
        except OSError as exc:
            logging.error("Failed to update '%s': %s", file_path.name, exc)
            errors += 1

    return matched, skipped, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Set file timestamps from date/time encoded in filenames.\n"
            "Supports Android, Samsung, WhatsApp, and screenshot naming conventions."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s /path/to/photos\n"
            "  %(prog)s /path/to/photos --recursive\n"
            "  %(prog)s /path/to/photos --dry-run --verbose\n"
            "  %(prog)s /path/to/photos --utc\n"
        ),
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory containing media files (default: current directory)",
    )
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Process subdirectories recursively",
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying any files",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show files that did not match any pattern (skipped files)",
    )
    parser.add_argument(
        "--utc",
        action="store_true",
        help=(
            "Treat filename timestamps as UTC (default: local time). "
            "Use this if your phone stores filenames in UTC."
        ),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        logging.error("Not a directory: %s", directory)
        sys.exit(1)

    logging.info("Scanning: %s", directory)
    if args.dry_run:
        logging.info("Dry run mode — no files will be modified.")

    matched, skipped, errors = process_directory(directory, args.recursive, args.dry_run, args.utc)

    print(f"\nDone: {matched} updated, {skipped} skipped, {errors} error(s).")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
