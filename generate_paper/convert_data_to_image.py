# sizing is now okish
# resizing works
# and now A4 for printing
# expects one number per line
# only tested with files with ~ 30 items

import numpy as np
from PIL import Image
import cv2
import sys

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
      
    print("k",k)
    print("c",c)
    return k,c


def generate_image(array_of_rows, scale_factor):
        numpy_csv = array_of_rows.astype('uint8')*255
        print("shape",numpy_csv.shape[0],numpy_csv.shape[1])

        # cv2 swaps axes
        numpy_csv2 = np.swapaxes(numpy_csv,0,1)        
        print("shape",numpy_csv2.shape[0],numpy_csv2.shape[1])

        # have to save it to use it
        img = cv2.imwrite('tmp.png', numpy_csv2)
        img2 = cv2.imread('tmp.png')

        # https://stackoverflow.com/questions/48121916/numpy-resize-rescale-image
        img3 = cv2.resize(img2, dsize=(numpy_csv.shape[0]*scale_factor, numpy_csv.shape[1]*scale_factor), interpolation=cv2.INTER_AREA)
        cv2.imshow("image",img3)
        cv2.waitKey(0)
        cv2.imwrite(filename+"_c_sharp.png",img3)

        return img3


# piano above middle C
# keys must have the same length for round tripping
# does this work???
# test it
key = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84, 86, 88, 89, 91, 93, 95, 96]

# key 1
# c# minor c# D# E F# G# A B  C#
#key = [61, 63, 64, 66, 68, 69, 71, 73, 74, 76, 78, 81, 83, 85, 87, 88, 90, 92, 93, 95, 97]

raw_data = []
lines = []

filename = sys.argv[1]
print("filename",filename)

with open(filename) as file:
    lines = [line.rstrip() for line in file]

for l in lines:
    if(l!=""):
      raw_data.append(float(l))

k,c = get_factor_and_offset(key,sorted(raw_data))
notes = convert_raw_to_midi(key,raw_data,k,c)
print(notes)

# want it to be a nice square in the middle of (a4 is 842 * 595 at 72pdpi)
# so let's say 500 squareish
# padded by 47 and 48 in the height (need to calculate exacts)
# ~ 171 on the width each side

min_key = min(key)
max_key = max(key)

# ~30 x 36 array
# we build an array with padding of the pre-scaled value
# so 842/ say 15 to give us a central space of about 480 ~ 56
# similarly 595/15 = 40
# and then 56-32/2 = 12 padding on width
# and 40-36/2 = 2 padding on height

# not sure if this can be generalised more

scale_factor = 15 # hard coded via calcs above

# a4 at 72 dbp
w = 842
h = 595

# padding calculations for the central space
ww = (842/scale_factor)-len(notes)
hh = (595/scale_factor)-((max_key - min_key)+1)

print("w,h",w,h)
print("ww,hh",ww,hh)

padding_w = round(ww/2)
padding_h = round(hh/2)

print("padding_w",padding_w)
print("padding_h",padding_h)

zzz = np.ones((int(w/scale_factor),int(h/scale_factor)))

count = 0

print("notes",notes,len(notes))

for z_arr in zzz:
  #rd = raw_data[count] - min_key
  #print(rd)
  if(count < padding_w or count > 40+padding_w):
    pass
  else:
    if(count-padding_w < len(notes)-1):
      #print("count -n",count-padding_w)
      nc = notes[count-padding_w]
      #print("nc",nc)
      #print("nc",nc-min_key)
      # zeros are for a black square in the final thing 
      z_arr[nc-min_key+padding_h]=0
  count = count + 1  

#print(zzz)
generate_image(zzz,scale_factor)
