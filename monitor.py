import cv2
import mediapipe as mp
from ultralytics import YOLO
import pygame
import mysql.connector
import math
import os


# =========================================================
# MEDIAPIPE
# =========================================================

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# =========================================================
# YOLO
# =========================================================

model = YOLO("models/yolov8n.pt")


# =========================================================
# ALARM
# =========================================================

pygame.mixer.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

alarm_paths = [
    os.path.join(BASE_DIR, "alarm", "alarm.mp3"),
    os.path.join(BASE_DIR, "utils", "alarm", "alarm.mp3")
]

alarm_path = None

for path in alarm_paths:

    if os.path.exists(path):

        alarm_path = path
        break


print("================================")
print("ALARM CHECK")
print("================================")

if alarm_path:

    print("Alarm found:")
    print(alarm_path)

else:

    print("ERROR: alarm.mp3 NOT FOUND")

print("================================")


alarm_playing = False


def play_alarm():

    global alarm_playing

    if alarm_playing:
        return

    if alarm_path is None:

        print("Cannot play alarm - file not found")

        return

    try:

        pygame.mixer.music.load(alarm_path)

        pygame.mixer.music.play(-1)

        alarm_playing = True

        print("🔊 ALARM ON")

    except Exception as e:

        print("Alarm error:", e)


def stop_alarm():

    global alarm_playing

    if alarm_playing:

        pygame.mixer.music.stop()

        alarm_playing = False

        print("🔇 ALARM OFF")


# =========================================================
# MYSQL
# =========================================================

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="smart_driver_db"
)

cursor = db.cursor()


# =========================================================
# CREATE COUNTER TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS monitoring_counts
(
    id INT PRIMARY KEY,
    drowsiness_count INT DEFAULT 0,
    yawn_count INT DEFAULT 0,
    headpose_count INT DEFAULT 0,
    phone_count INT DEFAULT 0
)
""")

db.commit()


# =========================================================
# GET PREVIOUS COUNTS
# =========================================================

cursor.execute("""
SELECT
    drowsiness_count,
    yawn_count,
    headpose_count,
    phone_count
FROM monitoring_counts
WHERE id = 1
""")

row = cursor.fetchone()


if row:

    drowsiness_count = row[0]
    yawn_count = row[1]
    headpose_count = row[2]
    phone_count = row[3]

else:

    drowsiness_count = 0
    yawn_count = 0
    headpose_count = 0
    phone_count = 0

    cursor.execute("""
    INSERT INTO monitoring_counts
    VALUES (1,0,0,0,0)
    """)

    db.commit()


# =========================================================
# SAVE COUNTS
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
# DISTANCE
# =========================================================

def distance(p1, p2):

    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


# =========================================================
# EAR
# =========================================================

def calculate_ear(landmarks, eye):

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
# EYES
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


# IMPORTANT
# Increased from 0.23 to 0.26
# Easier to detect closed eyes

EAR_THRESHOLD = 0.26

closed_frames = 0

DROWSY_LIMIT = 15


# =========================================================
# YAWN
# =========================================================

UPPER_LIP = 13
LOWER_LIP = 14

YAWN_THRESHOLD = 0.035

yawn_frames = 0

YAWN_LIMIT = 10


# =========================================================
# EVENT STATES
# =========================================================

drowsiness_active = False
yawn_active = False
head_active = False
phone_active = False


# =========================================================
# CAMERA
# =========================================================

cap = cv2.VideoCapture(
    0,
    cv2.CAP_DSHOW
)


if not cap.isOpened():

    print("Camera could not be opened")

    exit()


print()
print("================================")
print("SMART DRIVER MONITORING STARTED")
print("================================")
print("Drowsiness :", drowsiness_count)
print("Yawn       :", yawn_count)
print("Head Pose  :", headpose_count)
print("Phone      :", phone_count)
print()
print("Press Q to exit")
print()


# =========================================================
# MAIN LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break


    h, w, _ = frame.shape


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
    # FACE
    # =====================================================

    if results.multi_face_landmarks:

        face = results.multi_face_landmarks[0]

        landmarks = face.landmark


        # =================================================
        # DROWSINESS
        # =================================================

        left_ear = calculate_ear(
            landmarks,
            LEFT_EYE
        )

        right_ear = calculate_ear(
            landmarks,
            RIGHT_EYE
        )

        avg_ear = (
            left_ear + right_ear
        ) / 2


        # SHOW EAR VALUE
        cv2.putText(
            frame,
            f"EAR: {avg_ear:.3f}",
            (20, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )


        if avg_ear < EAR_THRESHOLD:

            closed_frames += 1

        else:

            closed_frames = 0


        if closed_frames >= DROWSY_LIMIT:

            drowsiness_detected = True


        # =================================================
        # YAWN
        # =================================================

        mouth_distance = distance(
            landmarks[UPPER_LIP],
            landmarks[LOWER_LIP]
        )


        if mouth_distance > YAWN_THRESHOLD:

            yawn_frames += 1

        else:

            yawn_frames = 0


        if yawn_frames >= YAWN_LIMIT:

            yawn_detected = True


        # =================================================
        # HEAD POSE
        # =================================================

        nose = landmarks[1]

        nose_x = nose.x * w


        if nose_x < w / 3:

            head_detected = True

            head_text = "LOOKING LEFT"

        elif nose_x > (2 * w / 3):

            head_detected = True

            head_text = "LOOKING RIGHT"

        else:

            head_text = "LOOKING CENTER"


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
    # PHONE DETECTION
    # =====================================================

    try:

        yolo_results = model(
            frame,
            verbose=False
        )


        for result in yolo_results:

            for box in result.boxes:

                class_id = int(box.cls[0])

                confidence = float(box.conf[0])


                # COCO:
                # 67 = cell phone

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
                        "PHONE DETECTED",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

    except Exception as e:

        print("YOLO error:", e)


    # =====================================================
    # DROWSINESS COUNT
    # =====================================================

    if drowsiness_detected:

        if not drowsiness_active:

            drowsiness_count += 1

            drowsiness_active = True

            save_counts()

            print(
                "DROWSINESS COUNT:",
                drowsiness_count
            )

    else:

        drowsiness_active = False


    # =====================================================
    # YAWN COUNT
    # =====================================================

    if yawn_detected:

        if not yawn_active:

            yawn_count += 1

            yawn_active = True

            save_counts()

            print(
                "YAWN COUNT:",
                yawn_count
            )

    else:

        yawn_active = False


    # =====================================================
    # HEAD POSE COUNT
    # =====================================================

    if head_detected:

        if not head_active:

            headpose_count += 1

            head_active = True

            save_counts()

            print(
                "HEAD POSE COUNT:",
                headpose_count
            )

    else:

        head_active = False


    # =====================================================
    # PHONE COUNT
    # =====================================================

    if phone_detected:

        if not phone_active:

            phone_count += 1

            phone_active = True

            save_counts()

            print(
                "PHONE COUNT:",
                phone_count
            )

    else:

        phone_active = False


    # =====================================================
    # DISPLAY ALERTS
    # =====================================================

    alert = False


    if drowsiness_detected:

        alert = True

        cv2.putText(
            frame,
            "!!! DROWSINESS DETECTED !!!",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            3
        )


    if yawn_detected:

        alert = True

        cv2.putText(
            frame,
            "!!! YAWN DETECTED !!!",
            (20, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            3
        )


    if head_detected:

        alert = True

        cv2.putText(
            frame,
            "!!! HEAD POSE ALERT !!!",
            (20, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
            3
        )


    if phone_detected:

        alert = True

        cv2.putText(
            frame,
            "!!! PHONE USAGE !!!",
            (20, 145),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            3
        )


    # =====================================================
    # ALARM
    # =====================================================

    if alert:

        play_alarm()

    else:

        stop_alarm()


    # =====================================================
    # COUNTERS
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
    # CAMERA WINDOW
    # =====================================================

    cv2.imshow(
        "Smart Driver Management System",
        frame
    )


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