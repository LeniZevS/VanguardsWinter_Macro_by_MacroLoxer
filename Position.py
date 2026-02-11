
import time
from Tools import winTools as wt

def set_rblx(): # Start up sequence
    window = wt.get_window("Roblox") # Get roblox window
    global roblox_window
    roblox_window = window
        
    wt.resize_window(roblox_window, 1100, 800)  # Resize window
    wt.move_window(roblox_window, 200, 100)  # Move window to top left corner
       
    wt.activate_window(window=window) # Activate window
    time.sleep(0.5)

set_rblx()