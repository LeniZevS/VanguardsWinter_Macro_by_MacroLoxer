from pyautogui import *
import keyboard

import time
import pyautogui

save_mouse_location = 'z'
stop_key = 'n'
mouse_info2 = {}
mouse_just_pos = []
#Togglables
BotOn = True

def add_cords(cords):
    color = pyautogui.pixel(cords[0],cords[1])
    pos_info = {(cords.x, cords.y): color}
    mouse_info2.update(pos_info)
    mouse_just_pos.append((cords.x,cords.y))

def bot_toggle():
    global BotOn
    BotOn = not BotOn
    
    

keyboard.add_hotkey(save_mouse_location, lambda: add_cords(pyautogui.position()))
keyboard.add_hotkey(stop_key, bot_toggle)


while BotOn:
    time.sleep(0.1)

print(f"Mouse position with color {mouse_info2}")
print(f"Just mouse cordinates: {mouse_just_pos}")

