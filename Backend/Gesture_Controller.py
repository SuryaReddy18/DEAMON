import cv2
import math
import pyautogui
import numpy as np
from ultralytics import YOLO
from enum import IntEnum
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import screen_brightness_control as sbcontrol

# Load YOLOv8 model
model = YOLO('yolov8n.pt')  # Use a custom-trained YOLO model for hand detection if available
print(model.names)


# Gesture Encodings
class Gest(IntEnum):
    FIST = 0
    PALM = 1
    PINCH_MAJOR = 2
    PINCH_MINOR = 3
    V_GEST = 4
    TWO_FINGER_CLOSED = 5
    INDEX = 6
    MID = 7

# Multi-handedness Labels
class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1

# Convert YOLO bounding boxes to recognizable Gestures
class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label

    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_dist(self, points):
        if not self.hand_result:
            return 0
        x1, y1, x2, y2 = self.hand_result
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        return math.sqrt(dx**2 + dy**2)

    def set_finger_state(self):
        if self.hand_result is None:
            return

        # Simulate finger state based on bounding box aspect ratio
        x1, y1, x2, y2 = self.hand_result
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        aspect_ratio = width / height

        if aspect_ratio > 1.5:
            self.finger = Gest.PALM
        elif aspect_ratio < 0.8:
            self.finger = Gest.FIST
        else:
            self.finger = Gest.MID

    def get_gesture(self):
        if self.hand_result is None:
            return Gest.PALM

        current_gesture = Gest.PALM
        if self.finger == Gest.FIST:
            current_gesture = Gest.FIST
        elif self.finger == Gest.PALM:
            current_gesture = Gest.PALM
        elif self.finger == Gest.MID:
            current_gesture = Gest.MID

        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0

        self.prev_gesture = current_gesture

        if self.frame_count > 4:
            self.ori_gesture = current_gesture
        return self.ori_gesture

# Executes commands according to detected gestures
class Controller:
    tx_old = 0
    ty_old = 0
    trial = True
    flag = False
    grabflag = False
    pinchmajorflag = False
    pinchminorflag = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    prev_hand = None
    pinch_threshold = 0.3

    @staticmethod
    def changesystembrightness():
        currentBrightnessLv = sbcontrol.get_brightness(display=0) / 100.0
        currentBrightnessLv += Controller.pinchlv / 50.0
        if currentBrightnessLv > 1.0:
            currentBrightnessLv = 1.0
        elif currentBrightnessLv < 0.0:
            currentBrightnessLv = 0.0
        sbcontrol.fade_brightness(int(100 * currentBrightnessLv), start=sbcontrol.get_brightness(display=0))

    @staticmethod
    def changesystemvolume():
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        currentVolumeLv = volume.GetMasterVolumeLevelScalar()
        currentVolumeLv += Controller.pinchlv / 50.0
        if currentVolumeLv > 1.0:
            currentVolumeLv = 1.0
        elif currentVolumeLv < 0.0:
            currentVolumeLv = 0.0
        volume.SetMasterVolumeLevelScalar(currentVolumeLv, None)

    @staticmethod
    def scrollVertical():
        pyautogui.scroll(120 if Controller.pinchlv > 0.0 else -120)

    @staticmethod
    def scrollHorizontal():
        pyautogui.keyDown('shift')
        pyautogui.keyDown('ctrl')
        pyautogui.scroll(-120 if Controller.pinchlv > 0.0 else 120)
        pyautogui.keyUp('ctrl')
        pyautogui.keyUp('shift')

    @staticmethod
    def get_position(hand_result):
        if hand_result is None:
            return None
        x1, y1, x2, y2 = hand_result
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        return (center_x, center_y)

    @staticmethod
    def handle_controls(gesture, hand_result):
        x, y = None, None
        if gesture != Gest.PALM:
            x, y = Controller.get_position(hand_result)

        if gesture == Gest.V_GEST:
            Controller.flag = True
            pyautogui.moveTo(x, y, duration=0.1)

        elif gesture == Gest.FIST:
            if not Controller.grabflag:
                Controller.grabflag = True
                pyautogui.mouseDown(button="left")
            pyautogui.moveTo(x, y, duration=0.1)

        elif gesture == Gest.MID and Controller.flag:
            pyautogui.click()
            Controller.flag = False

        elif gesture == Gest.INDEX and Controller.flag:
            pyautogui.click(button='right')
            Controller.flag = False

        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
            pyautogui.doubleClick()
            Controller.flag = False

        elif gesture == Gest.PINCH_MINOR:
            Controller.scrollVertical()

        elif gesture == Gest.PINCH_MAJOR:
            Controller.changesystembrightness()

# Main Gesture Controller Class
class GestureController:
    gc_mode = 0
    cap = None
    CAM_HEIGHT = None
    CAM_WIDTH = None
    hr_major = None  # Right Hand by default
    hr_minor = None  # Left hand by default
    dom_hand = True

    def __init__(self):
        GestureController.gc_mode = 1
        GestureController.cap = cv2.VideoCapture(0)
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)

    def classify_hands(self, boxes, img_width):
        left, right = None, None
        for box in boxes:
            x_center = (box[0] + box[2]) / 2
            if x_center < img_width / 2:
                left = box
            else:
                right = box

            if self.dom_hand:
                self.hr_major = right
                self.hr_minor = left
            else:
                self.hr_major = left
                self.hr_minor = right

    def start(self):
        handmajor = HandRecog(HLabel.MAJOR)
        handminor = HandRecog(HLabel.MINOR)

        while GestureController.cap.isOpened() and GestureController.gc_mode:
            success, image = GestureController.cap.read()

            if not success:
                print("Ignoring empty camera frame.")
                continue

            img_rgb = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)
            results = model.predict(img_rgb)

            # Extract YOLO's bounding boxes for hands
            hand_boxes = [
                box.xyxy[0].tolist() for box in results[0].boxes if int(box.cls) == 0  # Hand class
            ]

            if hand_boxes:
                img_width = image.shape[1]
                self.classify_hands(hand_boxes, img_width)

                handmajor.update_hand_result(self.hr_major)
                handminor.update_hand_result(self.hr_minor)

                handmajor.set_finger_state()
                handminor.set_finger_state()
                gest_name = handminor.get_gesture()

                if gest_name == Gest.PINCH_MINOR:
                    Controller.handle_controls(gest_name, handminor.hand_result)
                else:
                    gest_name = handmajor.get_gesture()
                    Controller.handle_controls(gest_name, handmajor.hand_result)

                # Draw bounding boxes
                for box in hand_boxes:
                    x1, y1, x2, y2 = map(int, box)
                    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            else:
                Controller.prev_hand = None

            cv2.imshow('Gesture Controller', image)
            if cv2.waitKey(5) & 0xFF == 13:
                break

        GestureController.cap.release()
        cv2.destroyAllWindows()

# Run the Gesture Controller
if __name__ == "__main__":
    gc = GestureController()
    gc.start()