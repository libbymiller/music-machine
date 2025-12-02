/*
 *  Copyright (c) 2015 The WebRTC project authors. All Rights Reserved.
 *
 *  Use of this source code is governed by a BSD-style license
 *  that can be found in the LICENSE file in the root of the source
 *  tree.
 */

//now with basic synth, sorting and opencv and notes playing
//adding speed and multiple synths

import sbd from "./SimpleBlobDetector.js";

//'use strict';

// Put variables in global scope to make them available to the browser console.
const constraints = window.constraints = {
  audio: false,
  video: true
};

const video = document.querySelector('video');
const canvas = document.querySelector('canvas');
 const ctx = canvas.getContext('2d');

const colorNameDiv = document.getElementById('color-name');

const beepyPolySynth = new Tone.PolySynth({}).toDestination();

let crunchy = {
        "volume": 0,
        "detune": 0,
        "portamento": 0,
        "envelope": {
                "attack": 0.001,
                "attackCurve": "linear",
                "decay": 0.5,
                "decayCurve": "exponential",
                "release": 5,
                "releaseCurve": "exponential",
                "sustain": 0.5
        },
        "oscillator": {
                "partialCount": 10,
                "partials": [
                        0.8105694691387023,
                        0,
                        -0.0900632743487447,
                        0,
                        0.03242277876554809,
                        0,
                        -0.016542234064055146,
                        0,
                        0.010007030483193857,
                        0
                ],
                "phase": 0,
                "type": "sawtooth"
        }
};

let crunchyPolySynth = new Tone.PolySynth({polyphony: 32},crunchy).toDestination();

//C above middle C
//c# minor c# D# E F# G# A B  C#
const keys = [
[60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79, 81, 83, 84, 86, 88, 89, 91, 93, 95, 96],
[61, 63, 64, 66, 68, 69, 71, 73, 74, 76, 78, 81, 83, 85, 87, 88, 90, 92, 93, 95, 97]
];

const speeds = [100, 500];
const synths = [beepyPolySynth, crunchyPolySynth];

let speed = speeds[0];
let synth = synths[0];
let key = keys[0];
console.log("key is ",key)

function handleSuccess(stream) {
  const videoTracks = stream.getVideoTracks();
  console.log('Got stream with constraints:', constraints);
  console.log(`Using video device: ${videoTracks[0].label}`);
  window.stream = stream; // make variable available to browser console
  video.srcObject = stream;

  detectColor();
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function blobDetect(imgData, colours,ignore_x){
     //choose some aspects

     if(colours.includes("RED")){
        key = keys[1];
        document.querySelector('#key').textContent="RED, key is C#";
     }else{
        key = keys[0];
        document.querySelector('#key').textContent="NO RED, key is C";
     }
     if(colours.includes("GREEN")){
        speed = speeds[1];
        document.querySelector('#speed').textContent="GREEN, speed is "+speed;
     }else{
        speed = speeds[0];
        document.querySelector('#speed').textContent="NO GREEN, speed is "+speed;
     }
     if(colours.includes("YELLOW")){
        synth = synths[1];
        document.querySelector('#synth').textContent="YELLOW, synth is crunchy";
     }else{
        synth = synths[0];
        document.querySelector('#synth').textContent="NO YELLOW, synth is beepy";
     }


     let kp = sbd(imgData,{"faster":true,"filterByInertia":false})
     console.log("keypoints",kp);
     ctx.strokeStyle = "red";

     let entries = Object.entries(kp);

     //works though gives it a strange index of a string based on the prev numeric index I think
     let sorted_x = entries.sort((a, b) => a[1].pt.x - b[1].pt.x);

     console.log("sorted_x",sorted_x);
     //for the music we need the y values only
     let list_of_y = [];
     for(let x in sorted_x){
        let pt = sorted_x[x][1];
        console.log("pt.x, ignore_x",pt.x,ignore_x);
        if(pt.pt.x<ignore_x){ // ignore control blocks
          list_of_y.push(Math.round(pt.pt.y));
        }
     }
     console.log("list_of_y",list_of_y);
     let f_o_array = get_factor_and_offset(key,list_of_y);
     console.log("f_o_array",f_o_array);
     let zz = convert_raw_to_midi(key,list_of_y,f_o_array[0],f_o_array[1]);
     console.log("zz",zz);
     let count = 0;
     for(let x in sorted_x){
       let y_midi = zz[count];
       if(y_midi){
        //draw a square
        let pt = sorted_x[x][1];
        //console.log("pt",pt);
        let x_r = Math.round(pt.pt.x)-(pt.size/2);
        let y_r = Math.round(pt.pt.y)-(pt.size/2);
        ctx.strokeRect(x_r,y_r,pt.size,pt.size);
        await sleep(speed);

        //play a note 
        synth.triggerAttackRelease(Tone.Midi(y_midi).toNote(), "16n");
       }
       count++;
     }

     setTimeout(detectColorInner, 5000);
}



function handleError(error) {
  if (error.name === 'OverconstrainedError') {
    errorMsg(`OverconstrainedError: The constraints could not be satisfied by the available devices. Constraints: ${JSON.stringify(constraints)}`);
  } else if (error.name === 'NotAllowedError') {
    errorMsg('NotAllowedError: Permissions have not been granted to use your camera and ' +
      'microphone, you need to allow the page access to your devices in ' +
      'order for the demo to work.');
  }
  errorMsg(`getUserMedia error: ${error.name}`, error);
}

function errorMsg(msg, error) {
  const errorElement = document.querySelector('#errorMsg');
  errorElement.innerHTML += `<p>${msg}</p>`;
  if (typeof error !== 'undefined') {
    console.error(error);
  }
}

async function init(e) {
  console.log("init");
  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    handleSuccess(stream);
  } catch (e) {
    handleError(e);
  }
}

function rgbToHsv(r, g, b) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h, s, v = max;

  const d = max - min;
  s = max === 0 ? 0 : d / max;

  if (max === min) h = 0;
  else {
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }

  return [Math.round(h * 179), Math.round(s * 255), Math.round(v * 255)];
}

function getColorName(h, s, v) {
  if (v < 30) return "BLACK";
  else if (s < 25) return v > 200 ? "WHITE" : "GRAY";
  else if (h < 5 || h >= 170) return "RED";
  else if (h < 22) return "ORANGE";
  else if (h < 33) return "YELLOW";
  else if (h < 45) return "LIGHT GREEN";
  else if (h < 78) return "GREEN";
  else if (h < 95) return "CYAN";
  else if (h < 110) return "LIGHT BLUE";
  else if (h < 131) return "BLUE";
  else if (h < 145) return "PURPLE";
  else if (h < 170) return "PINK";
  return "UNKNOWN";
}



function detectColor() {

  console.log("detecting colour");

  video.addEventListener("play", async function() {

     await sleep(1000);//
     detectColorInner();

  },false);

}

function detectColorInner(){

     ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
     ctx.strokeStyle = "blue";
//a rough square in the middle
//i.e. w-h
     let sq_x = (canvas.width - canvas.height);
     ctx.strokeRect(0,0,canvas.width-sq_x,canvas.width);
     //ctx.strokeRect(0,0,10,10);

     console.log("2w,h",canvas.width,canvas.height)

     let imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);

     console.log("imgData",imgData);
     //bodge job - every 60 pixels take a sample
     let exclude_colours = ["WHITE","GRAY"];
     let colours_found = [];

     for(let x=0; x<canvas.width; x=x+60){
       for(let y=0; y<canvas.height; y=y+60){
         //console.log("x,y",x,y);
         const pixel = ctx.getImageData(x, y, 1, 1).data;
         const [r, g, b] = pixel;

         const [h, s, v] = rgbToHsv(r, g, b);
         const colorName = getColorName(h, s, v);
         if(!exclude_colours.includes(colorName)){
            console.log("colorName",colorName);
            if(!colours_found.includes(colorName)){
              colours_found.push(colorName);
            }
         }
       }
     }
     console.log("colours_found",colours_found);
     //pass control to blob detect
     let ignore_x = (canvas.width-sq_x);
     console.log("ignore_x is",canvas.width-sq_x);
     blobDetect(imgData, colours_found,ignore_x);
}

//music stuff
//k,c = get_factor_and_offset(key,patients_recruited)

function arrayMax(array) {
  return array.reduce((a, b) => Math.max(a, b));
}

function arrayMin(array) {
  return array.reduce((a, b) => Math.min(a, b));
}

function get_factor_and_offset(key,raw){
console.log("key,raw",key,raw);

    let diff_key = arrayMax(key) - arrayMin(key);
    let diff_raw = arrayMax(raw) - arrayMin(raw);
    console.log("diff_key",diff_key);
    console.log("diff_raw",diff_raw);
    let k = diff_key/diff_raw;//don't want zero here.hm
    console.log("k",k);

    let c = arrayMax(key) - k * arrayMax(raw);

    console.log("k",k);
    console.log("c",c);
    return [k,c];
}

function convert_raw_to_midi(key,raw,factor,offset){

    let to_return = [];

    for (let r in raw){
      //console.log("r,raw[r],factor,offset",r,raw[r],factor,offset);
      let scaled_raw = raw[r]*factor + offset;
      //console.log("scaled_raw",scaled_raw);
      let result = find_closest_value(key,scaled_raw);
      to_return.push(result);
    }
    //console.log("to_return",to_return);
    return to_return;
}

function find_closest_value(arr,num){
                var curr = arr[0];
                var diff = Math.abs (num - curr);
                for (var val = 0; val < arr.length; val++) {
                    var newdiff = Math.abs (num - arr[val]);
                    if (newdiff < diff) {
                        diff = newdiff;
                        curr = arr[val];
                    }
                }
                return curr;
}

init();

