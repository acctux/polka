#!/usr/bin/env python3

import subprocess
import threading

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk


def get_languages() -> list[str]:
    try:
        result = subprocess.run(
            ["trans", "-list-languages-english"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError, OSError):
        return ["English", "Russian"]

    languages = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return languages or ["English", "Russian"]


def translate(text: str, source: str, target: str) -> str:
    try:
        result = subprocess.run(
            [
                "trans",
                "-host",
                "google",
                "-source",
                source,
                "-target",
                target,
                "-no-ansi",
                text,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except FileNotFoundError:
        return "Error: `trans` is not installed or could not be found."
    except OSError as error:
        return f"Error: {error}"

    return result.stdout.strip() or result.stderr.strip() or "No output returned."


def copy_to_clipboard(text: str) -> bool:
    try:
        result = subprocess.run(
            ["wl-copy"],
            input=text,
            text=True,
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except OSError:
        return False


class TranslateWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application, languages: list[str]):
        super().__init__(
            application=app,
            title="Quick Translate",
            default_width=550,
            default_height=400,
        )
        self.languages = languages
        self.build_ui()
        self.connect("map", lambda *_: self.input_view.grab_focus())

    def build_ui(self) -> None:
        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=10,
            margin_start=12,
            margin_end=12,
            margin_top=12,
            margin_bottom=12,
        )
        self.set_child(main_box)

        header = Gtk.Box(spacing=8)
        main_box.append(header)

        self.source_dropdown = Gtk.DropDown.new_from_strings(self.languages)
        self.target_dropdown = Gtk.DropDown.new_from_strings(self.languages)
        self.source_dropdown.set_selected(self.language_index("English"))
        self.target_dropdown.set_selected(self.language_index("Russian"))

        swap_button = Gtk.Button(label="⇄")
        swap_button.connect("clicked", self.swap_languages)

        self.translate_button = Gtk.Button(
            label="Translate",
            css_classes=["suggested-action"],
        )
        self.translate_button.connect("clicked", self.start_translation)

        for widget in (
            self.source_dropdown,
            swap_button,
            self.target_dropdown,
            Gtk.Box(hexpand=True),
            self.translate_button,
        ):
            header.append(widget)

        self.input_view = Gtk.TextView(
            wrap_mode=Gtk.WrapMode.WORD,
            height_request=100,
        )
        main_box.append(self.input_view)

        output_scroll = Gtk.ScrolledWindow(vexpand=True)
        output_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.output_view = Gtk.TextView(
            editable=False,
            cursor_visible=False,
            wrap_mode=Gtk.WrapMode.WORD,
        )
        output_scroll.set_child(self.output_view)
        main_box.append(output_scroll)

        self.status_label = Gtk.Label(label="Ready", xalign=0)
        main_box.append(self.status_label)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.input_view.add_controller(key_controller)

    def language_index(self, name: str) -> int:
        try:
            return self.languages.index(name)
        except ValueError:
            return 0

    def swap_languages(self, _button: Gtk.Button) -> None:
        source = self.source_dropdown.get_selected()
        target = self.target_dropdown.get_selected()
        self.source_dropdown.set_selected(target)
        self.target_dropdown.set_selected(source)

    def on_key_pressed(self, _controller, key, _keycode, state) -> bool:
        enter_keys = (Gdk.KEY_Return, Gdk.KEY_KP_Enter)
        modifiers = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK

        if key in enter_keys and not state & modifiers:
            self.start_translation()
            return True

        return False

    def start_translation(self, _button=None) -> None:
        buffer = self.input_view.get_buffer()
        text = buffer.get_text(
            buffer.get_start_iter(),
            buffer.get_end_iter(),
            True,
        ).strip()

        if not text:
            return

        source = self.languages[self.source_dropdown.get_selected()]
        target = self.languages[self.target_dropdown.get_selected()]

        self.status_label.set_text("⏳ Translating...")
        self.translate_button.set_sensitive(False)

        threading.Thread(
            target=self.translation_worker,
            args=(text, source, target),
            daemon=True,
        ).start()

    def translation_worker(self, text: str, source: str, target: str) -> None:
        result = translate(text, source, target)
        GLib.idle_add(self.show_result, text, result)

    def show_result(self, original_text: str, result: str) -> bool:
        self.translate_button.set_sensitive(True)
        self.output_view.get_buffer().set_text(result)

        for line in result.splitlines():
            line = line.strip()
            cleaned = line.lower()

            if (
                not line
                or cleaned == original_text.lower()
                or cleaned.startswith(("/", "["))
                or "definitions of" in cleaned
            ):
                continue

            if copy_to_clipboard(line):
                self.status_label.set_text(f"📋 Copied: {line}")
                return GLib.SOURCE_REMOVE

        self.status_label.set_text("Done")
        return GLib.SOURCE_REMOVE


def main() -> int:
    app = Gtk.Application(application_id="org.nick.quicktranslate")
    app.connect(
        "activate",
        lambda application: TranslateWindow(
            application,
            get_languages(),
        ).present(),
    )
    return app.run(None)


if __name__ == "__main__":
    raise SystemExit(main())
