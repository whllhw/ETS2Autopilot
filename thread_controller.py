import threading
import time

import pyvjoy
from database import Settings


class ControllerThread(threading.Thread):
    print_lock = threading.Lock()
    running = True
    autopilot = False
    angle = 0

    def __init__(self):
        threading.Thread.__init__(self, daemon=True)
        ControllerThread.running = True
        ControllerThread.autopilot = False
        self.controller = Settings().get_value(Settings.CONTROLLER)
        self.vjoy = Settings().get_value(Settings.VJOY_DEVICE)
        self.axis = Settings().get_value(Settings.STEERING_AXIS)

    def stop(self):
        with ControllerThread.print_lock:
            ControllerThread.running = False

    def run(self):
        vjoy = pyvjoy.VJoyDevice(self.vjoy)
        vjoy.reset()
        vjoy.set_axis(pyvjoy.HID_USAGE_X, 0x4000)
        while ControllerThread.running:
            time.sleep(0.15)
            if not ControllerThread.autopilot:
                pass
                # angle = round((joystick.get_axis(self.axis) + 1) * 32768 / 2)
            else:
                angle = ControllerThread.angle
                vjoy.set_axis(pyvjoy.HID_USAGE_X, angle)
        vjoy.set_axis(pyvjoy.HID_USAGE_X, 0x4000)

    def is_running(self):
        return self.running

    def set_autopilot(self, value):
        with ControllerThread.print_lock:
            ControllerThread.autopilot = value

    def set_angle(self, value):
        with ControllerThread.print_lock:
            ControllerThread.angle = value
