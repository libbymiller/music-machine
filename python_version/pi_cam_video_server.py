# version with real data
# with https://github.com/SimpleDevs-Dev/PiCamera2Stream
# so this works but only sends one frame after each round of music

from threading import Thread

import cv2
import numpy as np
import musicalbeeps
import time

from flask import Flask, Response
import argparse


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

# Set up parser
parser = argparse.ArgumentParser(description="Pipe footage from PiCamera2 to Flask-based local server.")
# Add arguments to server
parser.add_argument("-p", "--port", help="The port you wish to launch the server on. Default=5000", type=int, default=5000)
parser.add_argument('-x', "--size_x", help="The intended width of the camera output. Default=640", type=int, default=640)
parser.add_argument('-y', "--size_y", help="The intended height of the camera output. Default=480", type=int, default=480)
parser.add_argument('-ae', "--auto_exposure", help="Do we want the camera to perform auto-exposure correction? Default=True", type=bool, default=True)
parser.add_argument('-awb', "--auto_white_balance", help="Do we want the camera to auto-select the appropriate white balance? Default=True", type=bool, default=True)
parser.add_argument('-inv', "--invert", help="Do we invert vertically?", type=bool, default=False)

args = parser.parse_args()

if picamera_exists:
# Set up the camera
  camera = Picamera2()
  camera.configure(camera.create_preview_configuration(main={"format":"XRGB8888", "size":(args.size_x, args.size_y)}))
  camera.set_controls({"AeEnable":args.auto_exposure,"AwbEnable":args.auto_white_balance})
  camera.start()


# https://gist.github.com/devxpy/063968e0a2ef9b6db0bd6af8079dad2a
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
OCTAVES = list(range(11))
NOTES_IN_OCTAVE = len(NOTES)

def number_to_note(number: int) -> tuple:
    octave = number // NOTES_IN_OCTAVE
    assert octave in OCTAVES, errors['notes']
    assert 0 <= number <= 127, errors['notes']
    note = NOTES[number % NOTES_IN_OCTAVE]
    # this returns things like  C#6 when it should be C6#
    # so if note has  # then swap the last two characters
    if("#" in note):
      n = list(note)
      ln = n[-1]
      pn = n[-2]
      n[-2]=ln
      n[-1]=pn
    return note, octave


def note_to_number(note: str, octave: int) -> int:
    assert note in NOTES, errors['notes']
    assert octave in OCTAVES, errors['notes']

    note = NOTES.index(note)
    note += (NOTES_IN_OCTAVE * octave)

    assert 0 <= note <= 127, errors['notes']

    return note

player = musicalbeeps.Player(volume = 0.3,
                            mute_output = False)


def find_closest_value(givenList, target):
    #print("closest value",givenList,target)
    def difference(givenList):
        return abs(givenList - target)
    
    result = min(givenList, key=difference)
    return result


def convert_raw_to_midi(key,raw,factor,offset):
    to_return = []
    for r in raw:
      scaled_raw = r*factor + offset
      #print("scaled_raw",scaled_raw)
      result = find_closest_value(key,scaled_raw) 
      to_return.append(result)  
    #print("to_return",to_return)
    return to_return


def get_factor_and_offset(key,raw):
    print("key",key)
    print("raw",raw)
    k = (max(key) - min(key)) / (max(raw) - min(raw))
    c = max(key) - k * max(raw)
    #print("k",k)
    #print("c",c)
    return k,c


#key = [36, 38, 40,41,43,45,47,48,50]
# piano above middle C
key1 = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84, 86, 88, 89, 91, 93, 95, 96]
# c# minor c# D# E F# G# A B  C#
key2 = [61, 63, 64, 66, 68, 69, 71, 73, 74, 76, 78, 81, 83, 85, 87, 88, 90, 92, 93, 95, 97]

# rough and ready assume length is 700
l = 700

def detect_orange(image):
  orange_detected = False
# Convert the image to HSV color space
  hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Define lower and upper HSV boundaries for the colour orange
  lower_orange = np.array([20, 150, 0])
  upper_orange = np.array([24, 255, 255])

# Create a mask with cv2.inRange to detect orange colours
  orange_mask = cv2.inRange(hsv_image, lower_orange, upper_orange)

# Use bitwise AND to extract the orange colour from the original image
  result = cv2.bitwise_and(image, image, mask=orange_mask)

# Creating contour to track orange color
  contours, hierarchy = cv2.findContours(orange_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

  for pic, contour in enumerate(contours):
    area = cv2.contourArea(contour)
    if(area > 300):
      x, y, w, h = cv2.boundingRect(contour)
      image = cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
      print("ORANGE DETECTED")
      orange_detected = True

  cv2.imwrite("test_orange.png",image)
  return orange_detected


def play_notes(notes):
    #time.sleep(1)
    print("playing notes!")
    for n in notes:
      print("n2note",number_to_note(n))
      nn = number_to_note(n)
      tmp_list = list(nn[0])
      print("tmp_list",tmp_list)

      # sharps come out wrong, fixing that
      if(len(tmp_list)==2):
        n_arr = [tmp_list[0], str(nn[1]), tmp_list[1]]
      else:
        n_arr = [tmp_list[0], str(nn[1])]
      print(n_arr)
      #here we want to circle the note too in the image and return it
      # like this???
      frame = camera.capture_array("main")
      ret, buffer = cv2.imencode('.jpg', frame)
      frame = buffer.tobytes()
      yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

      player.play_note("".join(n_arr), 0.3)




app = Flask(__name__)


# no idea how to make his work???
# separate out the detection, and make the thread the music part
def generate_frames():
    thread = None

    while True:
       time.sleep(2)
       raw_data = []
       list_of_x = []
       list_of_y = []
       keypoints_by_x = {}

       array = camera.capture_array("main")
       keypoints = detector.detect(array)
       print("keypoints",keypoints)

       for k in keypoints: 
          print(k.pt)
          x = round(k.pt[0],0)
          y = round(k.pt[1],0)
          # this is adding them in the wrong order
          # needs to be ordered by x 
          #list_of_y.append(y)
          keypoints_by_x[x]=y
          s = round(k.size,0)
          #print("size",s)

          #print("keypoints_by_x",keypoints_by_x)
       kp_by_x_sorted = dict(sorted(keypoints_by_x.items()))
       print("keypoints_by_x_sorted",kp_by_x_sorted)

       for kps in kp_by_x_sorted:
          list_of_x.append(kps)
          list_of_y.append(kp_by_x_sorted[kps])

       # hack
       list_of_x.append(-1)
       list_of_y.append(-1)

       print("list_of_y",list_of_y)
       for ll in list_of_y:
          raw_data.append(l-ll)

       print("new_raw_data",raw_data)


       # how do we get the right ordering??
       # is it reversed??
       key = None
       if(detect_orange(array)):
            key = key2
            print("Key is C# minor")
       else:
            key = key1
            print("Key is C major")

       k,c = get_factor_and_offset(key,sorted(raw_data))
       notes = convert_raw_to_midi(key,raw_data,k,c)

       print("notes",len(notes))
       print("playing notes!")
       count = 0
       for n in notes:
          print("n2note",number_to_note(n))
          nn = number_to_note(n)
          tmp_list = list(nn[0])
          print("tmp_list",tmp_list)

          # sharps come out wrong, fixing that
          if(len(tmp_list)==2):
            n_arr = [tmp_list[0], str(nn[1]), tmp_list[1]]
          else:
            n_arr = [tmp_list[0], str(nn[1])]
          print(n_arr)
          #here we want to circle the note too in the image and return it
          # like this???
          frame = camera.capture_array("main")
          x = int(list_of_x[count])
          y = int(list_of_y[count])
          print("coords?",x,y)
          count = count + 1
          w = h = 20
          frame = cv2.rectangle(frame, (x -w, y -w), (x + w, y + h), (0, 0, 255), 1)

          ret, buffer = cv2.imencode('.jpg', frame)
          frame = buffer.tobytes()
          yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
          #hack!
          if(x>0):
            player.play_note("".join(n_arr), 0.3)


@app.route('/picamera2_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ =='__main__':
    app.run(host='0.0.0.0', port=args.port)
