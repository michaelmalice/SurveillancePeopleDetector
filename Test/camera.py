import cv2
import time

class Camera():
    # Constructor
    def __init__(self):
        width = 640
        height = 480
        fps = 20
        resolution = (width, height)
        
        self.cap = cv2.VideoCapture(0)
        # set correct resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("Camera warming up")
        time.sleep(3)
        
        # ret is return value, true if succesful, frame is the frame captured
        self.ret, self.frame = self.cap.read()
        if self.ret:
        
            
            # Prepare output window
            self.winName = "Surveillance Camera"
            cv2.namedWindow(self.winName, cv2.WINDOW_AUTOSIZE)
        
            # Read three images first
            self.prev_frame = cv2.cvtColor(self.cap.read()[1], cv2.COLOR_RGB2GRAY)
            self.current_frame = cv2.cvtColor(self.cap.read()[1], cv2.COLOR_RGB2GRAY)
            self.next_frame = cv2.cvtColor(self.cap.read()[1], cv2.COLOR_RGB2GRAY)
        
            # Define the codec and create VideoWriter object
            self.fourcc = cv2.VideoWriter_fourcc(*'H264')
            self.out = cv2.VideoWriter('output.avi', self.fourcc, fps, resolution, True)
        
        
    def get_frame(self):
        self.frames = open("stream.jpg", 'wb+')
        s, img = self.cap.read()
        if s:
            cv2.imwrite("stream.jpg", img)
            return self.frames.read()
        
    
    def diffImg(self, tprev, tc, tnex):
        Im1 = cv2.absdiff(tnex, tc)
        Im2 = cv2.absdiff(tc, tprev)
        return cv2.bitwise_and(Im1, Im2)
    
    def captureVideo(self):
        self.ret, self.frame = self.cap.read()
        diffe = self.diffImg(self.prev_frame, self.current_frame, self.next_frame)
        cv2.imshow(self.winName, diffe)
        
        # Put images in right order
        self.prev_frame = self.current_frame
        self.current_frame = self.next_frame
        self.next_frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2GRAY)
        
        
    def saveVideo(self):
        self.out.write(self.frame)
        return()
    
    def __del__(self):
        self.cap.release()
        cv2.destroyAllWindows
        self.out.release()
        print("camera has been disabled and all ouput windows closed")
        return()
    
def main():
    cam1 = Camera()
    
    while(True):
        cam1.captureVideo()
        cam1.saveVideo()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    return()


if __name__ == '__main__':
    main()