I used bookworm on a Pi 4 for this.

To run chrome:

/usr/bin/chromium --headless=new --disable-gpu --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222 --kiosk --auto-accept-camera-and-microphone-capture --enable-logging --vmodule=*/webrtc/*=1 http://localhost:8000/test4.html

(not all of those flags are needed or doing things)

You'll need to allow camera using a screen for the first time - the windowing system intercepts the request from the browser.

To debug headlessly, go to chrome://inspect#devices on laptop

you'll need to run a ssh tunnel too - from laptop

ssh -L 9222:localhost:9222 pi@192.168.1.13

(i.e. 192.168.1.13 is the IP address of the pi)

and 
cd server
python -m http.server 8000




