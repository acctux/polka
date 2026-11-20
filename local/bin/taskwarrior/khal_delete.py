#!/usr/bin/env python3

import re
import subprocess
from pathlib import Path

CALENDAR_DIR = Path.home() / "Desktop/Calendar"
SEPARATOR = "|"


def read_ics_fields(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")

    def get_field(name: str) -> str:
        match = re.search(
            rf"^{name}(?:;[^:]*)?:(.*)$",
            text,
            flags=re.MULTILINE,
        )
        return match.group(1).strip() if match else ""

    summary = get_field("SUMMARY")
    summary = (
        summary.replace(r"\,", ",")
        .replace(r"\;", ";")
        .replace(r"\n", " ")
        .replace(r"\\", "\\")
    )

    start = get_field("DTSTART")
    if len(start) == 8 and start.isdigit():
        start = f"{start[:4]}-{start[4:6]}-{start[6:8]}"

    return {
        "summary": summary or "(untitled)",
        "start": start or "(no date)",
        "uid": get_field("UID"),
    }


def load_cards() -> list[dict[str, str]]:
    cards = []

    for path in sorted(CALENDAR_DIR.glob("*.ics")):
        try:
            fields = read_ics_fields(path)
        except (OSError, UnicodeError):
            continue

        cards.append(
            {
                **fields,
                "path": str(path),
                "label": f"{fields['start']} — {fields['summary']}",
            }
        )

    return cards


def main() -> None:
    cards = load_cards()

    if not cards:
        subprocess.run(
            ["zenity", "--info", "--text", f"No .ics cards found in {CALENDAR_DIR}"],
            check=False,
        )
        return

    command = [
        "zenity",
        "--list",
        "--checklist",
        "--title=Delete Calendar Cards",
        "--text=Check the cards to delete",
        "--column=Delete",
        "--column=Event",
        "--column=Date",
        "--column=UID",
        "--print-column=4",
        f"--separator={SEPARATOR}",
        "--height=600",
        "--width=900",
    ]

    for card in cards:
        command.extend(
            [
                "FALSE",
                card["label"],
                card["start"],
                card["uid"],
            ]
        )

    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return

    selected_uids = set(result.stdout.strip().split(SEPARATOR))
    selected_cards = [card for card in cards if card["uid"] in selected_uids]

    if not selected_cards:
        return

    names = "\n".join(
        f"• {card['summary']} ({card['start']})" for card in selected_cards
    )
    confirm = subprocess.run(
        [
            "zenity",
            "--question",
            "--title=Confirm deletion",
            "--text",
            f"Delete {len(selected_cards)} selected card(s)?\n\n{names}",
            "--width=450",
        ],
        check=False,
    )

    if confirm.returncode != 0:
        return

    for card in selected_cards:
        Path(card["path"]).unlink(missing_ok=True)

    print(f"Deleted {len(selected_cards)} calendar card(s).")


if __name__ == "__main__":
    main()
