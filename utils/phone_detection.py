import cv2
from ultralytics import YOLO
import pygame
import os

# Load YOLO model
model = YOLO("models/yolov8n.pt")

# Initialize pygame
pygame.mixer.init()

# Alarm file
alarm_path = "alarm/alarm.mp3"

if not os.path.exists(alarm_path):
    print("Alarm file not found:", alarm_path)
    exit()

alarm_playing = False

# Open webcam
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    phone_detected = False

    results = model(frame)

    for result in results:

        for box in result.boxes:

            cls = int(box.cls[0])
            confidence = float(box.conf[0])

            class_name = model.names[cls]

            # Print detected object
            print(class_name, confidence)

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(frame,
                        f"{class_name} {confidence:.2f}",
                        (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0,255,0),
                        2)

            # Detect mobile phone
            if class_name == "cell phone" and confidence > 0.40:

                phone_detected = True

    if phone_detected:

        cv2.putText(frame,
                    "PHONE DETECTED!",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,255),
                    3)

        if not alarm_playing:

            import winsound
            winsound.Beep(1000,500)
            alarm_playing = True

    else:

        if alarm_playing:

            pygame.mixer.music.stop()
            alarm_playing = False

    cv2.imshow("Phone Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

pygame.mixer.music.stop()
pygame.quit()