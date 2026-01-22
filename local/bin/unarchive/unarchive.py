#!/usr/bin/env python3
import subprocess
import curses
import tempfile
import shutil
import sys
from pathlib import Path


def get_archive_items(archive):
    """List items in an archive using 'ouch', automatically answering 'Y' to decompression prompt."""
    # Run 'ouch list' with a process interaction to answer 'Y' to the decompression prompt
    result = subprocess.run(
        ["ouch", "list", archive],
        input="Y\n",  # Provide 'Y' as input to automatically confirm the decompression
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()


def curses_selection(stdscr, items, selected):
    """Curses UI for selecting items."""
    curses.curs_set(0)
    idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "↑/↓: move, SPACE: toggle, ENTER: confirm\n")
        for i, item in enumerate(items):
            prefix = "[x]" if selected[i] else "[ ]"
            display = item if len(item) <= 80 else "..." + item[-77:]
            stdscr.addstr(
                i + 1,
                0,
                f"{'> ' if i == idx else '  '}{prefix} {display}",
                curses.A_REVERSE if i == idx else 0,
            )
        stdscr.refresh()
        key = stdscr.getch()
        if key == curses.KEY_UP or key == ord("k"):
            idx = (idx - 1) % len(items)
        elif key == curses.KEY_DOWN or key == ord("j"):
            idx = (idx + 1) % len(items)
        elif key == ord(" "):
            selected[idx] = not selected[idx]
        elif key in (curses.KEY_ENTER, 10, 13):
            break


def select_items(items):
    """Launch the selection UI and return selected items."""
    selected = [False] * len(items)
    curses.wrapper(curses_selection, items, selected)
    return [item for i, item in enumerate(items) if selected[i]]


def decompress_to_tmpfs(archive, selected_items):
    """Decompress the archive to a temp directory and prune unselected files."""
    temp_dir = Path(tempfile.mkdtemp())
    subprocess.run(["ouch", "decompress", archive, "--dir", str(temp_dir)], check=True)
    if selected_items != ["*"]:
        for path in temp_dir.rglob("*"):
            if path.is_file() and str(path.relative_to(temp_dir)) not in selected_items:
                path.unlink()
        for path in sorted(temp_dir.rglob("*"), key=lambda p: -len(str(p.parts))):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()
    return temp_dir


def move_to_destination(temp_dir, dest):
    """Move files to the destination directory."""
    dest = Path(dest)
    for path in temp_dir.rglob("*"):
        if path.is_file():
            target = dest / path.relative_to(temp_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(target))

    shutil.rmtree(temp_dir)
    print(f"Files moved to {dest}")


def main():
    if len(sys.argv) < 2:
        print("Usage: ./script.py <archive> [destination]")
        return
    archive = Path(sys.argv[1])
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else archive.parent / archive.stem
    items = get_archive_items(str(archive))
    if not items:
        print("Archive is empty.")
        return
    selected = select_items(items)
    if not selected:
        print("No items selected.")
        return
    temp_dir = decompress_to_tmpfs(str(archive), selected)
    move_to_destination(temp_dir, dest)


if __name__ == "__main__":
    main()
