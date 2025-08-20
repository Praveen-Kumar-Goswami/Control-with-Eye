import cv2
import mediapipe as mp
import numpy as np
import time
import tkinter as tk

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

# Webcam
cap = cv2.VideoCapture(0)

# Get screen size
root = tk.Tk()
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

calibration_data = []
calibration_points = [
    (100, 100),                        # Top-left
    (screen_w - 100, 100),             # Top-right
    (100, screen_h - 100),             # Bottom-left
    (screen_w - 100, screen_h - 100),  # Bottom-right
    (screen_w // 2, screen_h // 2)     # Center
]

def get_eye_position(landmarks, img_w, img_h):
    left_eye = landmarks[468]
    return (left_eye.x * img_w, left_eye.y * img_h)

# Create fullscreen calibration window
cv2.namedWindow("Calibration", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Calibration", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

for point in calibration_points:
    overlay = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)
    cv2.circle(overlay, point, 30, (0, 255, 0), -1)  # green dot
    cv2.imshow("Calibration", overlay)

    print(f"Look at the dot at {point}")
    cv2.waitKey(2000)  # show for 2 sec

    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    img_h, img_w, _ = frame.shape

    if results.multi_face_landmarks:
        mesh_points = results.multi_face_landmarks[0].landmark
        eye_pos = get_eye_position(mesh_points, img_w, img_h)
        calibration_data.append((eye_pos, point))

cv2.destroyWindow("Calibration")
print("Calibration completed ✅")

# Mapping using linear regression
eye_points = np.array([d[0] for d in calibration_data])
screen_points = np.array([d[1] for d in calibration_data])

A_x = np.vstack([eye_points[:, 0], np.ones(len(eye_points))]).T
m_x, c_x = np.linalg.lstsq(A_x, screen_points[:, 0], rcond=None)[0]

A_y = np.vstack([eye_points[:, 1], np.ones(len(eye_points))]).T
m_y, c_y = np.linalg.lstsq(A_y, screen_points[:, 1], rcond=None)[0]

print("Tracking started 🎯")

# Fullscreen overlay window for gaze tracking
cv2.namedWindow("Eye Tracking Overlay", cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty("Eye Tracking Overlay", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    img_h, img_w, _ = frame.shape

    overlay = np.zeros((screen_h, screen_w, 3), dtype=np.uint8)

    if results.multi_face_landmarks:
        mesh_points = results.multi_face_landmarks[0].landmark
        eye_pos = get_eye_position(mesh_points, img_w, img_h)

        # Apply mapping
        x = int(m_x * eye_pos[0] + c_x)
        y = int(m_y * eye_pos[1] + c_y)

        # Draw gaze dot
        cv2.circle(overlay, (x, y), 20, (0, 0, 255), -1)

    cv2.imshow("Eye Tracking Overlay", overlay)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
