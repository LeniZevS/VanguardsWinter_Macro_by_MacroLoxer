
import os
from pyautogui import *
import time
import pyautogui
import ctypes

def does_exist(imageDirectory: str, confidence: float, grayscale: bool, region: tuple | None=None) -> bool:
    try:
   
        name = imageDirectory
        imageDirectory = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Resources",
        imageDirectory)
        if region is None:
            check = pyautogui.locateOnScreen(imageDirectory, grayscale=grayscale, confidence=confidence)
        else:
            check = pyautogui.locateOnScreen(imageDirectory, grayscale=grayscale, confidence=confidence, region=region)
     
        if check is not None:
            return True
        return False
    except Exception as e:
        return False

def click_image(imageDirectory: str, confidence: float, grayscale: bool, offset: tuple[int,int], region: tuple| None=None) -> bool:
    try:
        imageDirectory = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"Resources", imageDirectory)
        if region is None:
            image_location = pyautogui.locateOnScreen(imageDirectory, grayscale=grayscale, confidence=confidence)
        else:
            image_location = pyautogui.locateOnScreen(imageDirectory, grayscale=grayscale, confidence=confidence, region=region)
        if image_location is not None:
            image_center = pyautogui.center(image_location)
            if offset == (0,0):
                click(image_center.x, image_center.y)
                return True
            else:
                click(image_center.x+offset[0], image_center.y+offset[1])
                return True
    except Exception as e:
        return False

def click(x: int,y: int, delay: int | None=None,) -> None: # Set curser position and click
    '''
    Click at cordinate x,y
    If cordinate is abs pass in window_pos/topleft (x,y) of the active foregroundww
    '''
    if delay is None:
        delay = 0.1 # Standard click delaya
    else:
        delay=delay
    pyautogui.moveTo(x,y)
    time.sleep(delay)
    ctypes.windll.user32.mouse_event(0x0001, 0, 1, 0, 0)
    pyautogui.click()
    