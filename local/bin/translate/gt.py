#!/usr/bin/env python3
import threading
from pathlib import Path
import gi
from googletrans import Translator, LANGUAGES

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib


# Helper to format language names nicely (Googletrans returns codes/names)
def get_languages() -> dict[str, str]:
    # Returns a map of {"English": "en", "Russian": "ru", ...}
    return {name.title(): code for code, name in LANGUAGES.items()}


def copy(text: str) -> bool:
    import subprocess

    return (
        subprocess.run(
            ["wl-copy"], input=text, text=True, capture_output=True
        ).returncode
        == 0
    )


class TranslateWindow(Gtk.ApplicationWindow):
    def __init__(self, app, lang_map):
        super().__init__(
            application=app,
            title="Quick Translate",
            default_width=550,
            default_height=400,
        )
        self.map = lang_map
        self.names = sorted(lang_map.keys())
        self.translator = Translator()
        self._build_ui()

    def _build_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        self.set_child(box)

        head = Gtk.Box(spacing=8)
        self.src = Gtk.DropDown.new_from_strings(self.names)
        self.trg = Gtk.DropDown.new_from_strings(self.names)
        self.src.set_selected(self.names.index("English"))
        self.trg.set_selected(self.names.index("Russian"))

        swap = Gtk.Button(label="⇄")
        swap.connect("clicked", self._on_swap)
        self.btn = Gtk.Button(label="Translate", css_classes=["suggested-action"])
        self.btn.connect("clicked", self.translate)

        for w in [self.src, swap, self.trg, Gtk.Box(hexpand=True), self.btn]:
            head.append(w)
        box.append(head)

        self.inp = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD)
        self.inp.set_size_request(-1, 150)
        box.append(self.inp)

        self.out = Gtk.TextView(
            editable=False, cursor_visible=False, wrap_mode=Gtk.WrapMode.WORD
        )
        box.append(self.out)

        self.stat = Gtk.Label(label="Ready", xalign=0)
        box.append(self.stat)

        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self._on_key)
        self.inp.add_controller(controller)
        self.connect("map", lambda _: self.inp.grab_focus())

    def _on_swap(self, _):
        s, t = self.src.get_selected(), self.trg.get_selected()
        self.src.set_selected(t)
        self.trg.set_selected(s)

    def _on_key(self, ctrl, key, code, state):
        if key in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and not (
            state & (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK)
        ):
            self.translate(None)
            return True
        return False

    def translate(self, _):
        buf = self.inp.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True).strip()
        if not text:
            return

        self.stat.set_text("⏳ Translating...")
        self.btn.set_sensitive(False)
        src_code = self.map[self.names[self.src.get_selected()]]
        trg_code = self.map[self.names[self.trg.get_selected()]]

        threading.Thread(
            target=self._run_trans, args=(text, src_code, trg_code), daemon=True
        ).start()

    def _run_trans(self, text, src, trg):
        try:
            translated = self.translator.translate(text, src=src, dest=trg)
            GLib.idle_add(self._on_finished, translated.text)
        except Exception as e:
            GLib.idle_add(self._on_finished, f"Error: {str(e)}")

    def _on_finished(self, res):
        self.btn.set_sensitive(True)
        if res:
            self.out.get_buffer().set_text(res)
            if copy(res):
                self.stat.set_text(f"📋 Copied: {res[:30]}...")
                return
        self.stat.set_text("Done")


if __name__ == "__main__":
    app = Gtk.Application(application_id="com.github.quicktranslate")
    app.connect("activate", lambda a: TranslateWindow(a, get_languages()).present())
    app.run(None)
