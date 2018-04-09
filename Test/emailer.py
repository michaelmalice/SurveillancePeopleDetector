import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import threading
import os
from datetime import datetime

class Emailer(threading.Thread):
 
    def __init__(self, directory, emailPassword):
        self.directory = directory
        threading.Thread.__init__(self)
        self.emailPassword = emailPassword
        
    # Send email
    def run(self):
        msg = MIMEMultipart()
        imageFiles = []
        for root, dirs, files in os.walk(self.directory):
            for file in files:
                if "png" in file:
                    imageFiles.append(os.path.join(self.directory, file))
        for file in imageFiles:
            fp = open(file, 'rb')
            img = MIMEImage(fp.read())
            fp.close()
            msg.attach(img)
        msg['Subject'] = 'Person Detected'
        msg['From'] = ''
        msg['To'] = ''
        msg.preamble = 'Person Detected'
        
        try:
            smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
            smtpObj.ehlo()
            smtpObj.starttls()
            smtpObj.login('', self.emailPassword)
            smtpObj.send_message(msg)
            smtpObj.quit()
        except SMTPDataError:
            print("Message not sent. Check Folder of images")
            
        print("Email sent at " + str(datetime.now()))
        
