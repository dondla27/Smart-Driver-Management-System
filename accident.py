import cv2
import mediapipe as mp
from alarm import beep

# ----------------------------
# MediaPipe Face Mesh
# ----------------------------
mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ----------------------------
# Webcam
# ----------------------------
cap = cv2.VideoCapture(0)

while True:

    success, frame = cap.read()

    if not success:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        face = results.multi_face_landmarks[0]

        h, w, _ = frame.shape

        nose = face.landmark[1]

        nose_x = int(nose.x * w)
        nose_y = int(nose.y * h)

        cv2.circle(frame, (nose_x, nose_y), 5, (0, 255, 0), -1)

        # Accident condition (example)
        if nose_y > int(h * 0.75):

            cv2.putText(
                frame,
                "ACCIDENT DETECTED!",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            beep()

    cv2.imshow("Accident Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()