# just reads the image and finds the keypoints

import numpy as np
import cv2
import time


    
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

params = cv2.SimpleBlobDetector_Params()
detector = cv2.SimpleBlobDetector_create(params)
    

if picamera_exists:
    camera = Picamera2()
    camera.start()
    

def go():
    time.sleep(1)
    im = camera.capture_array("main")
    keypoints = detector.detect(im)
    print("keypoints",keypoints)   

# Draw detected blobs as red circles.
# cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS ensures the size of the circle corresponds to the size of blob
# ~https://stackoverflow.com/questions/30291958/feature-detection-with-opencv-fails-with-seg-fault~
# ~https://learnopencv.com/blob-detection-using-opencv-python-c/~

    im_with_keypoints = cv2.drawKeypoints(im, keypoints, np.array([]), (0,0,255), cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

# font
    font = cv2.FONT_HERSHEY_SIMPLEX
# fontScale
    fontScale = 0.5
# Blue color in BGR
    color = (255, 0, 0)
    thickness = 1
    list_of_y = []
    keypoints_by_x = {}

    for k in keypoints: 
       print(k.pt)

       x = round(k.pt[0],0)
       y = round(k.pt[1],0)
  # this is adding them in the wrong order
  # needs to be ordered by x 
  #list_of_y.append(y)
       keypoints_by_x[x]=y
       s = round(k.size,0)
       print("size",s)

       xy_str = "%d,%d" % (x,y)

       org = (int(x)-10,int(y)+40)
       cv2.putText(im_with_keypoints, xy_str, org, font, 
                   fontScale, color, thickness, cv2.LINE_AA)

    cv2.imwrite("test_nokp.png",im_with_keypoints)
    cv2.imwrite("test_kp.png",im)
#print("keypoints_by_x",keypoints_by_x)
#kp_by_x_sorted = dict(sorted(keypoints_by_x.items()))
#print("keypoints_by_x_sorted",kp_by_x_sorted)

go()
