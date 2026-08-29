import cv2
import mediapipe as mp
from ultralytics import YOLO
import pygame
import mysql.connector
import math
import os
import time


# =========================================================
# 1. MEDIAPIPE FACE MESH
# =========================================================

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# =========================================================
# 2. YOLO MODEL
# =========================================================

model = YOLO("models/yolov8n.pt")


# =========================================================
# 3. ALARM
# =========================================================

pygame.mixer.init()

# IMPORTANT:
# monitor.py is in project root
# alarm.mp3 is inside alarm folder

alarm_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "alarm",
    "alarm.mp3"
)

print("Alarm file:", alarm_path)

alarm_playing = False


def play_alarm():

    global alarm_playing

    if not alarm_playing:

        if os.path.exists(alarm_path):

            try:
                pygame.mixer.music.load(alarm_path)
                pygame.mixer.music.play(-1)

                alarm_playing = True

                print("ALARM ON")

            except Exception as e:
                print("Alarm Error:", e)

        else:

            print("Alarm file NOT FOUND:")
            print(alarm_path)


def stop_alarm():

    global alarm_playing

    if alarm_playing:

        pygame.mixer.music.stop()

        alarm_playing = False

        print("ALARM OFF")


# =========================================================
# 4. MYSQL DATABASE
# =========================================================

try:

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="smart_driver_db"
    )

    cursor = db.cursor()

    print("MySQL connected successfully")

except Exception as e:

    print("MySQL connection error:")
    print(e)

    exit()


# =========================================================
# 5. CREATE COUNTER TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS monitoring_counts (

    id INT PRIMARY KEY,

    drowsiness_count INT DEFAULT 0,

    yawn_count INT DEFAULT 0,

    headpose_count INT DEFAULT 0,

    phone_count INT DEFAULT 0

)
""")

db.commit()


# =========================================================
# 6. CREATE FIRST ROW IF NOT EXISTS
# =========================================================

cursor.execute("""
SELECT id,
       drowsiness_count,
       yawn_count,
       headpose_count,
       phone_count
FROM monitoring_counts
WHERE id = 1
""")

data = cursor.fetchone()


if data is None:

    cursor.execute("""
    INSERT INTO monitoring_counts
    (id, drowsiness_count, yawn_count, headpose_count, phone_count)
    VALUES
    (1, 0, 0, 0, 0)
    """)

    db.commit()

    drowsiness_count = 0
    yawn_count = 0
    headpose_count = 0
    phone_count = 0

else:

    drowsiness_count = data[1]
    yawn_count = data[2]
    headpose_count = data[3]
    phone_count = data[4]


print()
print("================================")
print("PREVIOUS COUNTS")
print("Drowsiness :", drowsiness_count)
print("Yawn       :", yawn_count)
print("Head Pose  :", headpose_count)
print("Phone      :", phone_count)
print("================================")
print()


# =========================================================
# 7. UPDATE DATABASE
# =========================================================

def save_counts():

    cursor.execute("""
    UPDATE monitoring_counts
    SET
        drowsiness_count = %s,
        yawn_count = %s,
        headpose_count = %s,
        phone_count = %s
    WHERE id = 1
    """,
    (
        drowsiness_count,
        yawn_count,
        headpose_count,
        phone_count
    ))

    db.commit()


# =========================================================
# 8. WEBCAM
# =========================================================

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():

    print("Camera Error")

    db.close()

    exit()


# =========================================================
# 9. DISTANCE FUNCTION
# =========================================================

def distance(p1, p2):

    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


# =========================================================
# 10. EAR FUNCTION
# =========================================================

def EAR(landmarks, eye):

    vertical1 = distance(
        landmarks[eye[1]],
        landmarks[eye[5]]
    )

    vertical2 = distance(
        landmarks[eye[2]],
        landmarks[eye[4]]
    )

    horizontal = distance(
        landmarks[eye[0]],
        landmarks[eye[3]]
    )

    if horizontal == 0:

        return 0

    return (vertical1 + vertical2) / (2 * horizontal)


# =========================================================
# 11. EYE LANDMARKS
# =========================================================

LEFT_EYE = [
    33,
    160,
    158,
    133,
    153,
    144
]

RIGHT_EYE = [
    362,
    385,
    387,
    263,
    373,
    380
]


EAR_THRESHOLD = 0.23

closed_frames = 0

DROWSY_FRAME_LIMIT = 20


# =========================================================
# 12. YAWN
# =========================================================

UPPER_LIP = 13
LOWER_LIP = 14

YAWN_THRESHOLD = 0.025

yawn_frames = 0

YAWN_FRAME_LIMIT = 10


# =========================================================
# 13. EVENT STATES
# =========================================================

drowsiness_active = False

yawn_active = False

head_active = False

phone_active = False


# =========================================================
# 14. MAIN LOOP
# =========================================================

print("====================================")
print("SMART DRIVER MONITORING STARTED")
print("Press Q to stop")
print("====================================")


while True:

    ret, frame = cap.read()

    if not ret:

        print("Camera frame error")

        break


    h, w, _ = frame.shape


    # =====================================================
    # FACE DETECTION
    # =====================================================

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )

    results = face_mesh.process(rgb)


    drowsiness_detected = False

    yawn_detected = False

    head_detected = False

    phone_detected = False


    # =====================================================
    # FACE FEATURES
    # =====================================================

    if results.multi_face_landmarks:

        face = results.multi_face_landmarks[0]

        landmarks = face.landmark


        # =================================================
        # DROWSINESS
        # =================================================

        left_ear = EAR(
            landmarks,
            LEFT_EYE
        )

        right_ear = EAR(
            landmarks,
            RIGHT_EYE
        )

        avg_ear = (
            left_ear + right_ear
        ) / 2


        if avg_ear < EAR_THRESHOLD:

            closed_frames += 1

        else:

            closed_frames = 0


        if closed_frames >= DROWSY_FRAME_LIMIT:

            drowsiness_detected = True


        # =================================================
        # YAWN
        # =================================================

        upper = landmarks[UPPER_LIP]

        lower = landmarks[LOWER_LIP]


        mouth_open = distance(
            upper,
            lower
        )


        if mouth_open > YAWN_THRESHOLD:

            yawn_frames += 1

        else:

            yawn_frames = 0


        if yawn_frames >= YAWN_FRAME_LIMIT:

            yawn_detected = True


        # =================================================
        # HEAD POSE
        # =================================================

        nose = landmarks[1]

        nose_x = int(nose.x * w)


        if nose_x < w / 3:

            head_detected = True

            head_text = "LOOKING LEFT"

        elif nose_x > (2 * w / 3):

            head_detected = True

            head_text = "LOOKING RIGHT"

        else:

            head_text = "LOOKING CENTER"


        # =================================================
        # DISPLAY FACE INFORMATION
        # =================================================

        cv2.putText(
            frame,
            f"EAR: {avg_ear:.2f}",
            (20, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        cv2.putText(
            frame,
            head_text,
            (20, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )


    # =====================================================
    # YOLO PHONE DETECTION
    # =====================================================

    try:

        yolo_results = model(
            frame,
            verbose=False
        )

        for result in yolo_results:

            for box in result.boxes:

                class_id = int(
                    box.cls[0]
                )

                confidence = float(
                    box.conf[0]
                )

                # COCO class 67 = cell phone

                if class_id == 67 and confidence > 0.45:

                    phone_detected = True

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 0, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "PHONE",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 0, 255),
                        2
                    )


    except Exception as e:

        print("YOLO Error:", e)


    # =====================================================
    # COUNT DROWSINESS ONLY ONCE PER EPISODE
    # =====================================================

    if drowsiness_detected:

        if not drowsiness_active:

            drowsiness_count += 1

            drowsiness_active = True

            save_counts()

            print(
                "DROWSINESS COUNT =",
                drowsiness_count
            )

    else:

        drowsiness_active = False


    # =====================================================
    # COUNT YAWN ONLY ONCE PER EPISODE
    # =====================================================

    if yawn_detected:

        if not yawn_active:

            yawn_count += 1

            yawn_active = True

            save_counts()

            print(
                "YAWN COUNT =",
                yawn_count
            )

    else:

        yawn_active = False


    # =====================================================
    # COUNT HEAD POSE ONLY ONCE PER EPISODE
    # =====================================================

    if head_detected:

        if not head_active:

            headpose_count += 1

            head_active = True

            save_counts()

            print(
                "HEAD POSE COUNT =",
                headpose_count
            )

    else:

        head_active = False


    # =====================================================
    # COUNT PHONE ONLY ONCE PER EPISODE
    # =====================================================

    if phone_detected:

        if not phone_active:

            phone_count += 1

            phone_active = True

            save_counts()

            print(
                "PHONE COUNT =",
                phone_count
            )

    else:

        phone_active = False


    # =====================================================
    # DISPLAY ALERTS
    # =====================================================

    y_position = 40


    if drowsiness_detected:

        cv2.putText(
            frame,
            "DROWSINESS DETECTED!",
            (20, y_position),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            3
        )

        y_position += 40


    if yawn_detected:

        cv2.putText(
            frame,
            "YAWN DETECTED!",
            (20, y_position),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 255, 255),
            3
        )

        y_position += 40


    if head_detected:

        cv2.putText(
            frame,
            "HEAD POSE ALERT!",
            (20, y_position),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 0, 255),
            3
        )

        y_position += 40


    if phone_detected:

        cv2.putText(
            frame,
            "PHONE USAGE DETECTED!",
            (20, y_position),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            3
        )


    # =====================================================
    # ALARM
    # =====================================================

    if (
        drowsiness_detected
        or
        yawn_detected
        or
        head_detected
        or
        phone_detected
    ):

        play_alarm()

    else:

        stop_alarm()


    # =====================================================
    # DISPLAY COUNTERS
    # =====================================================

    cv2.putText(
        frame,
        f"Drowsiness: {drowsiness_count}",
        (20, h - 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Yawn: {yawn_count}",
        (20, h - 90),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Head Pose: {headpose_count}",
        (20, h - 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    cv2.putText(
        frame,
        f"Phone: {phone_count}",
        (20, h - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (255, 255, 255),
        2
    )


    # =====================================================
    # SHOW CAMERA
    # =====================================================

    cv2.imshow(
        "Smart Driver Management System",
        frame
    )


    # =====================================================
    # QUIT
    # =====================================================

    if cv2.waitKey(1) & 0xFF == ord("q"):

        break


# =========================================================
# CLEANUP
# =========================================================

stop_alarm()

cap.release()

cv2.destroyAllWindows()

pygame.quit()

save_counts()

cursor.close()

db.close()

print()
print("================================")
print("MONITORING STOPPED")
print("FINAL COUNTS")
print("Drowsiness :", drowsiness_count)
print("Yawn       :", yawn_count)
print("Head Pose  :", headpose_count)
print("Phone      :", phone_count)
print("================================")