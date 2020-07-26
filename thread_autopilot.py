import threading
from PIL import ImageGrab
import tensorflow as tf
import numpy as np
import scipy.misc
import cv2
import time
from database import Settings, Data
import model
import functions
import keyboard

class AutopilotThread(threading.Thread):
    lock = threading.Lock()
    running = True

    def __init__(self, statusbar, controller_thread, steering_wheel, image_front):
        threading.Thread.__init__(self, daemon=True)

        with AutopilotThread.lock:
            AutopilotThread.running = True

        self.statusbar = statusbar
        self.controller_thread = controller_thread
        self.steering_wheel_ui = steering_wheel
        self.image_front_ui = image_front

        self.running = True
        self.country_code = Settings().get_value(Settings.COUNTRY_DEFAULT)
        self.b_autopilot = Settings().get_value(Settings.AUTOPILOT)
        self.steering_axis = Settings().get_value(Settings.STEERING_AXIS)

        self.sess = tf.InteractiveSession(graph=model.g)
        saver = tf.train.Saver()
        saver.restore(self.sess, "save/model_%s.ckpt" % self.country_code)

    def stop(self):
        with AutopilotThread.lock:
            AutopilotThread.running = False

    def hotkey_callback(self):
        self.autopilot = not self.autopilot

    def run(self):
        # Settings instance
        s = Settings()
        # State of autopilot
        self.autopilot = False
        img_wheel = cv2.imread('steering_wheel_image.jpg', 0)
        img_wheel = cv2.cvtColor(img_wheel, cv2.COLOR_BGR2RGB)
        functions.set_image(img_wheel.copy(), self.steering_wheel_ui)
        rows, cols, _ = img_wheel.shape
        keyboard.add_hotkey('shift+w', self.hotkey_callback)
        start_time = functions.current_milli_time()
        while AutopilotThread.running:
            self.controller_thread.set_autopilot(self.autopilot)
            # Get frame of game
            frame_raw = ImageGrab.grab(bbox=functions.get_screen_bbox())
            frame = np.uint8(frame_raw)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Relevant image region for steering angle prediction
            main = frame[s.get_value(Settings.IMAGE_FRONT_BORDER_TOP):s.get_value(Settings.IMAGE_FRONT_BORDER_BOTTOM),
                   s.get_value(Settings.IMAGE_FRONT_BORDER_LEFT):s.get_value(Settings.IMAGE_FRONT_BORDER_RIGHT)]
            # Resize the image to the size of the neural network input layer
            image = scipy.misc.imresize(main, [66, 200]) / 255.0
            # Let the neural network predict the new steering angle
            y_eval = model.y.eval(session=self.sess, feed_dict={model.x: [image], model.keep_prob: 1.0})[0][0]
            degrees = y_eval * 180 / scipy.pi
            steering = int(round((degrees + 180) / 180 * 32768 / 2))  # Value for vjoy controller

            # Set the value of the vjoy joystick to the predicted steering angle
            if self.autopilot:
                self.controller_thread.set_angle(steering)
                self.statusbar.showMessage("Autopilot active, steering: " + str(steering))
            else:
                self.statusbar.showMessage("Autopilot inactive")
            M = cv2.getRotationMatrix2D((cols / 2, rows / 2), -degrees, 1)
            dst = cv2.warpAffine(img_wheel, M, (cols, rows))
            functions.set_image(dst.copy(), self.steering_wheel_ui)
            functions.set_image(main.copy(), self.image_front_ui)
            wait_time = functions.current_milli_time() - start_time - 40
            if wait_time < 0:
                time.sleep(-wait_time / 1000)
            start_time = functions.current_milli_time()
        keyboard.clear_hotkey('shift+w')
        self.controller_thread.set_autopilot(False)
