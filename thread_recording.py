# coding:utf-8
import threading
import time

import numpy as np
from PIL import ImageGrab
import cv2
from database import Settings, Data
import functions
import os
from ets2_telemetry import get_steering_throttle_speed
import keyboard


class RecordingThread(threading.Thread):
    lock = threading.Lock()
    running = True

    def __init__(self, statusbar, image_front, fill_sequence_list):
        threading.Thread.__init__(self, daemon=True)
        with RecordingThread.lock:
            RecordingThread.running = True

        self.statusbar = statusbar
        self.image_front = image_front
        self.running = True
        self.fill_sequence_list = fill_sequence_list

        self.recording = False
        self.sequence_id = None
        if not os.path.exists("captured/"):
            os.mkdir("captured")

    def stop(self):
        with RecordingThread.lock:
            RecordingThread.running = False
            self.fill_sequence_list()

    def record_callback(self,d):
        self.recording = not self.recording
        if self.recording:  # started recording
            self.sequence_id = d.add_sequence()
        else:  # stopped recording
            self.fill_sequence_list()

    def run(self):
        s = Settings()
        d = Data(batch=True)

        img_id = d.get_next_fileid()
        self.recording = False

        maneuver = 0  # 0 - normal, 1 - indicator left, 2 - indicator right
        last_record = functions.current_milli_time()

        keyboard.add_hotkey('shift+w', self.record_callback, args=[d])
        while RecordingThread.running:
            # Capture the whole game
            frame_raw = ImageGrab.grab(bbox=functions.get_screen_bbox())
            frame = np.uint8(frame_raw)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            main = frame[s.get_value(Settings.IMAGE_FRONT_BORDER_TOP):s.get_value(Settings.IMAGE_FRONT_BORDER_BOTTOM),
                   s.get_value(Settings.IMAGE_FRONT_BORDER_LEFT): s.get_value(Settings.IMAGE_FRONT_BORDER_RIGHT)]
            # gray = cv2.cvtColor(main, cv2.COLOR_BGR2GRAY)
            # blur_gray = cv2.GaussianBlur(gray, (3, 3), 0)
            # edges = cv2.Canny(blur_gray, 50, 150)
            # dilated = cv2.dilate(edges, (3,3), iterations=2)

            # Resize image to save some space (height = 100px)
            ratio = main.shape[1] / main.shape[0]
            resized = cv2.resize(main, (round(ratio * 100), 100))

            # cv2.imshow('cap', dilated)
            # cv2.imshow('resized', resized)
            functions.set_image(main.copy(), self.image_front)

            axis, throttle, speed = get_steering_throttle_speed()
            if axis == 0:
                maneuver = 0
            elif axis > 0:
                maneuver = 1
            else:
                maneuver = 2
            if self.recording:
                self.statusbar.showMessage("Recording: active | Indicator: %s" % functions.get_indicator(maneuver))
            else:
                self.statusbar.showMessage("Recording: inactive | Indicator: %s" % functions.get_indicator(maneuver))
            # Save frame every 150ms
            if self.recording:
                cv2.imwrite("captured/%d.png" % img_id, resized)
                d.add_image("%d.png" % img_id, axis, speed, throttle, maneuver, self.sequence_id)
                img_id += 1
                # at least wait 150ms
                wait_milli_time = functions.current_milli_time() - last_record - 150
                if wait_milli_time < 0:
                    time.sleep(-wait_milli_time / 1000)
                last_record = functions.current_milli_time()
            else:
                time.sleep(0.15)
        keyboard.clear_hotkey('shift+w')
        d.append()
