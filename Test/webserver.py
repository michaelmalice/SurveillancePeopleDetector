import time
import threading
from flask import Flask, render_template, Response


app = Flask(__name__)


class WebServer(threading.Thread):

    videoThreader = None

    def __init__(self, videoThread):
        threading.Thread.__init__(self)
        global videoThreader
        videoThreader = videoThread
        
    def run(self):
        time.sleep(5)
        app.run(host='0.0.0.0', debug=False, threaded=True)
        
        
    @app.route('/')
    def index():
        """Video streaming home page."""
        return render_template('index.html')

    def gen(threader):
        """Video streaming generator function."""
        while True:
            frame = threader.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + bytearray(frame) + b'\r\n')
        
    @app.route('/video_feed')
    def video_feed():
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(WebServer.gen(videoThreader),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    
