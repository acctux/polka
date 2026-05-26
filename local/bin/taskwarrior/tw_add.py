#!/usr/bin/env python3

from pathlib import Path
import yaml
import subprocess


FILE = Path(__file__).parent / "dates.yaml"


# ---------- IO ----------
def load_events():
    with open(FILE, "r") as f:
        return yaml.safe_load(f)["events"]


def save_events(events):
    with open(FILE, "w") as f:
        yaml.dump({"events": events}, f, sort_keys=False)


# ---------- DELETE ----------
def run_delete_picker(events):
    cmd = [
        "zenity",
        "--list",
        "--title=Delete Event",
        "--text=Select event to delete",
        "--column=Name",
        "--column=Date",
        "--column=Due Days",
        "--print-column=1",
        "--height=400",
        "--width=600",
    ]

    for e in events:
        cmd += [e["name"], e["date"], str(e["due_days"])]

    return subprocess.run(cmd, text=True, capture_output=True).stdout.strip() or None


def delete_event(name):
    events = load_events()
    save_events([e for e in events if e["name"] != name])


# ---------- CREATE ----------
def create_event():
    name = subprocess.run(
        ["zenity", "--entry", "--title=New Event", "--text=Event name"],
        text=True,
        capture_output=True,
    ).stdout.strip()
    if not name:
        return
    date = subprocess.run(
        ["zenity", "--entry", "--title=New Event", "--text=Date (Sun or 02-14)"],
        text=True,
        capture_output=True,
    ).stdout.strip()
    if not date:
        return
    due_days = subprocess.run(
        ["zenity", "--entry", "--title=New Event", "--text=Due days"],
        text=True,
        capture_output=True,
    ).stdout.strip()
    if not due_days:
        return
    events = load_events()
    events.append({"name": name, "date": date, "due_days": int(due_days)})
    save_events(events)
    print(f"+ created: {name}")


# ---------- MAIN MENU ----------
def main_menu():
    cmd = [
        "zenity",
        "--list",
        "--title=Event Manager",
        "--text=Choose action",
        "--column=Action",
        "--print-column=1",
    ]
    cmd += [
        "Create Event",
        "Delete Event",
        "Quit",
    ]
    return subprocess.run(cmd, text=True, capture_output=True).stdout.strip() or None


def main():
    choice = main_menu()
    if choice == "Create Event":
        create_event()
    elif choice == "Delete Event":
        events = load_events()
        selected = run_delete_picker(events)
        if selected:
            delete_event(selected)
            print(f"- deleted: {selected}")
    else:
        return


if __name__ == "__main__":
    main()
