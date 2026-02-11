import pyautogui, pygetwindow as gw
import subprocess
import os
from datetime import datetime
from PIL import ImageGrab
import numpy as np
import cv2
import io

def get_window(title: str) -> gw.Win32Window:
    '''
    Finds title within a string and returns window
    '''
    try:
        find_title = next(filter(lambda p: title in p, gw.getAllTitles()))
        match = gw.getWindowsWithTitle(find_title)[0]
        return match
    except Exception as e:
        print(f"Window not found: {e}")
        return None

def activate_window(window: gw.Win32Window) -> bool:
    try:
        window.activate()
        return True
    except Exception as e:
        print(f"Window not found: {e}")
        return False

def kill_window(window: gw.Win32Window) -> bool:
    try:
        pid = window.processId
        subprocess.run(
            ["taskkill", "/F", "/PID", str(pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except Exception as e:
        print(f"Window was not found {e}")
        return False

def move_window(window: gw.Win32Window, x: int, y: int) -> None:
    try:
        window.moveTo(x, y)
    except Exception as e:
        print(f"Error: {e}")

def resize_window(window: gw.Win32Window, x: int, y: int) -> None:
    try:
        window.resizeTo(x, y)
    except Exception as e:
        print(f"Error {e}")

def get_winSize(window: gw.Win32Window):
    try:
        return window.size
    except Exception as e:
        print(f"Error {e}")

def screenshot_window(window: gw.Win32Window, name: str, retImg: bool):
    try:
        x, y = window.topleft

        if name is None:
            time_stamp = str.replace(datetime.now().strftime("%D-%H-%M-%S"), "/", "_")
            name = f"{window.title}-{time_stamp}.png"

        absDir = os.path.abspath(__file__)
        relDir = os.path.join(os.path.dirname(os.path.dirname(absDir)), "Screenshots")

        os.makedirs(relDir, exist_ok=True)

        fullPath = os.path.join(relDir, name)
        screenshot_image = pyautogui.screenshot(
            imageFilename=fullPath,
            region=[x, y, window.width, window.height],
            allScreens=False
        )

        if retImg:
            return screenshot_image

    except Exception as e:
        print(f"{type(window)} experienced an error when screenshotting : {e}")

def screen_shot_memory(window: gw.Win32Window | None = None):
    if window is None:
        window = gw.getActiveWindow()
    left, top, width, height = window.box
    img = ImageGrab.grab(bbox=(left, top, left + width, top + height))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def screenshot_region(region: tuple[int, int]):
    '''
    Region: Where the screenshot will be taken (x,y,width,height)
    Returns: NumPy array (BGR), Ment for EasyOCR and CV2 usage
    '''
    try:
        img = ImageGrab.grab(bbox=region)
        img_np = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return img_np
    except Exception as e:
        print(f"Region {region} experienced an error when screenshotting : {e}")

def clear_screenshot_cache():
    if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Screenshots")):
        screen_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Screenshots")
        for e in os.listdir(screen_path):
            os.remove(f"{screen_path}\\{e}")
