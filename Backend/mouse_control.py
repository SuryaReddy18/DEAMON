import cv2
import torch
import numpy as np
import pyautogui
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Load YOLOv5 Model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:/DAEMON/Backend/best.pt', force_reload=True)

model.conf = 0.5  # Confidence threshold

# Audio Control Setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, 0, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
minVol, maxVol, _ = volume.GetVolumeRange()

# Variables for controlling actions
click_threshold = 50
click_cooldown = 0
last_brightness = 50
last_volume = (minVol + maxVol) / 2


def process_frame(frame):
    """Detect hand using YOLOv5 and return bounding box."""
    results = model(frame)
    detections = results.xyxy[0].cpu().numpy()
    hands = [d for d in detections if int(d[5]) == 0]  # Assuming class 0 is 'hand'
    return hands


def control_mouse(hands, frame):
    """Move and click mouse based on detected hand."""
    global click_cooldown
    
    if len(hands) == 0:
        return
    
    x1, y1, x2, y2, conf, cls = hands[0]  # Use first detected hand
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    
    screen_width, screen_height = pyautogui.size()
    mouse_x = np.interp(center_x, [0, frame.shape[1]], [0, screen_width])
    mouse_y = np.interp(center_y, [0, frame.shape[0]], [0, screen_height])
    pyautogui.moveTo(mouse_x, mouse_y)
    
    # Clicking logic based on bounding box width
    if (x2 - x1) < click_threshold and click_cooldown <= 0:
        pyautogui.click()
        click_cooldown = 20
    
    if click_cooldown > 0:
        click_cooldown -= 1


def control_brightness_volume(hands):
    """Adjust screen brightness and volume based on hand position."""
    global last_brightness, last_volume
    
    if len(hands) == 0:
        return
    
    _, y1, _, y2, _, _ = hands[0]
    hand_height = y2 - y1
    
    new_brightness = int(np.interp(hand_height, [50, 300], [0, 100]))
    new_volume = np.interp(hand_height, [50, 300], [minVol, maxVol])
    
    if abs(new_brightness - last_brightness) > 5:
        sbc.set_brightness(new_brightness)
        last_brightness = new_brightness
    
    if abs(new_volume - last_volume) > 1.5:
        volume.SetMasterVolumeLevel(new_volume, None)
        last_volume = new_volume


def main():
    global click_cooldown
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame, 1)
        
        hands = process_frame(frame)
        control_mouse(hands, frame)
        control_brightness_volume(hands)
        
        for hand in hands:
            x1, y1, x2, y2, _, _ = hand
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        
        cv2.imshow("Hand Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
