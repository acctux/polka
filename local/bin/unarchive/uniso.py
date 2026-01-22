#!/usr/bin/env python3
import subprocess
import curses
from pathlib import Path
import sys


# ------------------- Tree Node -------------------
class Node:
    def __init__(self, name, path, is_dir=False):
        self.name = name
        self.path = path
        self.is_dir = is_dir
        self.children = []
        self.expanded = False
        self.selected = False


def build_tree(file_list):
    root = Node("", "", True)
    nodes = {"": root}
    for f in file_list:
        parts = f.strip("/").split("/")
        for i in range(len(parts)):
            parent_path = "/".join(parts[:i])
            current_path = "/".join(parts[: i + 1])
            if current_path not in nodes:
                node = Node(parts[i], current_path)
                nodes[current_path] = node
                nodes[parent_path].children.append(node)
    # mark directories
    for n in nodes.values():
        if n.children:
            n.is_dir = True
    root.expanded = True
    return root


def flatten_visible(node):
    result = []

    def _recurse(n, depth):
        if n.path:
            result.append((n, depth))
        if n.is_dir and n.expanded:
            for child in sorted(n.children, key=lambda x: (not x.is_dir, x.name)):
                _recurse(child, depth + 1)

    _recurse(node, 0)
    return result


# ------------------- Curses Browser -------------------
def curses_browser(stdscr, root):
    curses.curs_set(0)
    stdscr.keypad(True)
    idx = 0
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        visible = flatten_visible(root)
        stdscr.addstr(
            0, 0, "↑/↓: move  SPACE: select  o: expand/collapse  ENTER: confirm\n"
        )
        for i, (node, depth) in enumerate(visible):
            prefix = "[x]" if node.selected else "[ ]"
            arrow = (
                "▼" if node.is_dir and node.expanded else "▶" if node.is_dir else " "
            )
            line = f"{'  ' * depth}{arrow} {prefix} {node.name}{'/' if node.is_dir else ''}"
            if i + 1 < height:
                stdscr.addstr(
                    i + 1, 0, line[: width - 1], curses.A_REVERSE if i == idx else 0
                )
        stdscr.refresh()

        key = stdscr.getch()
        node = visible[idx][0]
        if key in (curses.KEY_UP, ord("k")):
            idx = (idx - 1) % len(visible)
        elif key in (curses.KEY_DOWN, ord("j")):
            idx = (idx + 1) % len(visible)
        elif key == ord(" "):
            node.selected = not node.selected
        elif key in (ord("o"), ord("O")) and node.is_dir:
            node.expanded = not node.expanded
        elif key in (curses.KEY_ENTER, 10, 13):
            break

    return [n.path for n, d in visible if n.selected and not n.is_dir]


# ------------------- ISO Functions -------------------
def get_iso_items(iso: Path):
    output = subprocess.run(
        ["7z", "l", "-ba", str(iso)], capture_output=True, text=True, check=True
    )
    files = []
    for line in output.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 6:
            files.append(" ".join(parts[5:]).strip())
    return files


def extract_file(iso: Path, file_path: str, dest: Path):
    target = dest / file_path
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["7z", "e", str(iso), file_path, f"-o{target.parent}", "-y"], check=True
    )


# ------------------- Main -------------------
def main():
    if len(sys.argv) < 2:
        print("Usage: ./iso_browser_7z.py <iso> [destination]")
        return
    iso = Path(sys.argv[1])
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else iso.parent / iso.stem
    items = get_iso_items(iso)
    if not items:
        print("ISO is empty.")
        return
    root = build_tree(items)
    selected = curses.wrapper(curses_browser, root)
    if not selected:
        print("No files selected.")
        return
    for f in selected:
        extract_file(iso, f, dest)
    print(f"Selected files extracted to {dest}")


if __name__ == "__main__":
    main()
