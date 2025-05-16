import cv2

def get_camera_feed():
    cap = cv2.VideoCapture(1)  # AI camera as /dev/video0
    if not cap.isOpened():
        raise RuntimeError("Could not open camera.")
    return cap
