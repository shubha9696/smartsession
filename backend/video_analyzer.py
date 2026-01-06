import cv2
import numpy as np
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    
    def __init__(self):
        if not MEDIAPIPE_AVAILABLE:
            logger.warning("MediaPipe not available - face analysis disabled")
            self.face_mesh = None
            self.face_detection = None
        else:
            try:
                self.mp_face_mesh = mp.solutions.face_mesh
                self.face_mesh = self.mp_face_mesh.FaceMesh(
                    max_num_faces=2,
                    refine_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                
                self.mp_face_detection = mp.solutions.face_detection
                self.face_detection = self.mp_face_detection.FaceDetection(
                    min_detection_confidence=0.7
                )
            except Exception as e:
                logger.error(f"Failed to initialize MediaPipe: {e}")
                self.face_mesh = None
                self.face_detection = None
        
        self.student_states: Dict[str, Dict] = {}
        self.gaze_history: Dict[str, deque] = {}
        self.emotion_history: Dict[str, deque] = {}
        
        self.GAZE_AWAY_THRESHOLD = 4.0
        self.HISTORY_SIZE = 30
        self.CONFUSION_THRESHOLD = 0.6
        
        logger.info("VideoAnalyzer initialized successfully")
        
    def is_ready(self) -> bool:
        return self.face_mesh is not None and self.face_detection is not None
    
    def analyze_frame(self, frame: np.ndarray, student_id: str) -> Dict:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = frame.shape
        
        if student_id not in self.student_states:
            self._initialize_student_state(student_id)
        
        detection_results = self.face_detection.process(rgb_frame)
        face_count = len(detection_results.detections) if detection_results.detections else 0
        
        mesh_results = self.face_mesh.process(rgb_frame)
        
        analysis = {
            "face_count": face_count,
            "face_detected": face_count > 0,
            "multiple_faces": face_count > 1,
            "landmarks_detected": mesh_results.multi_face_landmarks is not None,
            "status": "unknown",
            "alert_type": None,
            "confidence": 0.0,
            "gaze_direction": "center",
            "emotion": "neutral",
            "confusion_score": 0.0,
            "engagement_level": "unknown"
        }
        
        if face_count == 0:
            analysis["status"] = "alert"
            analysis["alert_type"] = "no_face_detected"
            analysis["message"] = "No face detected in frame"
            self._update_student_state(student_id, analysis)
            return analysis
        
        if face_count > 1:
            analysis["status"] = "alert"
            analysis["alert_type"] = "multiple_faces"
            analysis["message"] = "Multiple faces detected"
            self._update_student_state(student_id, analysis)
            return analysis
        
        if mesh_results.multi_face_landmarks:
            landmarks = mesh_results.multi_face_landmarks[0].landmark
            
            gaze_info = self._analyze_gaze(landmarks, w, h)
            analysis["gaze_direction"] = gaze_info["direction"]
            analysis["gaze_away"] = gaze_info["away"]
            
            self._update_gaze_history(student_id, gaze_info["away"])
            gaze_away_duration = self._get_continuous_gaze_away_duration(student_id)
            
            if gaze_away_duration > self.GAZE_AWAY_THRESHOLD:
                analysis["status"] = "alert"
                analysis["alert_type"] = "gaze_away"
                analysis["message"] = f"Looking away for {gaze_away_duration:.1f}s"
                self._update_student_state(student_id, analysis)
                return analysis
            
            confusion_analysis = self._detect_confusion(landmarks, w, h)
            analysis["confusion_score"] = confusion_analysis["score"]
            analysis["confusion_indicators"] = confusion_analysis["indicators"]
            
            if confusion_analysis["score"] > self.CONFUSION_THRESHOLD:
                analysis["emotion"] = "confused"
                analysis["status"] = "warning"
                analysis["alert_type"] = "confused"
                analysis["message"] = "Student appears confused"
                analysis["engagement_level"] = "struggling"
            else:
                smile_score = self._detect_smile(landmarks, w, h)
                if smile_score > 0.6:
                    analysis["emotion"] = "happy"
                    analysis["status"] = "good"
                    analysis["engagement_level"] = "engaged"
                else:
                    analysis["emotion"] = "focused"
                    analysis["status"] = "good"
                    analysis["engagement_level"] = "focused"
            
            analysis["confidence"] = 0.85
            
        else:
            analysis["status"] = "warning"
            analysis["message"] = "Face detected but landmarks unclear"
            analysis["confidence"] = 0.3
        
        self._update_student_state(student_id, analysis)
        return analysis
    
    def _detect_confusion(self, landmarks, w: int, h: int) -> Dict:
        indicators = []
        scores = []
        
        left_brow_inner = landmarks[336]
        right_brow_inner = landmarks[107]
        left_brow_outer = landmarks[285]
        right_brow_outer = landmarks[55]
        left_brow_center = landmarks[300]
        right_brow_center = landmarks[70]
        
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]
        
        mouth_left = landmarks[61]
        mouth_right = landmarks[291]
        mouth_top = landmarks[13]
        mouth_bottom = landmarks[14]
        upper_lip = landmarks[0]
        lower_lip = landmarks[17]
        
        nose_tip = landmarks[1]
        nose_bridge = landmarks[168]
        
        left_face = landmarks[234]
        right_face = landmarks[454]
        
        brow_distance = abs(left_brow_inner.x - right_brow_inner.x) * w
        brow_height = ((left_brow_center.y + right_brow_center.y) / 2) * h
        eye_height = ((left_eye_top.y + right_eye_top.y) / 2) * h
        brow_to_eye = eye_height - brow_height
        
        if brow_distance < w * 0.12 and brow_to_eye < h * 0.03:
            indicators.append("brow_furrowing")
            scores.append(0.8)
        
        mouth_width = abs(mouth_left.x - mouth_right.x) * w
        mouth_height = abs(mouth_top.y - mouth_bottom.y) * h
        mouth_aspect_ratio = mouth_height / (mouth_width + 1e-6)
        
        if mouth_aspect_ratio < 0.25:
            indicators.append("no_smile")
            scores.append(0.5)
        
        face_tilt = abs(left_face.y - right_face.y) * h
        if face_tilt > h * 0.03:
            indicators.append("head_tilt")
            scores.append(0.6)
        
        left_eye_height = abs(left_eye_top.y - left_eye_bottom.y) * h
        right_eye_height = abs(right_eye_top.y - right_eye_bottom.y) * h
        avg_eye_height = (left_eye_height + right_eye_height) / 2
        
        if avg_eye_height < h * 0.015:
            indicators.append("eye_squinting")
            scores.append(0.7)
        
        lip_distance = abs(upper_lip.y - lower_lip.y) * h
        if lip_distance < h * 0.01 and mouth_aspect_ratio < 0.2:
            indicators.append("mouth_tension")
            scores.append(0.6)
        
        if len(scores) == 0:
            confusion_score = 0.0
        else:
            confusion_score = sum(scores) / len(scores)
            if len(indicators) >= 3:
                confusion_score = min(confusion_score * 1.2, 1.0)
        
        return {
            "score": confusion_score,
            "indicators": indicators
        }
    
    def _analyze_gaze(self, landmarks, w: int, h: int) -> Dict:
        left_iris = landmarks[468]
        right_iris = landmarks[473]
        
        left_eye_left = landmarks[33]
        left_eye_right = landmarks[133]
        right_eye_left = landmarks[362]
        right_eye_right = landmarks[263]
        
        left_ratio_x = (left_iris.x - left_eye_left.x) / (left_eye_right.x - left_eye_left.x + 1e-6)
        right_ratio_x = (right_iris.x - right_eye_left.x) / (right_eye_right.x - right_eye_left.x + 1e-6)
        
        avg_ratio_x = (left_ratio_x + right_ratio_x) / 2
        
        direction = "center"
        away = False
        
        if avg_ratio_x < 0.35:
            direction = "left"
            away = True
        elif avg_ratio_x > 0.65:
            direction = "right"
            away = True
        
        avg_iris_y = (left_iris.y + right_iris.y) / 2
        if avg_iris_y < 0.45:
            direction = "up"
            away = True
        elif avg_iris_y > 0.55:
            direction = "down"
            away = True
        
        return {
            "direction": direction,
            "away": away,
            "ratio_x": avg_ratio_x
        }
    
    def _detect_smile(self, landmarks, w: int, h: int) -> float:
        mouth_left = landmarks[61]
        mouth_right = landmarks[291]
        mouth_top = landmarks[13]
        mouth_bottom = landmarks[14]
        
        mouth_width = abs(mouth_left.x - mouth_right.x) * w
        mouth_height = abs(mouth_top.y - mouth_bottom.y) * h
        
        aspect_ratio = mouth_height / (mouth_width + 1e-6)
        
        # Higher ratio = more smile
        smile_score = min(aspect_ratio / 0.35, 1.0)
        return smile_score
    
    def _initialize_student_state(self, student_id: str):
        self.student_states[student_id] = {
            "last_update": datetime.now(),
            "status": "unknown",
            "gaze_away_start": None
        }
        self.gaze_history[student_id] = deque(maxlen=self.HISTORY_SIZE)
        self.emotion_history[student_id] = deque(maxlen=self.HISTORY_SIZE)
    
    def _update_student_state(self, student_id: str, analysis: Dict):
        self.student_states[student_id]["last_update"] = datetime.now()
        self.student_states[student_id]["latest_analysis"] = analysis
    
    def _update_gaze_history(self, student_id: str, gaze_away: bool):
        self.gaze_history[student_id].append({
            "away": gaze_away,
            "timestamp": datetime.now()
        })
    
    def _get_continuous_gaze_away_duration(self, student_id: str) -> float:
        history = self.gaze_history[student_id]
        if not history:
            return 0.0
        
        duration = 0.0
        for entry in reversed(history):
            if entry["away"]:
                if duration == 0:
                    duration = (datetime.now() - entry["timestamp"]).total_seconds()
                else:
                    duration = (datetime.now() - entry["timestamp"]).total_seconds()
            else:
                break
        
        return duration
    
    def get_all_students_state(self) -> Dict:
        states = {}
        for student_id, state in self.student_states.items():
            states[student_id] = {
                "student_id": student_id,
                "last_update": state["last_update"].isoformat(),
                "latest_analysis": state.get("latest_analysis", {})
            }
        return states
