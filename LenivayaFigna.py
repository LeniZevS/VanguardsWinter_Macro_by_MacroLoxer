import glob
import json
import os
import runpy
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser

from Utility import FileCheck

try:
    from PIL import Image, ImageTk
except Exception:
    Image = None
    ImageTk = None


IS_FROZEN = getattr(sys, "frozen", False)
APP_DIR = os.path.dirname(sys.executable) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))
DATA_DIR = getattr(sys, "_MEIPASS", APP_DIR)

POSITION_SCRIPT = os.path.join(DATA_DIR, "Position.py")
WINTER_SCRIPT = os.path.join(DATA_DIR, "Winter_Event.py")
POSITION_SCRIPT_NAME = "Position.py"
WINTER_SCRIPT_NAME = "Winter_Event.py"

CARD_BG = "#090C12"
CARD_BORDER = "#9AA8BC"
TITLE_FG = "#EFF5FF"
MUTED_FG = "#C8D2E2"

CREDIT_LINK = "https://www.youtube.com/@macroLoxer"

UI_SETTINGS_PATH = os.path.join(APP_DIR, "Settings", "UI_Settings.json")
ALLOWED_HOTKEYS = [f"F{i}" for i in range(1, 13)]
DEFAULT_UI_SETTINGS = {
    "position_hotkey": "F1",
    "start_hotkey": "F5",
    "stop_hotkey": "F6",
    "menu_bg_color": "#090C12",
    "menu_border_color": "#9AA8BC",
    "window_bg_color": "#030405",
    "background_image": "",
}

INSTRUCTION_TEXT = {
    "EN": (
        "1. Make sure Click to move and UI navigation is on.\n"
        "2. Unequip all cosmetics and custom cursors. Minimal resolution for working "
        "1300x900 with taskbar hidden.\n"
        "3. Zoom max and look all the way like I do.\n"
        "4. Then press Start."
    ),
    "RU": (
        "\u0031. \u0423\u0431\u0435\u0434\u0438\u0442\u0435\u0441\u044c, \u0447\u0442\u043e \u0432\u043a\u043b\u044e\u0447\u0435\u043d\u044b Click to Move \u0438 UI Navigation.\n"
        "\u0032. \u0421\u043d\u0438\u043c\u0438\u0442\u0435 \u0432\u0441\u0435 \u043a\u043e\u0441\u043c\u0435\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u043f\u0440\u0435\u0434\u043c\u0435\u0442\u044b \u0438 \u043a\u0430\u0441\u0442\u043e\u043c\u043d\u044b\u0435 \u043a\u0443\u0440\u0441\u043e\u0440\u044b. "
        "\u041c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u043e\u0435 \u0440\u0430\u0431\u043e\u0447\u0435\u0435 \u0440\u0430\u0437\u0440\u0435\u0448\u0435\u043d\u0438\u0435 1300x900, \u043f\u0430\u043d\u0435\u043b\u044c \u0437\u0430\u0434\u0430\u0447 \u0441\u043a\u0440\u044b\u0442\u0430.\n"
        "\u0033. \u041c\u0430\u043a\u0441\u0438\u043c\u0430\u043b\u044c\u043d\u043e \u043f\u0440\u0438\u0431\u043b\u0438\u0437\u044c\u0442\u0435 \u043a\u0430\u043c\u0435\u0440\u0443 \u0438 \u043f\u043e\u0441\u043c\u043e\u0442\u0440\u0438\u0442\u0435 \u0432\u043d\u0438\u0437, \u043a\u0430\u043a \u0443 \u043c\u0435\u043d\u044f.\n"
        "\u0034. \u0417\u0430\u0442\u0435\u043c \u043d\u0430\u0436\u043c\u0438\u0442\u0435 Start."
    ),
}


def _first_existing(paths):
    for path in paths:
        if os.path.exists(path):
            return path
    return None


def _is_python_executable(path):
    if not path:
        return False
    name = os.path.basename(path).lower()
    return name.startswith("python")


def _resolve_python(windowless=False):
    search_roots = [APP_DIR]
    if DATA_DIR not in search_roots:
        search_roots.append(DATA_DIR)
    py_meipass_root = os.path.dirname(DATA_DIR)
    if py_meipass_root not in search_roots:
        search_roots.append(py_meipass_root)

    version_dirs = []
    for root in search_roots:
        version_dirs.extend(glob.glob(os.path.join(root, "Python", "python*")))
    version_dirs = sorted(set(version_dirs), reverse=True)
    exe_name = "pythonw.exe" if windowless else "python.exe"
    for version_dir in version_dirs:
        candidate = os.path.join(version_dir, exe_name)
        if os.path.isfile(candidate):
            return candidate

    if windowless:
        pyw_candidate = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if os.path.isfile(pyw_candidate):
            return pyw_candidate
    return sys.executable or "python"


def _find_image_candidates(base_name):
    names = [
        os.path.join(DATA_DIR, "Resources", f"{base_name}.png"),
        os.path.join(DATA_DIR, "Resources", f"{base_name}.jpg"),
        os.path.join(DATA_DIR, "Resources", f"{base_name}.jpeg"),
        os.path.join(APP_DIR, "Resources", f"{base_name}.png"),
        os.path.join(APP_DIR, "Resources", f"{base_name}.jpg"),
        os.path.join(APP_DIR, "Resources", f"{base_name}.jpeg"),
    ]
    return names


def _resolve_worker_script(script_name):
    candidates = [
        os.path.join(APP_DIR, script_name),
        os.path.join(DATA_DIR, script_name),
        os.path.join(os.path.dirname(DATA_DIR), script_name),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def _maybe_run_worker_script():
    if len(sys.argv) < 2:
        return

    requested = os.path.basename(sys.argv[1]).lower()
    worker_map = {
        "position.py": "Position.py",
        "winter_event.py": "Winter_Event.py",
    }
    worker_name = worker_map.get(requested)
    if not worker_name:
        return

    script_path = os.path.join(DATA_DIR, worker_name)
    if not os.path.exists(script_path):
        script_path = os.path.join(APP_DIR, worker_name)
    if not os.path.exists(script_path):
        return

    sys.argv = [script_path, *sys.argv[2:]]
    if DATA_DIR not in sys.path:
        sys.path.insert(0, DATA_DIR)
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    runpy.run_path(script_path, run_name="__main__")
    sys.exit(0)


class LenivayaFignaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.ui_settings = self._load_ui_settings()
        self.position_hotkey = self.ui_settings["position_hotkey"]
        self.start_hotkey = self.ui_settings["start_hotkey"]
        self.stop_hotkey = self.ui_settings["stop_hotkey"]
        self.menu_bg_color = self.ui_settings["menu_bg_color"]
        self.menu_border_color = self.ui_settings["menu_border_color"]
        self.window_bg_color = self.ui_settings["window_bg_color"]
        self.title("LenivayaFigna")
        self.geometry("1100x700")
        self.minsize(980, 620)
        self.configure(bg=self.window_bg_color)

        self.python_exe = _resolve_python(windowless=False)
        self.pythonw_exe = _resolve_python(windowless=True)
        self.create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        self.winter_proc = None
        self.winter_log_thread = None
        self.suppress_winter_exit_log = False
        self.update_thread = None
        self.global_hotkeys = []

        custom_bg = self.ui_settings.get("background_image", "").strip()
        self.background_path = None
        if custom_bg:
            bg_path = custom_bg
            if not os.path.isabs(bg_path):
                bg_path = os.path.join(APP_DIR, bg_path)
            if os.path.exists(bg_path):
                self.background_path = bg_path
        if not self.background_path:
            self.background_path = _first_existing(_find_image_candidates("ui_background")) or _first_existing(
                _find_image_candidates("background")
            )
        self.splash_path = _first_existing(_find_image_candidates("start"))
        self.instruction_images = self._collect_instruction_images()

        self.bg_original = None
        self.bg_photo = None
        self.splash_original = None
        self.splash_photo = None
        self.splash_window = None

        self.instruction_window = None
        self.instruction_lang = "EN"
        self.instruction_index = 0
        self.instruction_photo = None
        self.instruction_pil_cache = {}
        self.settings_window = None
        self.settings_save_button = None
        self.settings_error_label = None
        self.settings_entries = {}
        self.hotkey_vars = {}
        self.color_vars = {}
        self.custom_background_var = None

        self._build_ui()
        self._register_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(1000, self._poll_process_state)
        self.after(30, self._start_with_splash)

    def _collect_instruction_images(self):
        images = []
        seen = set()
        # Requested order: image2 -> image3 -> image4 -> image1
        for idx in (2, 3, 4, 1):
            for path in _find_image_candidates(f"image{idx}"):
                if os.path.exists(path):
                    normalized = os.path.normcase(os.path.abspath(path))
                    if normalized not in seen:
                        images.append(path)
                        seen.add(normalized)
                    break
        return images

    def _normalize_hotkey(self, value):
        normalized = str(value).strip().upper()
        return normalized

    def _is_valid_hex_color(self, value):
        if not isinstance(value, str):
            return False
        text = value.strip()
        if len(text) != 7 or not text.startswith("#"):
            return False
        try:
            int(text[1:], 16)
            return True
        except ValueError:
            return False

    def _load_ui_settings(self):
        settings = dict(DEFAULT_UI_SETTINGS)
        try:
            if os.path.exists(UI_SETTINGS_PATH):
                with open(UI_SETTINGS_PATH, "r", encoding="utf-8") as settings_file:
                    data = json.load(settings_file)
                if isinstance(data, dict):
                    settings.update(data)
        except Exception:
            pass

        settings["position_hotkey"] = self._normalize_hotkey(settings.get("position_hotkey", "F1"))
        settings["start_hotkey"] = self._normalize_hotkey(settings.get("start_hotkey", "F5"))
        settings["stop_hotkey"] = self._normalize_hotkey(settings.get("stop_hotkey", "F6"))

        for key, default in (
            ("menu_bg_color", DEFAULT_UI_SETTINGS["menu_bg_color"]),
            ("menu_border_color", DEFAULT_UI_SETTINGS["menu_border_color"]),
            ("window_bg_color", DEFAULT_UI_SETTINGS["window_bg_color"]),
        ):
            color_value = str(settings.get(key, default)).strip()
            settings[key] = color_value if self._is_valid_hex_color(color_value) else default

        settings["background_image"] = str(settings.get("background_image", "")).strip()

        if settings["position_hotkey"] not in ALLOWED_HOTKEYS:
            settings["position_hotkey"] = DEFAULT_UI_SETTINGS["position_hotkey"]
        if settings["start_hotkey"] not in ALLOWED_HOTKEYS:
            settings["start_hotkey"] = DEFAULT_UI_SETTINGS["start_hotkey"]
        if settings["stop_hotkey"] not in ALLOWED_HOTKEYS:
            settings["stop_hotkey"] = DEFAULT_UI_SETTINGS["stop_hotkey"]

        key_set = {
            settings["position_hotkey"],
            settings["start_hotkey"],
            settings["stop_hotkey"],
        }
        if len(key_set) != 3:
            settings["position_hotkey"] = DEFAULT_UI_SETTINGS["position_hotkey"]
            settings["start_hotkey"] = DEFAULT_UI_SETTINGS["start_hotkey"]
            settings["stop_hotkey"] = DEFAULT_UI_SETTINGS["stop_hotkey"]

        return settings

    def _hotkeys_hint_text(self):
        return (
            f"{self.position_hotkey} - Position\n"
            f"{self.start_hotkey} - Start\n"
            f"{self.stop_hotkey} - Stop"
        )

    def _restart_application(self):
        try:
            if IS_FROZEN:
                command = [sys.executable]
            else:
                main_path = os.path.join(APP_DIR, "Main.py")
                if os.path.exists(main_path):
                    command = [self.python_exe if _is_python_executable(self.python_exe) else sys.executable, main_path]
                else:
                    command = [self.python_exe if _is_python_executable(self.python_exe) else sys.executable, os.path.abspath(__file__)]
            subprocess.Popen(command, cwd=APP_DIR, creationflags=self.create_no_window)
        except Exception:
            pass
        self._on_close()

    def _build_ui(self):
        self.bg_label = tk.Label(self, bg=self.window_bg_color)
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._load_background()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_panel = tk.Frame(
            self,
            bg=self.menu_bg_color,
            highlightbackground=self.menu_border_color,
            highlightthickness=1,
            bd=0,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(24, 12), pady=24)

        self.right_panel = tk.Frame(
            self,
            bg=self.menu_bg_color,
            highlightbackground=self.menu_border_color,
            highlightthickness=1,
            bd=0,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(12, 24), pady=24)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_rowconfigure(1, weight=1)

        title_label = tk.Label(
            self.left_panel,
            text="LenivayaFigna",
            fg=TITLE_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 21, "bold"),
        )
        title_label.pack(anchor="w", padx=16, pady=(14, 8))

        subtitle = tk.Label(
            self.left_panel,
            text="Roblox Winter Event Control",
            fg=MUTED_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", padx=16, pady=(0, 12))

        self.position_button = self._make_button(
            parent=self.left_panel,
            label="Position",
            command=self.run_position,
            bg="#3D567A",
            active="#2A3D57",
        )
        self.position_button.pack(anchor="w", padx=16, pady=6)

        self.start_stop_button = self._make_button(
            parent=self.left_panel,
            label="Start",
            command=self.toggle_winter_event,
            bg="#2C8F63",
            active="#1F6B4A",
        )
        self.start_stop_button.pack(anchor="w", padx=16, pady=6)

        self.check_update_button = self._make_button(
            parent=self.left_panel,
            label="CheckUpdate",
            command=self.run_check_update,
            bg="#B08335",
            active="#7D5D26",
        )
        self.check_update_button.pack(anchor="w", padx=16, pady=6)

        self.instruction_button = self._make_button(
            parent=self.left_panel,
            label="Instruction",
            command=self.open_instruction_window,
            bg="#355A8F",
            active="#264066",
        )
        self.instruction_button.pack(anchor="w", padx=16, pady=(12, 6))

        self.settings_button = self._make_button(
            parent=self.left_panel,
            label="Settings",
            command=self.open_settings_window,
            bg="#5B4E89",
            active="#463A6E",
        )
        self.settings_button.pack(anchor="w", padx=16, pady=6)

        self.credit_button = tk.Button(
            self.left_panel,
            text="Credit",
            width=10,
            font=("Segoe UI", 9, "bold"),
            command=self.open_credit_window,
            bg="#4E5870",
            fg="white",
            activebackground="#3A4254",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=5,
        )
        self.credit_button.pack(anchor="w", padx=16, pady=(2, 10))

        self.status_label = tk.Label(
            self.left_panel,
            text="Ready.",
            fg=MUTED_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 10),
            wraplength=250,
            justify="left",
        )
        self.status_label.pack(anchor="w", padx=16, pady=(8, 16))

        right_title = tk.Label(
            self.right_panel,
            text="Terminal",
            fg=TITLE_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 16, "bold"),
        )
        right_title.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 6))

        terminal_wrap = tk.Frame(
            self.right_panel,
            bg="#0A0E16",
            highlightbackground=self.menu_border_color,
            highlightthickness=1,
            bd=0,
        )
        terminal_wrap.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        terminal_wrap.grid_columnconfigure(0, weight=1)
        terminal_wrap.grid_rowconfigure(0, weight=1)

        self.terminal_text = tk.Text(
            terminal_wrap,
            bg="#0A0E16",
            fg="#D6E1F2",
            insertbackground="#D6E1F2",
            relief="flat",
            bd=0,
            wrap="word",
            font=("Consolas", 10),
            state="disabled",
            padx=8,
            pady=8,
        )
        self.terminal_text.grid(row=0, column=0, sticky="nsew")

        terminal_scroll = tk.Scrollbar(terminal_wrap, command=self.terminal_text.yview)
        terminal_scroll.grid(row=0, column=1, sticky="ns")
        self.terminal_text.config(yscrollcommand=terminal_scroll.set)

        self._append_terminal_line("Terminal ready.")

        self.bind_label = tk.Label(
            self,
            text=self._hotkeys_hint_text(),
            fg="#DCE5F5",
            bg=self.window_bg_color,
            font=("Consolas", 10),
            justify="right",
        )
        self.bind_label.place(relx=1.0, rely=1.0, x=-24, y=-18, anchor="se")

    def _make_button(self, parent, label, command, bg, active):
        return tk.Button(
            parent,
            text=label,
            width=16,
            font=("Segoe UI", 11, "bold"),
            command=command,
            bg=bg,
            fg="white",
            activebackground=active,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=6,
        )

    def _start_with_splash(self):
        self.withdraw()
        if self._show_splash():
            self.after(1200, self._fade_splash_step)
        else:
            self.deiconify()

    def _show_splash(self):
        if not self.splash_path:
            return False

        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.configure(bg="black")
        splash.attributes("-topmost", True)

        image_obj = None
        width, height = 640, 360

        if Image is not None and ImageTk is not None:
            try:
                self.splash_original = Image.open(self.splash_path).convert("RGB")
                max_w = min(900, self.winfo_screenwidth() - 120)
                max_h = min(520, self.winfo_screenheight() - 120)
                image = self.splash_original.copy()
                image.thumbnail((max_w, max_h))
                width, height = image.size
                image_obj = ImageTk.PhotoImage(image)
            except Exception:
                image_obj = None

        if image_obj is None and self.splash_path.lower().endswith(".png"):
            try:
                image_obj = tk.PhotoImage(file=self.splash_path)
                width = image_obj.width()
                height = image_obj.height()
            except Exception:
                image_obj = None

        if image_obj is None:
            splash.destroy()
            return False

        self.splash_photo = image_obj
        label = tk.Label(splash, image=self.splash_photo, bg="black", bd=0, highlightthickness=0)
        label.pack(fill="both", expand=True)

        screen_w = splash.winfo_screenwidth()
        screen_h = splash.winfo_screenheight()
        pos_x = int((screen_w - width) / 2)
        pos_y = int((screen_h - height) / 2)
        splash.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
        splash.attributes("-alpha", 1.0)

        self.splash_window = splash
        return True

    def _fade_splash_step(self):
        if self.splash_window is None:
            self.deiconify()
            return

        try:
            alpha = float(self.splash_window.attributes("-alpha"))
            alpha -= 0.08
            if alpha <= 0:
                self.splash_window.destroy()
                self.splash_window = None
                self.deiconify()
                return
            self.splash_window.attributes("-alpha", alpha)
            self.after(40, self._fade_splash_step)
        except Exception:
            try:
                self.splash_window.destroy()
            except Exception:
                pass
            self.splash_window = None
            self.deiconify()

    def _load_background(self):
        if not self.background_path:
            self.bg_label.config(text="")
            return

        if Image is not None and ImageTk is not None:
            try:
                self.bg_original = Image.open(self.background_path).convert("RGB")
                self.bind("<Configure>", self._resize_background)
                self._resize_background()
                return
            except Exception:
                pass

        if self.background_path.lower().endswith(".png"):
            try:
                self.bg_photo = tk.PhotoImage(file=self.background_path)
                self.bg_label.config(image=self.bg_photo)
                return
            except Exception:
                pass

        self.bg_label.config(text="")

    def _resize_background(self, _event=None):
        if self.bg_original is None or Image is None or ImageTk is None:
            return
        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())
        resampling_owner = getattr(Image, "Resampling", Image)
        resized = self.bg_original.resize((width, height), resampling_owner.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(resized)
        self.bg_label.config(image=self.bg_photo)

    def open_credit_window(self):
        window = tk.Toplevel(self)
        window.title("Credit")
        window.geometry("430x170")
        window.resizable(False, False)
        window.configure(bg=self.menu_bg_color)
        window.transient(self)

        tk.Label(
            window,
            text="UI: LeniZev",
            fg=TITLE_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        tk.Label(
            window,
            text="Original macro creator: MacroLoxer",
            fg=MUTED_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=16, pady=(0, 8))

        link = tk.Label(
            window,
            text=CREDIT_LINK,
            fg="#7FB4FF",
            bg=self.menu_bg_color,
            cursor="hand2",
            font=("Segoe UI", 10, "underline"),
        )
        link.pack(anchor="w", padx=16)
        link.bind("<Button-1>", lambda _event: webbrowser.open(CREDIT_LINK))

    def open_settings_window(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            self._validate_settings_form()
            return

        window = tk.Toplevel(self)
        window.title("Settings")
        window.geometry("520x420")
        window.resizable(False, False)
        window.configure(bg=self.menu_bg_color)
        window.transient(self)
        window.protocol("WM_DELETE_WINDOW", self._close_settings_window)

        self.settings_window = window
        self.settings_entries = {}
        self.hotkey_vars = {
            "position_hotkey": tk.StringVar(value=self.position_hotkey),
            "start_hotkey": tk.StringVar(value=self.start_hotkey),
            "stop_hotkey": tk.StringVar(value=self.stop_hotkey),
        }
        self.color_vars = {
            "menu_bg_color": tk.StringVar(value=self.menu_bg_color),
            "menu_border_color": tk.StringVar(value=self.menu_border_color),
            "window_bg_color": tk.StringVar(value=self.window_bg_color),
        }
        self.custom_background_var = tk.StringVar(value=self.ui_settings.get("background_image", ""))

        tk.Label(
            window,
            text="Settings",
            fg=TITLE_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 10))

        form = tk.Frame(window, bg=self.menu_bg_color)
        form.pack(fill="both", expand=True, padx=14)

        row = 0

        def add_entry(label_text, var, key_name):
            nonlocal row
            tk.Label(
                form,
                text=label_text,
                fg=MUTED_FG,
                bg=self.menu_bg_color,
                font=("Segoe UI", 10),
            ).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
            entry = tk.Entry(form, textvariable=var, width=28, font=("Consolas", 10))
            entry.grid(row=row, column=1, sticky="ew", pady=6)
            self.settings_entries[key_name] = entry
            row += 1

        add_entry("Position hotkey (F1-F12)", self.hotkey_vars["position_hotkey"], "position_hotkey")
        add_entry("Start hotkey (F1-F12)", self.hotkey_vars["start_hotkey"], "start_hotkey")
        add_entry("Stop hotkey (F1-F12)", self.hotkey_vars["stop_hotkey"], "stop_hotkey")
        add_entry("Menu color (#RRGGBB)", self.color_vars["menu_bg_color"], "menu_bg_color")
        add_entry("Menu border color (#RRGGBB)", self.color_vars["menu_border_color"], "menu_border_color")
        add_entry("Window bg color (#RRGGBB)", self.color_vars["window_bg_color"], "window_bg_color")
        add_entry("Custom background path (optional)", self.custom_background_var, "background_image")

        form.grid_columnconfigure(1, weight=1)

        for var in list(self.hotkey_vars.values()) + list(self.color_vars.values()) + [self.custom_background_var]:
            var.trace_add("write", lambda *_args: self._validate_settings_form())

        self.settings_error_label = tk.Label(
            window,
            text="",
            fg="#F6C0C0",
            bg=self.menu_bg_color,
            justify="left",
            font=("Segoe UI", 9),
        )
        self.settings_error_label.pack(fill="x", padx=14, pady=(6, 6))

        footer = tk.Frame(window, bg=self.menu_bg_color)
        footer.pack(fill="x", padx=14, pady=(0, 12))

        self.settings_save_button = tk.Button(
            footer,
            text="Save",
            width=12,
            font=("Segoe UI", 10, "bold"),
            command=self._save_settings,
            bg="#2C8F63",
            fg="white",
            activebackground="#1F6B4A",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=6,
        )
        self.settings_save_button.pack(side="right")

        self._validate_settings_form()

    def _close_settings_window(self):
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.destroy()
        self.settings_window = None
        self.settings_save_button = None
        self.settings_error_label = None
        self.settings_entries = {}
        self.hotkey_vars = {}
        self.color_vars = {}
        self.custom_background_var = None

    def _set_entry_error(self, entry, has_error):
        if entry is None:
            return
        if has_error:
            entry.config(bg="#FFD7D7")
        else:
            entry.config(bg="white")

    def _validate_settings_form(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            return False

        errors = []

        hotkeys = {}
        counts = {}
        for key, var in self.hotkey_vars.items():
            value = self._normalize_hotkey(var.get())
            hotkeys[key] = value
            counts[value] = counts.get(value, 0) + 1

        for key, value in hotkeys.items():
            invalid = value not in ALLOWED_HOTKEYS
            duplicate = counts.get(value, 0) > 1
            self._set_entry_error(self.settings_entries.get(key), invalid or duplicate)
            if invalid:
                errors.append(f"{key} must be one of: {', '.join(ALLOWED_HOTKEYS)}")
            if duplicate:
                errors.append("Hotkeys must be unique.")

        for key, var in self.color_vars.items():
            color_value = var.get().strip()
            invalid_color = not self._is_valid_hex_color(color_value)
            self._set_entry_error(self.settings_entries.get(key), invalid_color)
            if invalid_color:
                errors.append(f"{key} must be #RRGGBB.")

        bg_value = self.custom_background_var.get().strip() if self.custom_background_var else ""
        background_invalid = False
        if bg_value:
            candidate = bg_value if os.path.isabs(bg_value) else os.path.join(APP_DIR, bg_value)
            background_invalid = not os.path.exists(candidate)
        self._set_entry_error(self.settings_entries.get("background_image"), background_invalid)
        if background_invalid:
            errors.append("Custom background path does not exist.")

        if errors:
            if self.settings_error_label is not None:
                self.settings_error_label.config(text=errors[0], fg="#F6C0C0")
            if self.settings_save_button is not None:
                self.settings_save_button.config(state="disabled")
            return False

        if self.settings_error_label is not None:
            self.settings_error_label.config(text="Ready to save.", fg="#BFEBCF")
        if self.settings_save_button is not None:
            self.settings_save_button.config(state="normal")
        return True

    def _save_settings(self):
        if not self._validate_settings_form():
            return

        background_value = self.custom_background_var.get().strip() if self.custom_background_var else ""
        settings_to_save = {
            "position_hotkey": self._normalize_hotkey(self.hotkey_vars["position_hotkey"].get()),
            "start_hotkey": self._normalize_hotkey(self.hotkey_vars["start_hotkey"].get()),
            "stop_hotkey": self._normalize_hotkey(self.hotkey_vars["stop_hotkey"].get()),
            "menu_bg_color": self.color_vars["menu_bg_color"].get().strip(),
            "menu_border_color": self.color_vars["menu_border_color"].get().strip(),
            "window_bg_color": self.color_vars["window_bg_color"].get().strip(),
            "background_image": background_value,
        }

        try:
            os.makedirs(os.path.dirname(UI_SETTINGS_PATH), exist_ok=True)
            with open(UI_SETTINGS_PATH, "w", encoding="utf-8") as settings_file:
                json.dump(settings_to_save, settings_file, ensure_ascii=False, indent=2)
            self._append_terminal_line("Settings saved. Restarting application...")
            self._set_status("Settings saved. Restarting...")
            self.after(250, self._restart_application)
        except Exception as error:
            self._append_terminal_line(f"Settings save error: {error}")
            self._set_status(f"Settings save error: {error}")

    def open_instruction_window(self):
        if self.instruction_window is not None and self.instruction_window.winfo_exists():
            self.instruction_window.deiconify()
            self.instruction_window.lift()
            self._update_instruction_content()
            return

        window = tk.Toplevel(self)
        window.title("Instruction")
        window.geometry("980x760")
        window.minsize(860, 620)
        window.configure(bg=self.menu_bg_color)
        window.transient(self)
        window.protocol("WM_DELETE_WINDOW", self._close_instruction_window)

        top_frame = tk.Frame(window, bg=self.menu_bg_color)
        top_frame.pack(fill="x", padx=14, pady=(14, 8))

        self.instruction_title_label = tk.Label(
            top_frame,
            text="Instruction",
            fg=TITLE_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 16, "bold"),
        )
        self.instruction_title_label.pack(side="left")

        self.lang_button = tk.Button(
            top_frame,
            text="\u0420\u0443\u0441\u0441\u043a\u0438\u0439",
            width=10,
            command=self._toggle_instruction_language,
            bg="#355A8F",
            fg="white",
            activebackground="#264066",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=5,
            font=("Segoe UI", 9, "bold"),
        )
        self.lang_button.pack(side="right")

        self.instruction_text_label = tk.Label(
            window,
            text="",
            fg=MUTED_FG,
            bg=self.menu_bg_color,
            justify="left",
            anchor="w",
            font=("Segoe UI", 11),
            wraplength=920,
        )
        self.instruction_text_label.pack(fill="x", padx=16, pady=(0, 12))

        image_frame = tk.Frame(
            window,
            bg="#0D1320",
            highlightbackground=self.menu_border_color,
            highlightthickness=1,
            bd=0,
        )
        image_frame.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.instruction_image_label = tk.Label(
            image_frame,
            bg="#0D1320",
            fg=MUTED_FG,
            text="No instruction images found.\nAdd Resources/image1..image4",
            font=("Segoe UI", 11),
            justify="center",
        )
        self.instruction_image_label.pack(fill="both", expand=True, padx=6, pady=6)

        nav_frame = tk.Frame(window, bg=self.menu_bg_color)
        nav_frame.pack(fill="x", padx=16, pady=(0, 14))

        self.prev_image_button = tk.Button(
            nav_frame,
            text="Prev",
            width=10,
            command=self._instruction_prev_image,
            bg="#4E5870",
            fg="white",
            activebackground="#3A4254",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=5,
            font=("Segoe UI", 9, "bold"),
        )
        self.prev_image_button.pack(side="left")

        self.image_counter_label = tk.Label(
            nav_frame,
            text="0 / 0",
            fg=MUTED_FG,
            bg=self.menu_bg_color,
            font=("Segoe UI", 10, "bold"),
        )
        self.image_counter_label.pack(side="left", padx=14)

        self.next_image_button = tk.Button(
            nav_frame,
            text="Next",
            width=10,
            command=self._instruction_next_image,
            bg="#4E5870",
            fg="white",
            activebackground="#3A4254",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            bd=0,
            padx=6,
            pady=5,
            font=("Segoe UI", 9, "bold"),
        )
        self.next_image_button.pack(side="left")

        self.instruction_window = window
        self._update_instruction_content()
        self.instruction_window.bind("<Configure>", self._on_instruction_resize)

    def _close_instruction_window(self):
        if self.instruction_window is not None and self.instruction_window.winfo_exists():
            self.instruction_window.destroy()
        self.instruction_window = None

    def _toggle_instruction_language(self):
        self.instruction_lang = "RU" if self.instruction_lang == "EN" else "EN"
        self._update_instruction_content()

    def _instruction_prev_image(self):
        if not self.instruction_images:
            return
        self.instruction_index = (self.instruction_index - 1) % len(self.instruction_images)
        self._update_instruction_image()

    def _instruction_next_image(self):
        if not self.instruction_images:
            return
        self.instruction_index = (self.instruction_index + 1) % len(self.instruction_images)
        self._update_instruction_image()

    def _on_instruction_resize(self, _event):
        self._update_instruction_image()

    def _update_instruction_content(self):
        if self.instruction_window is None or not self.instruction_window.winfo_exists():
            return

        if self.instruction_lang == "EN":
            self.instruction_title_label.config(text="Instruction")
            self.lang_button.config(text="\u0420\u0443\u0441\u0441\u043a\u0438\u0439")
        else:
            self.instruction_title_label.config(text="\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f")
            self.lang_button.config(text="English")

        self.instruction_text_label.config(text=INSTRUCTION_TEXT[self.instruction_lang])
        self._update_instruction_image()
    def _update_instruction_image(self):
        if self.instruction_window is None or not self.instruction_window.winfo_exists():
            return

        count = len(self.instruction_images)
        if count == 0:
            self.instruction_image_label.config(
                image="",
                text="No instruction images found.\nAdd Resources/image1..image4",
            )
            self.image_counter_label.config(text="0 / 0")
            self.prev_image_button.config(state="disabled")
            self.next_image_button.config(state="disabled")
            return

        self.prev_image_button.config(state="normal")
        self.next_image_button.config(state="normal")
        self.instruction_index = self.instruction_index % count
        img_path = self.instruction_images[self.instruction_index]

        frame_w = max(300, self.instruction_image_label.winfo_width() - 10)
        frame_h = max(220, self.instruction_image_label.winfo_height() - 10)

        image_obj = None
        if Image is not None and ImageTk is not None:
            try:
                original = self.instruction_pil_cache.get(img_path)
                if original is None:
                    original = Image.open(img_path).convert("RGB")
                    self.instruction_pil_cache[img_path] = original
                img = original.copy()
                img.thumbnail((frame_w, frame_h))
                image_obj = ImageTk.PhotoImage(img)
            except Exception:
                image_obj = None

        if image_obj is None and img_path.lower().endswith(".png"):
            try:
                image_obj = tk.PhotoImage(file=img_path)
                scale = max(image_obj.width() // frame_w, image_obj.height() // frame_h, 1)
                if scale > 1:
                    image_obj = image_obj.subsample(scale, scale)
            except Exception:
                image_obj = None

        if image_obj is None:
            self.instruction_image_label.config(
                image="",
                text=f"Failed to load image:\n{os.path.basename(img_path)}",
            )
        else:
            self.instruction_photo = image_obj
            self.instruction_image_label.config(image=self.instruction_photo, text="")

        self.image_counter_label.config(text=f"{self.instruction_index + 1} / {count}")

    def _set_status(self, text):
        if hasattr(self, "status_label"):
            self.status_label.config(text=text)

    def _append_terminal_line(self, text):
        if not hasattr(self, "terminal_text"):
            return
        self.terminal_text.config(state="normal")
        self.terminal_text.insert("end", f"{text}\n")
        self.terminal_text.see("end")
        self.terminal_text.config(state="disabled")

    def _append_terminal_line_from_thread(self, text):
        self.after(0, lambda: self._append_terminal_line(text))

    def _capture_winter_output(self):
        if self.winter_proc is None or self.winter_proc.stdout is None:
            return
        try:
            for line in iter(self.winter_proc.stdout.readline, ""):
                if not line:
                    break
                clean = line.rstrip()
                if clean:
                    self._append_terminal_line_from_thread(clean)
        except Exception as error:
            self._append_terminal_line_from_thread(f"[output error] {error}")

    def _register_hotkeys(self):
        self.bind(f"<{self.position_hotkey}>", lambda _event: self.run_position())
        self.bind(f"<{self.start_hotkey}>", lambda _event: self.start_winter_event())
        self.bind(f"<{self.stop_hotkey}>", lambda _event: self.stop_winter_event())

        try:
            import keyboard

            for hotkey in self.global_hotkeys:
                try:
                    keyboard.remove_hotkey(hotkey)
                except Exception:
                    pass
            self.global_hotkeys = []

            self.global_hotkeys.append(
                keyboard.add_hotkey(self.position_hotkey.lower(), lambda: self.after(0, self.run_position))
            )
            self.global_hotkeys.append(
                keyboard.add_hotkey(self.start_hotkey.lower(), lambda: self.after(0, self.start_winter_event))
            )
            self.global_hotkeys.append(
                keyboard.add_hotkey(self.stop_hotkey.lower(), lambda: self.after(0, self.stop_winter_event))
            )
        except Exception:
            self._set_status("Global hotkeys are unavailable. Window hotkeys still work.")

    def _build_launch_command(self, script_path, capture_output=False):
        # In frozen builds, always re-launch the same EXE in worker mode.
        # This keeps PyInstaller paths consistent (_internal, bundled modules).
        if IS_FROZEN:
            return [sys.executable, os.path.basename(script_path)]
        if capture_output and _is_python_executable(self.python_exe):
            return [self.python_exe, "-u", script_path]
        if _is_python_executable(self.pythonw_exe):
            return [self.pythonw_exe, script_path]
        if _is_python_executable(self.python_exe):
            return [self.python_exe, script_path]
        return [sys.executable, script_path]

    def _build_worker_env(self, script_path, capture_output=False):
        env = os.environ.copy()
        if capture_output:
            env["PYTHONUNBUFFERED"] = "1"

        candidate_paths = [
            APP_DIR,
            DATA_DIR,
            os.path.dirname(DATA_DIR),
            os.path.dirname(script_path),
        ]
        clean_paths = []
        seen = set()
        for path in candidate_paths:
            if not path:
                continue
            normalized = os.path.normcase(os.path.normpath(path))
            if normalized in seen:
                continue
            if os.path.isdir(path):
                clean_paths.append(path)
                seen.add(normalized)

        existing_pythonpath = env.get("PYTHONPATH", "").strip()
        if existing_pythonpath:
            clean_paths.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(clean_paths)
        return env

    def run_position(self):
        script_path = _resolve_worker_script(POSITION_SCRIPT_NAME)
        if not os.path.exists(script_path):
            self._set_status("Position.py not found.")
            self._append_terminal_line("Position.py not found.")
            return
        try:
            subprocess.Popen(
                self._build_launch_command(script_path),
                cwd=APP_DIR,
                env=self._build_worker_env(script_path, capture_output=False),
                creationflags=self.create_no_window,
            )
            self._append_terminal_line("Waiting for position. Press Start when ready.")
            self._set_status("Position.py started.")
        except Exception as error:
            self._append_terminal_line(f"Position.py launch error: {error}")
            self._set_status(f"Position.py launch error: {error}")

    def toggle_winter_event(self):
        if self._winter_is_running():
            self.stop_winter_event()
        else:
            self.start_winter_event()

    def start_winter_event(self):
        if self._winter_is_running():
            self._set_status("Winter_Event.py is already running.")
            self._append_terminal_line("Macro is already running.")
            return
        script_path = _resolve_worker_script(WINTER_SCRIPT_NAME)
        if not os.path.exists(script_path):
            self._set_status("Winter_Event.py not found.")
            self._append_terminal_line("Winter_Event.py not found.")
            return
        try:
            env = self._build_worker_env(script_path, capture_output=True)
            self.winter_proc = subprocess.Popen(
                self._build_launch_command(script_path, capture_output=True),
                cwd=APP_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                creationflags=self.create_no_window,
            )
            self.suppress_winter_exit_log = False
            self.winter_log_thread = threading.Thread(target=self._capture_winter_output, daemon=True)
            self.winter_log_thread.start()
            self.start_stop_button.config(text="Stop", bg="#A53D3D", activebackground="#732A2A")
            self._append_terminal_line("Macro started.")
            self._set_status("Winter_Event.py started.")
        except Exception as error:
            self._append_terminal_line(f"Winter_Event.py launch error: {error}")
            self._set_status(f"Winter_Event.py launch error: {error}")

    def stop_winter_event(self):
        if self.winter_proc is None:
            self._set_start_state()
            self._set_status("Winter_Event.py is not running.")
            self._append_terminal_line("Macro is not running.")
            return

        pid = self.winter_proc.pid
        self.suppress_winter_exit_log = True
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                creationflags=self.create_no_window,
            )
        except Exception:
            try:
                self.winter_proc.terminate()
            except Exception:
                pass

        self.winter_proc = None
        self._set_start_state()
        self._append_terminal_line("Macro stopped.")
        self._set_status("Winter_Event.py stopped.")

    def _set_start_state(self):
        self.start_stop_button.config(text="Start", bg="#2C8F63", activebackground="#1F6B4A")

    def _winter_is_running(self):
        return self.winter_proc is not None and self.winter_proc.poll() is None

    def _poll_process_state(self):
        if self.winter_proc is not None and self.winter_proc.poll() is not None:
            code = self.winter_proc.returncode
            self.winter_proc = None
            self._set_start_state()
            if not self.suppress_winter_exit_log:
                self._append_terminal_line(f"Macro process exited (code {code}).")
            self.suppress_winter_exit_log = False
            self._set_status("Winter_Event.py finished.")
        self.after(1000, self._poll_process_state)

    def run_check_update(self):
        if self.update_thread is not None and self.update_thread.is_alive():
            self._set_status("Update is already running.")
            self._append_terminal_line("Update is already running.")
            return
        self.check_update_button.config(state="disabled")
        self._append_terminal_line("CheckUpdate started...")
        self._append_terminal_line(f"Source: {FileCheck.winter_event_url}")
        self._set_status("Checking and updating files...")
        self.update_thread = threading.Thread(target=self._run_update_worker, daemon=True)
        self.update_thread.start()

    def _run_update_worker(self):
        try:
            version_info = FileCheck.get_version_info()
            current_ver = version_info.get("current_version") or "unknown"
            latest_ver = version_info.get("latest_version") or "unknown"

            result = FileCheck.run_update_flow(
                auto_confirm=True,
                preserve_local_winter=False,
                print_fn=lambda *_args, **_kwargs: None,
            )

            if result["error"]:
                message = (
                    f"Current version: {current_ver}; "
                    f"Latest version: {latest_ver}; "
                    f"Update error: {result['error']}"
                )
            else:
                messages = []
                messages.append(f"Current version: {current_ver}")
                messages.append(f"Latest version: {latest_ver}")
                if version_info.get("error"):
                    messages.append(f"Version check warning: {version_info['error']}")
                if result.get("updated_resources"):
                    messages.append("Resources updated")
                if result.get("updated_winter"):
                    messages.append("Winter_Event.py updated")
                if result.get("skipped_winter"):
                    messages.append("Winter_Event.py kept (local)")
                if not result.get("updated_winter") and current_ver == latest_ver and current_ver != "unknown":
                    messages.append("Winter_Event.py is already up to date")
                post_ver = result.get("post_update_version")
                if post_ver:
                    messages.append(f"Installed version: {post_ver}")
                if not messages:
                    messages.append("No updates needed")
                message = "; ".join(messages)
        except Exception as error:
            message = f"CheckUpdate error: {error}"

        self.after(0, lambda: self._finish_update(message))

    def _finish_update(self, message):
        self.check_update_button.config(state="normal")
        self._append_terminal_line(message)
        self._set_status(message)

    def _on_close(self):
        try:
            import keyboard

            for hotkey in self.global_hotkeys:
                keyboard.remove_hotkey(hotkey)
        except Exception:
            pass
        self.destroy()


if __name__ == "__main__":
    _maybe_run_worker_script()
    app = LenivayaFignaApp()
    app.mainloop()

