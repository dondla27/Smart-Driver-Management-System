import cv2
import mediapipe as mp
import math
import winsound

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Start Webcam
cap = cv2.VideoCapture(0)

closed_frames = 0

# Distance Function
def distance(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

# Eye Aspect Ratio (EAR)
def eye_aspect_ratio(landmarks, eye):
    vertical1 = distance(landmarks[eye[1]], landmarks[eye[5]])
    vertical2 = distance(landmarks[eye[2]], landmarks[eye[4]])
    horizontal = distance(landmarks[eye[0]], landmarks[eye[3]])

    ear = (vertical1 + vertical2) / (2.0 * horizontal)
    return ear

# MediaPipe Eye Landmarks
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

while True:
    success, frame = cap.read()

    if not success:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        for face_landmarks in results.multi_face_landmarks:

            landmarks = face_landmarks.landmark

            leftEAR = eye_aspect_ratio(landmarks, LEFT_EYE)
            rightEAR = eye_aspect_ratio(landmarks, RIGHT_EYE)

            ear = (leftEAR + rightEAR) / 2

            cv2.putText(frame, f"EAR: {ear:.2f}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Drowsiness Detection
            if ear < 0.22:
                closed_frames += 1
            else:
                closed_frames = 0

            if closed_frames > 15:
                cv2.putText(frame, "DROWSINESS ALERT!", (50, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 3)

                # Windows Beep Alarm
                winsound.Beep(2500, 500)

    cv2.imshow("Smart Driver Drowsiness Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()