#Author Michael Larsen
#Goal is to use Neural Networks to detect people in video surveillance and only send alerts when a person is detected.

#Next steps
#FlowPlayer plays last video
#Home Version, doesnt send emails, maybe with gps
#record when person detected until no longer detected



# Required imports
from mvnc import mvncapi as mvnc
import sys
import numpy as np
import cv2
import time
import csv
import os
import sys
from sys import argv
import threading
from webserver import WebServer
from emailer import Emailer
from datetime import datetime


#Name of the OpenCV window
windowName = "Video Surveillance"

# labels for objects. The class IDs returned are the indices into this list
labels = ('background',
          'aeroplane', 'bicycle', 'bird', 'boat',
          'bottle', 'bus', 'car', 'cat', 'chair',
          'cow', 'diningtable', 'dog', 'horse',
          'motorbike', 'person', 'pottedplant',
          'sheep', 'sofa', 'train', 'tvmonitor')
# the ssd mobilenet image width and height
NETWORK_IMAGE_WIDTH = 300
NETWORK_IMAGE_HEIGHT = 300

# the minimal score for a box to be shown
min_score_percent = 60


emailPassword = input("Please enter password for email server: ")



class VideoProcessing (threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.firstTime = True
        self.startTime = None
        self.capture = False
        self.frameCount = 0
        self.dirName = ''
        self.killSwitch = False
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = None
        

    def run(self):
        
        # configure the NCS
        mvnc.SetGlobalOption(mvnc.GlobalOption.LOG_LEVEL, 2)

        # Get a list of ALL the sticks that are plugged in
        devices = mvnc.EnumerateDevices()
        if len(devices) == 0:
            print('No devices found')
            quit()

        # Pick the first stick to run the network
        device = mvnc.Device(devices[0])

        # Open the NCS
        device.OpenDevice()

        graph_filename = 'graph'

        # Load graph file to memory buffer
        with open(graph_filename, mode='rb') as f:
            graph_data = f.read()

        # allocate the Graph instance from NCAPI by passing the memory buffer
        ssd_mobilenet_graph = device.AllocateGraph(graph_data)
        
        # Create Video Capture object
        cap = cv2.VideoCapture(0)
        time.sleep(1)
        
        if ((cap == None or (not cap.isOpened()))):
            print ('Could not open video device.  Make sure file exists:')
            #print ('file name:' + input_video_file)
            print ('Also, if you installed python opencv via pip or pip3 you')
            print ('need to uninstall it and install from source with -D WITH_V4L=ON')
            print ('Use the provided script: install-opencv-from_source.sh')
            exit_app = True
            return
        while (not self.killSwitch):
            self.ret, self.display_image = cap.read()
            
            if (not self.ret):
                print("No image from the video device, exiting")
                break
            
            
            self.inferred_image = self.run_inference(self.display_image, ssd_mobilenet_graph)
            
            
            
        # Clean up the graph and the device
        print("quitting")
        ssd_mobilenet_graph.DeallocateGraph()
        device.CloseDevice()
        cap.release()
        
    def get_frame(self):
        self.frames = open("stream.jpg", 'wb+')
        #s, img = self.cap.read()
        if self.ret:
            cv2.imwrite("stream.jpg", self.inferred_image)
            return self.frames.read()    
    
    # create a preprocessed image from the source image that complies to the
    # network expectations and return it
    def preprocess_image(self, source_image):
        resized_image = cv2.resize(source_image, (NETWORK_IMAGE_WIDTH, NETWORK_IMAGE_HEIGHT))
    
        # trasnform values from range 0-255 to range -1.0 - 1.0
        resized_image = resized_image - 127.5
        resized_image = resized_image * 0.007843
        return resized_image
    
    # overlays the boxes and labels onto the display image.
    # display_image is the image on which to overlay the boxes/labels
    # object_info is a list of 7 values as returned from the network
    #     These 7 values describe the object found and they are:
    #         0: image_id (always 0 for myriad)
    #         1: class_id (this is an index into labels)
    #         2: score (this is the probability for the class)
    #         3: box left location within image as number between 0.0 and 1.0
    #         4: box top location within image as number between 0.0 and 1.0
    #         5: box right location within image as number between 0.0 and 1.0
    #         6: box bottom location within image as number between 0.0 and 1.0
    # returns None
    def overlay_on_image(self, display_image, object_info):
        
        
        
        source_image_width = display_image.shape[1]
        source_image_height = display_image.shape[0]

        base_index = 0
        class_id = object_info[base_index + 1]
        percentage = int(object_info[base_index + 2] * 100)
        if (percentage <= min_score_percent or labels[int(class_id)] is not 'person'):
            return False
        label_text = labels[int(class_id)] + " (" + str(percentage) + "%)"
        box_left = int(object_info[base_index + 3] * source_image_width)
        box_top = int(object_info[base_index + 4] * source_image_height)
        box_right = int(object_info[base_index + 5] * source_image_width)
        box_bottom = int(object_info[base_index + 6] * source_image_height)

        box_color = (255, 128, 0)  # box color
        box_thickness = 2
        cv2.rectangle(display_image, (box_left, box_top), (box_right, box_bottom), box_color, box_thickness)

        scale_max = (100.0 - min_score_percent)
        scaled_prob = (percentage - min_score_percent)
        scale = scaled_prob / scale_max

        # draw the classification label string just above and to the left of the rectangle
        #label_background_color = (70, 120, 70)  # greyish green background for text
        label_background_color = (0, int(scale * 175), 75)
        label_text_color = (255, 255, 255)  # white text

        label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        label_left = box_left
        label_top = box_top - label_size[1]
        if (label_top < 1):
            label_top = 1
        label_right = label_left + label_size[0]
        label_bottom = label_top + label_size[1]
        cv2.rectangle(display_image, (label_left - 1, label_top - 1), (label_right + 1, label_bottom + 1),
                      label_background_color, -1)

        # label text above the box
        cv2.putText(display_image, label_text, (label_left, label_bottom), cv2.FONT_HERSHEY_SIMPLEX, 0.5, label_text_color, 1)

        # display text to let user know how to quit
        cv2.rectangle(display_image,(0, 0),(100, 15), (128, 128, 128), -1)
        cv2.putText(display_image, "Q to Quit", (10, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

        return True
    # Run an inference on the passed image
    # image_to_classify is the image on which an inference will be performed
    #    upon successful return this image will be overlayed with boxes
    #    and labels identifying the found objects within the image.
    # ssd_mobilenet_graph is the Graph object from the NCAPI which will
    #    be used to peform the inference.
    def run_inference(self, image_to_classify, ssd_mobilenet_graph):
        
        # preprocess the image to meet nework expectations
        resized_image = self.preprocess_image(image_to_classify)

        # Send the image to the NCS as 16 bit floats
        ssd_mobilenet_graph.LoadTensor(resized_image.astype(np.float16), None)

        # Get the result from the NCS
        output, userobj = ssd_mobilenet_graph.GetResult()

        #   a.	First fp16 value holds the number of valid detections = num_valid.
        #   b.	The next 6 values are unused.
        #   c.	The next (7 * num_valid) values contain the valid detections data
        #       Each group of 7 values will describe an object/box These 7 values in order.
        #       The values are:
        #         0: image_id (always 0)
        #         1: class_id (this is an index into labels)
        #         2: score (this is the probability for the class)
        #         3: box left location within image as number between 0.0 and 1.0
        #         4: box top location within image as number between 0.0 and 1.0
        #         5: box right location within image as number between 0.0 and 1.0
        #         6: box bottom location within image as number between 0.0 and 1.0

        # number of boxes returned
        num_valid_boxes = int(output[0])

        for box_index in range(num_valid_boxes):
                base_index = 7+ box_index * 7
                if (not np.isfinite(output[base_index]) or
                        not np.isfinite(output[base_index + 1]) or
                        not np.isfinite(output[base_index + 2]) or
                        not np.isfinite(output[base_index + 3]) or
                        not np.isfinite(output[base_index + 4]) or
                        not np.isfinite(output[base_index + 5]) or
                        not np.isfinite(output[base_index + 6])):
                    # boxes with non finite (inf, nan, etc) numbers must be ignored
                    continue

                x1 = max(int(output[base_index + 3] * image_to_classify.shape[0]), 0)
                y1 = max(int(output[base_index + 4] * image_to_classify.shape[1]), 0)
                x2 = min(int(output[base_index + 5] * image_to_classify.shape[0]), image_to_classify.shape[0]-1)
                y2 = min((output[base_index + 6] * image_to_classify.shape[1]), image_to_classify.shape[1]-1)

                # overlay boxes and labels on to the image
                overlaid = self.overlay_on_image(image_to_classify, output[base_index:base_index + 7])
                if overlaid == True:
                    if (self.firstTime or (datetime.now() - self.startTime).total_seconds() >= 60):
                        self.firstTime = False
                        self.startTime = datetime.now()
                        self.capture = True
                        self.frameCount = 0
                        
                if (self.capture == True and self.frameCount % 5 == 0 and self.frameCount <= 75):
                    if self.frameCount == 0:
                        self.dirName = str(datetime.now())
                        os.makedirs(self.dirName)
                        print("dir created")
                    cv2.imwrite(os.path.join(self.dirName, str(datetime.now())) + ".png", image_to_classify)
                    if self.frameCount == 75:
                        print(str((datetime.now() - self.startTime).total_seconds()) + " seconds of footage")
                        print('got to 25')
                        emailMessage = Emailer(self.dirName, emailPassword)
                        emailMessage.start()
                        self.capture = False
                        self.dirName = ''
                
                if (self.capture == True and self.frameCount <= 75):
                    if self.frameCount == 0:
                        self.out = cv2.VideoWriter(os.path.join(self.dirName, str(datetime.now())) + ".avi", self.fourcc, 7.0, (640,480), True)
                    self.out.write(image_to_classify)
                    if self.frameCount == 75:
                        self.out.release()
                
                self.frameCount += 1
                #if (overlaid == False and self.capture == True):
                    #print("early stop")
                    #self.sendEmailMessage(self.dirName)
                    #self.capture = False
                    #self.dirName = ''

        return image_to_classify
    

if __name__ == '__main__':
    
    videoThread = VideoProcessing()
    
    serverThread = WebServer(videoThread)
    
    videoThread.start()
    serverThread.start()
    time.sleep(10)
    while True:
        choice = input("Please enter q to quit" + '\n')
        if choice == 'q':
            videoThread.killSwitch = True
            break
    #answer = input("Please enter 'v' to stop video thread, enter 's' to stop server thread. Enter q to quit")
    #if (answer == 'v'):
        #videoThread.