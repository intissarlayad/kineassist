import cv2
import numpy as np
import mediapipe as mp

# Remplacement des imports problématiques par la syntaxe stable de MediaPipe
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class PoseDetector:
    LANDMARKS = {
        "left_shoulder": 11, "right_shoulder": 12,
        "left_elbow": 13, "right_elbow": 14,
        "left_wrist": 15, "right_wrist": 16,
        "left_hip": 23, "right_hip": 24,
        "left_knee": 25, "right_knee": 26,
        "left_ankle": 27, "right_ankle": 28,
    }

    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.pose = mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=1,
        )

    def process_frame(self, frame_bgr):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False
        results = self.pose.process(frame_rgb)
        frame_rgb.flags.writeable = True
        return results, frame_rgb

    def draw_landmarks(self, frame_rgb, results, joint_colors=None):
        if not results.pose_landmarks:
            return frame_rgb
        annotated = frame_rgb.copy()
        mp_drawing.draw_landmarks(
            annotated,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=2, circle_radius=3),
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(180, 180, 180), thickness=2),
        )
        if joint_colors:
            h, w, _ = annotated.shape
            for idx, color in joint_colors.items():
                lm = results.pose_landmarks.landmark[idx]
                cx, cy = int(lm.x * w), int(lm.y * h)
                cv2.circle(annotated, (cx, cy), 10, color, -1)
                cv2.circle(annotated, (cx, cy), 12, (255, 255, 255), 2)
        return annotated

    def get_raw_landmarks(self, results):
        if not results.pose_landmarks:
            return None
        return results.pose_landmarks.landmark

    def close(self):
        self.pose.close()