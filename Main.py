import os
import runpy
import shutil
import sys
import tempfile
import urllib.request
import zipfile
import ctypes

# PyInstaller note:
# These scripts are executed via runpy from bundled files (data),
# so we keep explicit optional imports here to help dependency discovery.
try:
    import glob  # noqa: F401
    import subprocess  # noqa: F401
    import threading  # noqa: F401
    import tkinter  # noqa: F401
except Exception:
    pass

try:
    import requests  # noqa: F401
except Exception:
    pass


IS_FROZEN = getattr(sys, "frozen", False)
APP_DIR = os.path.dirname(sys.executable) if IS_FROZEN else os.path.dirname(os.path.abspath(__file__))
DATA_DIR = getattr(sys, "_MEIPASS", APP_DIR)

REPO_URL_FILE = os.path.join(APP_DIR, "bootstrap_repo_url.txt")
FROZEN_REPO_URL_FILE = os.path.join(DATA_DIR, "bootstrap_repo_url.txt")
DEFAULT_REPO_ZIP_URL = "https://github.com/YOUR_USERNAME/YOUR_REPO/archive/refs/heads/main.zip"

REQUIRED_PATHS = [
    "LenivayaFigna.py",
    "Position.py",
    "Winter_Event.py",
    "webhook.py",
    os.path.join("Utility", "FileCheck.py"),
    os.path.join("Tools", "winTools.py"),
    os.path.join("Settings", "Winter_Event.json"),
    "Resources",
    "tesseract",
]

WORKER_TARGETS = {
    "position.py": "Position.py",
    "winter_event.py": "Winter_Event.py",
}


def _read_repo_url():
    env_url = os.environ.get("LENIVAYA_REPO_ZIP_URL", "").strip()
    if env_url:
        return env_url

    if os.path.exists(REPO_URL_FILE):
        with open(REPO_URL_FILE, "r", encoding="utf-8") as cfg_file:
            url = cfg_file.read().strip()
            if url:
                return url

    if os.path.exists(FROZEN_REPO_URL_FILE):
        with open(FROZEN_REPO_URL_FILE, "r", encoding="utf-8") as cfg_file:
            url = cfg_file.read().strip()
            if url:
                return url
    return DEFAULT_REPO_ZIP_URL


def _is_placeholder_url(url):
    text = url.lower()
    return "your_username" in text or "your_repo" in text


def _has_required_files(base_dir):
    for rel_path in REQUIRED_PATHS:
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            return False
    return True


def _safe_extract(zip_path, target_dir):
    with zipfile.ZipFile(zip_path, "r") as archive:
        names = archive.namelist()
        if not names:
            raise RuntimeError("Downloaded archive is empty.")

        root_prefix = ""
        if "/" in names[0]:
            first_root = names[0].split("/", 1)[0]
            if all(name.startswith(first_root + "/") or name == first_root + "/" for name in names):
                root_prefix = first_root + "/"

        for info in archive.infolist():
            member_name = info.filename.replace("\\", "/")
            if root_prefix and member_name.startswith(root_prefix):
                member_name = member_name[len(root_prefix):]
            member_name = member_name.strip("/")
            if not member_name:
                continue

            destination = os.path.normpath(os.path.join(target_dir, member_name))
            if os.path.commonpath([destination, target_dir]) != target_dir:
                continue

            if info.is_dir():
                os.makedirs(destination, exist_ok=True)
                continue

            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with archive.open(info, "r") as source, open(destination, "wb") as dest:
                shutil.copyfileobj(source, dest)


def _download_repo_snapshot(repo_zip_url):
    with tempfile.TemporaryDirectory(prefix="lenivaya_bootstrap_") as temp_dir:
        zip_path = os.path.join(temp_dir, "repo.zip")

        request = urllib.request.Request(
            repo_zip_url,
            headers={"User-Agent": "LenivayaFigna-Bootstrap/1.0"},
        )
        with urllib.request.urlopen(request, timeout=90) as response, open(zip_path, "wb") as zip_file:
            shutil.copyfileobj(response, zip_file)

        _safe_extract(zip_path, APP_DIR)


def _ensure_project_files(force_update=False):
    if not force_update and (_has_required_files(APP_DIR) or _has_required_files(DATA_DIR)):
        return

    repo_zip_url = _read_repo_url()
    if _is_placeholder_url(repo_zip_url):
        message = (
            "Bootstrap URL is not configured.\n"
            f"Set your repo zip URL in: {REPO_URL_FILE}\n"
            "or set env var LENIVAYA_REPO_ZIP_URL"
        )
        raise RuntimeError(message)

    _download_repo_snapshot(repo_zip_url)

    if not _has_required_files(APP_DIR):
        raise RuntimeError("Files are still missing after download. Check repository content.")


def _run_worker_if_requested():
    if len(sys.argv) < 2:
        return

    requested = os.path.basename(sys.argv[1]).lower()
    target_name = WORKER_TARGETS.get(requested)
    if not target_name:
        return

    script_path = os.path.join(APP_DIR, target_name)
    if not os.path.exists(script_path):
        script_path = os.path.join(DATA_DIR, target_name)
    if not os.path.exists(script_path):
        raise RuntimeError(f"Worker script not found: {target_name}")

    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    sys.argv = [script_path, *sys.argv[2:]]
    runpy.run_path(script_path, run_name="__main__")
    sys.exit(0)


def _run_gui():
    gui_path = os.path.join(APP_DIR, "LenivayaFigna.py")
    if not os.path.exists(gui_path):
        gui_path = os.path.join(DATA_DIR, "LenivayaFigna.py")
    if not os.path.exists(gui_path):
        raise RuntimeError("LenivayaFigna.py not found.")

    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)
    sys.argv = [gui_path]
    runpy.run_path(gui_path, run_name="__main__")


def main():
    force_update = "--update" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg != "--update"]
    sys.argv = [sys.argv[0], *args]

    _ensure_project_files(force_update=force_update)
    _run_worker_if_requested()
    _run_gui()


def _show_error_message(text):
    try:
        ctypes.windll.user32.MessageBoxW(None, str(text), "LenivayaFigna - Error", 0x10)
    except Exception:
        print(text)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        _show_error_message(f"Startup error:\n{error}")
        raise
