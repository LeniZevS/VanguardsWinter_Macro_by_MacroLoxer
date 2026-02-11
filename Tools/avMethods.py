
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # needed to get py tools
from Tools import botTools as bt
from Tools import winTools as wt
# Inputs
import time

# Text Detection 
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = os.path.join( # ocr
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tesseract", "tesseract.exe"
)

os.environ["TESSDATA_PREFIX"] = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tesseract", "tessdata"
)

def get_wave(new_region: tuple[int, int, int, int] | None = None) -> int: # Gets the current wave of the match
    '''
    NEED TO BE IN MATCH 
    Returns the wave the player is on.
    '''
    try:
        
        x, y, w, h =  477,154,605,179 # Wave num location
        regionArea = (x,y,w,h)
        if new_region is not None:
            regionArea=new_region
        screenshot = wt.screenshot_region(region=regionArea) # Get image of num
    
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) # Grayscale for speed
        _, threshold = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY) # Threshold so only the num is there
        thresh = cv2.resize(threshold, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC) # resize for accuracy
        wave = pytesseract.image_to_string(thresh, config='--psm 7 -c tessedit_char_whitelist=0123456789') # Number detector [0,9] no char
        if not wave.strip():
            return -1
        return int(wave) # Returns the wave that was found
        
    except Exception as e:
        print(f"Error in get_wave: {e}")
def read_region(region: tuple[int, int, int, int] | None = None) -> int: # Gets the current wave of the match
    '''
    reads a region
    '''
    try:
        
        regionArea = region
        screenshot = wt.screenshot_region(region=regionArea) # Get image of num
    
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY) # Grayscale for speed
        _, threshold = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY) # Threshold 
        thresh = cv2.resize(threshold, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC) # resize for accuracy
        text = pytesseract.image_to_string(thresh, config='--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') 
        if not text.strip():
            return text
        return text 
        
    except Exception as e:
        print(f"Error in get_wave: {e}")
def restart_match():
    '''sybau'''
    #(227, 868), (1150, 454), (681, 565), (726, 570), (1212, 264)
    bt.click(227, 868)
    time.sleep(0.8)
    bt.click(1150, 454)
    time.sleep(0.8)
    bt.click(681, 565)
    time.sleep(1.5)
    bt.click(726, 560)
    time.sleep(0.7)
    bt.click(1212, 254)
    time.sleep(0.7)

