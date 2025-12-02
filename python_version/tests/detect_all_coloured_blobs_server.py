import cv2
import numpy as np
from flask import Flask, Response

try:
    from picamera2 import Picamera2, MappedArray
    from picamera2.encoders import H264Encoder, Quality
    from picamera2.outputs import CircularOutput
    from libcamera import controls
    from libcamera import Transform
    from bisect import bisect_left
    picamera_exists = True 
  
except ImportError:
    Picamera2 = None
    picamera_exists = False

print("picamera_exists",picamera_exists)

camera = None
if picamera_exists:
    camera = Picamera2()
    camera.configure(camera.create_preview_configuration(main={"format":"XRGB8888", "size":(640, 480)}))
    camera.start()


def create_mask():
  image = camera.capture_array("main")

  # Convert the image to HSV colour space
  hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

  # Define lower and upper HSV boundaries for the colours
  # running it theough this - https://onlinetools.com/image/show-hsv-image-colors
  # looks like I can filter based on saturation only, 2nd arg

  lower_colour = np.array([0, 200, 0])
  upper_colour = np.array([179, 255, 255])

  # Create a mask with cv2.inRange to detect colours
  colour_mask = cv2.inRange(hsv_image, lower_colour, upper_colour)

  # Use bitwise AND to extract the colours from the original image
  result = cv2.bitwise_and(image, image, mask=colour_mask)

  # Creating contour to track colours
  contours, hierarchy = cv2.findContours(colour_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

  for pic, contour in enumerate(contours):
    area = cv2.contourArea(contour)
    if(area > 300):
      x, y, w, h = cv2.boundingRect(contour)
      image = cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)
      # because always oblongs
      rx = int(x+(w/2))
      ry = int(y+(h/2))
      colour = result[ry,rx]
      print("colour",colour)
      cv2.putText(image, str(colour), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255))

  ret, buffer = cv2.imencode('.jpg', result)
  frame = buffer.tobytes()
  yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


app = Flask(__name__)

@app.route('/picamera2_feed')
def video_feed():
    return Response(create_mask(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ =='__main__':
    app.run(host='0.0.0.0', port=5000)

  
