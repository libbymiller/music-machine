import cv2
import numpy as np

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
    camera.start()


image = camera.capture_array("main")


# Load the image
#image=cv2.imread("./orange_brick.png")

# Convert the image to HSV color space
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define lower and upper HSV boundaries for the color blue
#lower_blue = np.array([20, 150, 0])
#upper_blue = np.array([24, 255, 255])

# orange
lower_orange = np.array([100, 150, 0])
upper_orange = np.array([140, 255, 255])

# Create a mask with cv2.inRange to detect blue colors
orange_mask = cv2.inRange(hsv_image, lower_orange, upper_orange)

# Use bitwise AND to extract the blue color from the original image
result = cv2.bitwise_and(image, image, mask=orange_mask)

# Creating contour to track red color
contours, hierarchy = cv2.findContours(blue_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

for pic, contour in enumerate(contours):
  area = cv2.contourArea(contour)
  if(area > 300):
    x, y, w, h = cv2.boundingRect(contour)
    image = cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.putText(image, "Orange Colour", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255))


cv2.imwrite("test_orange.png",image)
# Display the original image, mask, and result
#cv2.imshow("orig",image)       # Display original image
#cv2.waitKey(0)
#cv2.imshow("mask",orange_mask)   # Display orange mask
#cv2.waitKey(0)
#cv2.imshow("res",result)      # Display the result where orange is detected
#cv2.waitKey(0)

