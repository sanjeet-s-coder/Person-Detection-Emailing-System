import jetson.inference
import jetson.utils
from jetson_utils import videoSource, videoOutput
import smtplib
from email.message import EmailMessage
import time
import os

# Load the object detection network
net = jetson.inference.detectNet("ssd-mobilenet-v2", threshold=0.5)

# Use USB webcam (video0)
camera = jetson.utils.videoSource("/dev/video0")  # USB camera
display = jetson.utils.videoOutput("display://0")  # Optional display

# Set the cooldown period (in seconds)
email_cooldown = 10
last_email_time = 0

def send_email(image_path):
    msg = EmailMessage()
    msg.set_content("ALERT: A Intruder has been detected by the AI Security System. See the attached image for details.")
    msg["Subject"] = "Intruder Detected!"
    msg["From"] = "sanjeetsuthrave@gmail.com"
    msg["To"] = "sanjeetsuthrave@gmail.com"

    # Open the image file in binary mode and attach it to the email
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()
        msg.add_attachment(img_data, maintype="image", subtype="jpeg", filename=os.path.basename(image_path))
    
    # Connect to Gmail and send the message
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("sanjeetsuthrave@gmail.com", "myapppassword")
        smtp.send_message(msg)
        print("Email sent successfully with attached image.")

while display.IsStreaming():
    img = camera.Capture()

    if img is None:
        continue

    detections = net.Detect(img)
    display.Render(img)
    display.SetStatus("Object Detection | Network {:.0f} FPS".format(net.GetNetworkFPS()))

    current_time = time.time()
    for detection in detections:
        label = net.GetClassDesc(detection.ClassID)
        if label == "person":
            print("Person detected!")
            # Check if the cooldown period has passed
            if current_time - last_email_time >= email_cooldown:
                snapshot_path = "Screenshots/snapshot.jpg"
                jetson.utils.saveImage(snapshot_path, img)
                send_email(snapshot_path)
                last_email_time = current_time
    time.sleep(0.1)
