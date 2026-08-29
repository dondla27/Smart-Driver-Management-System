import cv2
import mediapipe as mp
import winsound



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
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while True:

    success, frame = cap.read()

    if not success:
        break

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_mesh.process(rgb)

    if results.multi_face_landmarks:

        face = results.multi_face_landmarks[0]

        h, w, _ = frame.shape

        # Nose landmark
        nose = face.landmark[1]

        nose_x = int(nose.x * w)

        # Draw nose point
        cv2.circle(frame, (nose_x, int(nose.y * h)), 5, (0, 255, 0), -1)

        # Determine head direction
        if nose_x < w // 3:

            text = "LOOKING LEFT"

            winsound.Beep(1000,300)
        elif nose_x > 2 * w // 3:

            text = "LOOKING RIGHT"
            winsound.Beep(1000,300)
        else:

            text = "LOOKING CENTER"
            
        cv2.putText(
            frame,
            text,
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    cv2.imshow("Head Pose Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()

cv2.destroyAllWindows()