import threading
import time
import numpy as np
import cv2
from flask import Flask, render_template, Response

exitFlag = 0
app = Flask(__name__)

class myThread (threading.Thread):
    def __init__(self, camIndex):
        threading.Thread.__init__(self)
        self.camIndex = camIndex
        self.cap = cv2.VideoCapture(self.camIndex)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
    def run(self):
        print ("Warming up Camera")
        time.sleep(2)

        while(True):
            # Capture frame-by-frame
            self.ret, self.frame = self.cap.read()

            # Our operations on the frame come here
            #gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

            # Display the resulting frame
            #cv2.imshow('frame', self.frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # When everything done, release the capture
                self.cap.release()
                cv2.destroyAllWindows()
                break
        
        
    def get_frame(self):
        self.frames = open("stream.jpg", 'wb+')
        #s, img = self.cap.read()
        if self.ret:
            cv2.imwrite("stream.jpg", self.frame)
            return self.frames.read()

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html')

def gen():
    """Video streaming generator function."""
    while True:
        frame = thread1.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(frame) + b'\r\n')
        
@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    # create new threads
    thread1 = myThread(0)
    # start new threads

    thread1.start()
    #thread1.join()
    time.sleep(5)
    app.run(host='0.0.0.0', debug=False, threaded=True)
    print("Exiting Main Thread")
        




