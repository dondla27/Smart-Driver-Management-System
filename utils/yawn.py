import cv2
import mediapipe as mp
import winsound
import math


# MediaPipe Face Mesh
# ---------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ---------------------------
# Webcam
# ---------------------------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# Mouth landmarks
UPPER_LIP = 13
LOWER_LIP = 14

# Threshold
YAWN_THRESHOLD = 0.05


def distance(p1, p2):
    return math.sqrt(
        (p1.x - p2.x) ** 2 +
        (p1.y - p2.y) ** 2
    )


while True:

    ret, frame = cap.read()

    if not ret:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        face = results.multi_face_landmarks[0]

        landmarks = face.landmark

        top = landmarks[UPPER_LIP]
        bottom = landmarks[LOWER_LIP]

        mouth_distance = distance(top, bottom)

        if mouth_distance > YAWN_THRESHOLD:

            cv2.putText(
                frame,
                "YAWN DETECTED",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            winsound.Beep(1000,300)
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(-1)
                winsound.Beep(1000,500)

        
    cv2.imshow("Yawn Detection", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()