import mediapipe as mp

print("MediaPipe:", mp)
print("Location:", mp.__file__)
print("Version:", mp.__version__)
print("Has solutions:", hasattr(mp, "solutions"))

print(mp.solutions.face_mesh)