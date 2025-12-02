import time
import picamera2
import numpy as np

with picamera2.Picamera2() as camera:
    camera.start()
    time.sleep(1)
    array = camera.capture_array("main")
    # TODO Do something with array
    print(array.shape)
