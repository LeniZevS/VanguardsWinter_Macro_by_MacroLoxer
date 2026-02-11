import glob
import os
import runpy
import subprocess
import sys
import threading
import tkinter as tk

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

BACKGROUND_CANDIDATES = [
    os.path.join(DATA_DIR, "Resources", "ui_background.png"),
    os.path.join(DATA_DIR, "Resources", "ui_background.jpg"),
    os.path.join(DATA_DIR, "Resources", "ui_background.jpeg"),
    os.path.join(DATA_DIR, "Resources", "background.png"),
    os.path.join(DATA_DIR, "Resources", "background.jpg"),
    os.path.join(DATA_DIR, "Resources", "background.jpeg"),
    os.path.join(APP_DIR, "Resources", "ui_background.png"),
    os.path.join(APP_DIR, "Resources", "ui_background.jpg"),
    os.path.join(APP_DIR, "Resources", "ui_background.jpeg"),
    os.path.join(APP_DIR, "Resources", "background.png"),
    os.path.join(APP_DIR, "Resources", "background.jpg"),
    os.path.join(APP_DIR, "Resources", "background.jpeg"),
]

GUIDE_CANDIDATES = [
    os.path.join(DATA_DIR, "Resources", "image1.png"),
    os.path.join(DATA_DIR, "Resources", "image1.jpg"),
    os.path.join(DATA_DIR, "Resources", "image1.jpeg"),
    os.path.join(APP_DIR, "Resources", "image1.png"),
    os.path.join(APP_DIR, "Resources", "image1.jpg"),
    os.path.join(APP_DIR, "Resources", "image1.jpeg"),
]

SPLASH_CANDIDATES = [
    os.path.join(DATA_DIR, "Resources", "start.png"),
    os.path.join(DATA_DIR, "Resources", "start.jpg"),
    os.path.join(DATA_DIR, "Resources", "start.jpeg"),
    os.path.join(APP_DIR, "Resources", "start.png"),
    os.path.join(APP_DIR, "Resources", "start.jpg"),
    os.path.join(APP_DIR, "Resources", "start.jpeg"),
]

CARD_BG = "#090C12"
CARD_BORDER = "#9AA8BC"
TITLE_FG = "#EFF5FF"
MUTED_FG = "#C8D2E2"


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
    version_dirs = sorted(glob.glob(os.path.join(APP_DIR, "Python", "python*")), reverse=True)
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

    script_path = os.path.join(APP_DIR, worker_name)
    if not os.path.exists(script_path):
        return

    sys.argv = [script_path, *sys.argv[2:]]
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    runpy.run_path(script_path, run_name="__main__")
    sys.exit(0)


class LenivayaFignaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LenivayaFigna")
        self.geometry("1120x720")
        self.minsize(980, 620)
        self.configure(bg="#030405")

        self.python_exe = _resolve_python(windowless=False)
        self.pythonw_exe = _resolve_python(windowless=True)
        self.create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        self.winter_proc = None
        self.update_thread = None
        self.global_hotkeys = []

        self.background_path = _first_existing(BACKGROUND_CANDIDATES)
        self.guide_path = _first_existing(GUIDE_CANDIDATES)
        self.splash_path = _first_existing(SPLASH_CANDIDATES)

        self.bg_original = None
        self.bg_photo = None
        self.guide_original = None
        self.guide_photo = None
        self.splash_original = None
        self.splash_photo = None
        self.splash_window = None

        self._build_ui()
        self._register_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(1000, self._poll_process_state)
        self.after(30, self._start_with_splash)

    def _build_ui(self):
        self.bg_label = tk.Label(self, bg="#030405")
        self.bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._load_background()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.left_panel = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            bd=0,
        )
        self.left_panel.grid(row=0, column=0, sticky="nsw", padx=(26, 14), pady=26)

        self.right_panel = tk.Frame(
            self,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            bd=0,
        )
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(14, 26), pady=26)
        self.right_panel.grid_rowconfigure(1, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.bind("<Configure>", self._on_right_panel_resize)

        title_label = tk.Label(
            self.left_panel,
            text="LenivayaFigna",
            fg=TITLE_FG,
            bg=CARD_BG,
            font=("Segoe UI", 20, "bold"),
        )
        title_label.pack(anchor="w", padx=16, pady=(14, 8))

        subtitle = tk.Label(
            self.left_panel,
            text="Roblox Winter Event Control",
            fg=MUTED_FG,
            bg=CARD_BG,
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

        self.status_label = tk.Label(
            self.left_panel,
            text="Ready.",
            fg=MUTED_FG,
            bg=CARD_BG,
            font=("Segoe UI", 10),
            wraplength=240,
            justify="left",
        )
        self.status_label.pack(anchor="w", padx=16, pady=(14, 8))

        hint_text = "Background: Resources/ui_background.png\nSplash: Resources/start.png"
        bg_hint = tk.Label(
            self.left_panel,
            text=hint_text,
            fg="#98A7BC",
            bg=CARD_BG,
            font=("Consolas", 9),
            justify="left",
        )
        bg_hint.pack(anchor="w", padx=16, pady=(0, 14))

        instruction_label = tk.Label(
            self.right_panel,
            text="Встаньте как на картинке",
            fg=TITLE_FG,
            bg=CARD_BG,
            font=("Segoe UI", 16, "bold"),
        )
        instruction_label.grid(row=0, column=0, sticky="n", pady=(14, 10))

        self.image_wrap = tk.Frame(self.right_panel, bg=CARD_BG)
        self.image_wrap.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))

        self.guide_label = tk.Label(
            self.image_wrap,
            bg=CARD_BG,
            fg=MUTED_FG,
            text="Guide image not found.\nSave your screenshot as Resources/image1.png",
            font=("Segoe UI", 11),
            justify="center",
        )
        self.guide_label.pack(fill="both", expand=True)
        self._load_guide_image()

        bind_label = tk.Label(
            self,
            text="F1 - Position\nF2 - Start\nF3 - Stop",
            fg="#DCE5F5",
            bg="#030405",
            font=("Consolas", 10),
            justify="right",
        )
        bind_label.place(relx=1.0, rely=1.0, x=-24, y=-20, anchor="se")

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
            except Exception as error:
                self._set_status(f"Background load error: {error}")

        if self.background_path.lower().endswith(".png"):
            try:
                self.bg_photo = tk.PhotoImage(file=self.background_path)
                self.bg_label.config(image=self.bg_photo)
                return
            except Exception as error:
                self._set_status(f"Background load error: {error}")

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

    def _load_guide_image(self, target_w=760, target_h=480):
        if not self.guide_path:
            self.guide_label.config(
                image="",
                text="Guide image not found.\nSave your screenshot as Resources/image1.png",
            )
            return

        if Image is not None and ImageTk is not None:
            try:
                if self.guide_original is None:
                    self.guide_original = Image.open(self.guide_path).convert("RGB")
                img = self.guide_original.copy()
                img.thumbnail((max(64, target_w), max(64, target_h)))
                self.guide_photo = ImageTk.PhotoImage(img)
                self.guide_label.config(image=self.guide_photo, text="")
                return
            except Exception as error:
                self._set_status(f"Guide image error: {error}")

        if self.guide_path.lower().endswith(".png"):
            try:
                self.guide_photo = tk.PhotoImage(file=self.guide_path)
                self.guide_label.config(image=self.guide_photo, text="")
                return
            except Exception as error:
                self._set_status(f"Guide image error: {error}")

        self.guide_label.config(
            image="",
            text="Image format is not supported without Pillow.\nUse PNG or install Pillow.",
        )

    def _on_right_panel_resize(self, event):
        target_w = event.width - 40
        target_h = event.height - 100
        self._load_guide_image(target_w=target_w, target_h=target_h)

    def _set_status(self, text):
        if hasattr(self, "status_label"):
            self.status_label.config(text=text)

    def _register_hotkeys(self):
        self.bind("<F1>", lambda _event: self.run_position())
        self.bind("<F2>", lambda _event: self.start_winter_event())
        self.bind("<F3>", lambda _event: self.stop_winter_event())

        try:
            import keyboard

            self.global_hotkeys.append(
                keyboard.add_hotkey("f1", lambda: self.after(0, self.run_position))
            )
            self.global_hotkeys.append(
                keyboard.add_hotkey("f2", lambda: self.after(0, self.start_winter_event))
            )
            self.global_hotkeys.append(
                keyboard.add_hotkey("f3", lambda: self.after(0, self.stop_winter_event))
            )
        except Exception:
            self._set_status("Global F1/F2/F3 are unavailable. Window hotkeys still work.")

    def _build_launch_command(self, script_path):
        if _is_python_executable(self.pythonw_exe):
            return [self.pythonw_exe, script_path]
        if _is_python_executable(self.python_exe):
            return [self.python_exe, script_path]
        if IS_FROZEN:
            return [sys.executable, os.path.basename(script_path)]
        return [sys.executable, script_path]

    def run_position(self):
        if not os.path.exists(POSITION_SCRIPT):
            self._set_status("Position.py not found.")
            return
        try:
            subprocess.Popen(
                self._build_launch_command(POSITION_SCRIPT),
                cwd=APP_DIR,
                creationflags=self.create_no_window,
            )
            self._set_status("Position.py started.")
        except Exception as error:
            self._set_status(f"Position.py launch error: {error}")

    def toggle_winter_event(self):
        if self._winter_is_running():
            self.stop_winter_event()
        else:
            self.start_winter_event()

    def start_winter_event(self):
        if self._winter_is_running():
            self._set_status("Winter_Event.py is already running.")
            return
        if not os.path.exists(WINTER_SCRIPT):
            self._set_status("Winter_Event.py not found.")
            return
        try:
            self.winter_proc = subprocess.Popen(
                self._build_launch_command(WINTER_SCRIPT),
                cwd=APP_DIR,
                creationflags=self.create_no_window,
            )
            self.start_stop_button.config(text="Stop", bg="#A53D3D", activebackground="#732A2A")
            self._set_status("Winter_Event.py started.")
        except Exception as error:
            self._set_status(f"Winter_Event.py launch error: {error}")

    def stop_winter_event(self):
        if self.winter_proc is None:
            self._set_start_state()
            self._set_status("Winter_Event.py is not running.")
            return

        pid = self.winter_proc.pid
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
        self._set_status("Winter_Event.py stopped.")

    def _set_start_state(self):
        self.start_stop_button.config(text="Start", bg="#2C8F63", activebackground="#1F6B4A")

    def _winter_is_running(self):
        return self.winter_proc is not None and self.winter_proc.poll() is None

    def _poll_process_state(self):
        if self.winter_proc is not None and self.winter_proc.poll() is not None:
            self.winter_proc = None
            self._set_start_state()
            self._set_status("Winter_Event.py finished.")
        self.after(1000, self._poll_process_state)

    def run_check_update(self):
        if self.update_thread is not None and self.update_thread.is_alive():
            self._set_status("Update is already running.")
            return
        self.check_update_button.config(state="disabled")
        self._set_status("Checking and updating files...")
        self.update_thread = threading.Thread(target=self._run_update_worker, daemon=True)
        self.update_thread.start()

    def _run_update_worker(self):
        try:
            result = FileCheck.run_update_flow(auto_confirm=True, print_fn=lambda *_args, **_kwargs: None)
            if result["error"]:
                message = f"Update error: {result['error']}"
            else:
                updated_items = []
                if result["updated_winter"]:
                    updated_items.append("Winter_Event.py")
                if result["updated_resources"]:
                    updated_items.append("Resources")
                if updated_items:
                    message = f"Updated: {', '.join(updated_items)}"
                else:
                    message = "No updates needed."
        except Exception as error:
            message = f"CheckUpdate error: {error}"

        self.after(0, lambda: self._finish_update(message))

    def _finish_update(self, message):
        self.check_update_button.config(state="normal")
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
