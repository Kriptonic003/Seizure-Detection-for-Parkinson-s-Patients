import cv2
import mediapipe as mp
import numpy as np
import logging
from typing import Optional, Dict, List, Tuple

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        """Initialize video processing with MediaPipe pose detection"""
        try:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            # Initialize MediaPipe Pose with robust settings
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                enable_segmentation=False,
                smooth_segmentation=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            # Keypoint mapping for easier access
            self.keypoint_names = {
                'nose': 0,
                'left_eye': 2,
                'right_eye': 5,
                'left_ear': 7,
                'right_ear': 8,
                'left_shoulder': 11,
                'right_shoulder': 12,
                'left_elbow': 13,
                'right_elbow': 14,
                'left_wrist': 15,
                'right_wrist': 16,
                'left_hip': 23,
                'right_hip': 24,
                'left_knee': 25,
                'right_knee': 26,
                'left_ankle': 27,
                'right_ankle': 28
            }
            
            logger.info("VideoProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VideoProcessor: {e}")
            raise
    
    def extract_keypoints(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Extract body keypoints from a video frame using MediaPipe
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            Dictionary containing keypoints data or None if no pose detected
        """
        try:
            if frame is None:
                logger.warning("Received None frame")
                return None
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks is None:
                return None
            
            # Extract keypoints
            keypoints = self._extract_landmarks(results.pose_landmarks, frame.shape)
            
            return {
                'keypoints': keypoints,
                'landmarks': results.pose_landmarks,
                'frame_shape': frame.shape
            }
            
        except Exception as e:
            logger.error(f"Error extracting keypoints: {e}")
            return None
    
    def _extract_landmarks(self, landmarks, frame_shape: Tuple[int, int, int]) -> Dict:
        """
        Extract landmark coordinates and convert to pixel coordinates
        
        Args:
            landmarks: MediaPipe pose landmarks
            frame_shape: Shape of the input frame (height, width, channels)
            
        Returns:
            Dictionary with keypoint coordinates
        """
        height, width = frame_shape[:2]
        keypoints = {}
        
        for name, idx in self.keypoint_names.items():
            landmark = landmarks.landmark[idx]
            
            # Convert normalized coordinates to pixel coordinates
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            z = landmark.z  # Keep normalized depth
            
            keypoints[name] = {
                'x': x,
                'y': y,
                'z': z,
                'visibility': landmark.visibility
            }
        
        return keypoints
    
    def calculate_movement_velocity(self, keypoints: Dict, prev_keypoints: Optional[Dict]) -> Dict:
        """
        Calculate movement velocity for key body parts
        
        Args:
            keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            
        Returns:
            Dictionary with velocity data for different body parts
        """
        if prev_keypoints is None:
            return {}
        
        velocities = {}
        
        # Calculate velocity for important body parts
        important_parts = ['left_wrist', 'right_wrist', 'left_ankle', 'right_ankle', 'nose']
        
        for part in important_parts:
            if part in keypoints and part in prev_keypoints:
                curr_pos = (keypoints[part]['x'], keypoints[part]['y'])
                prev_pos = (prev_keypoints[part]['x'], prev_keypoints[part]['y'])
                
                # Calculate Euclidean distance
                velocity = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                velocities[part] = velocity
        
        return velocities
    
    def detect_fall(self, keypoints: Dict) -> Dict:
        """
        Detect potential fall based on body position
        
        Args:
            keypoints: Current frame keypoints
            
        Returns:
            Dictionary with fall detection results
        """
        try:
            # Check if key body parts are detected
            required_parts = ['nose', 'left_hip', 'right_hip', 'left_ankle', 'right_ankle']
            if not all(part in keypoints for part in required_parts):
                return {'detected': False, 'confidence': 0.0, 'reason': 'Missing keypoints'}
            
            # Calculate body position indicators
            nose_y = keypoints['nose']['y']
            hip_y = (keypoints['left_hip']['y'] + keypoints['right_hip']['y']) / 2
            ankle_y = (keypoints['left_ankle']['y'] + keypoints['right_ankle']['y']) / 2
            
            # Check if body is horizontal (potential fall)
            body_height = abs(hip_y - nose_y)
            body_width = abs(ankle_y - hip_y)
            
            # Fall detection logic
            is_horizontal = body_width > body_height * 1.5  # Body is more horizontal than vertical
            is_low_position = nose_y > hip_y  # Head is below hips
            
            fall_confidence = 0.0
            reason = ""
            
            if is_horizontal and is_low_position:
                fall_confidence = 0.8
                reason = "Body in horizontal position with head below hips"
            elif is_horizontal:
                fall_confidence = 0.6
                reason = "Body in horizontal position"
            elif is_low_position:
                fall_confidence = 0.4
                reason = "Head position below hips"
            
            return {
                'detected': fall_confidence > 0.5,
                'confidence': fall_confidence,
                'reason': reason,
                'body_height': body_height,
                'body_width': body_width
            }
            
        except Exception as e:
            logger.error(f"Error in fall detection: {e}")
            return {'detected': False, 'confidence': 0.0, 'reason': f'Error: {str(e)}'}
    
    def detect_rapid_movements(self, velocities: Dict, threshold: float = 50.0) -> Dict:
        """
        Detect rapid repetitive movements
        
        Args:
            velocities: Movement velocities for body parts
            threshold: Velocity threshold for rapid movement detection
            
        Returns:
            Dictionary with rapid movement detection results
        """
        rapid_movements = []
        
        for part, velocity in velocities.items():
            if velocity > threshold:
                rapid_movements.append({
                    'part': part,
                    'velocity': velocity,
                    'severity': 'high' if velocity > threshold * 2 else 'medium'
                })
        
        if rapid_movements:
            return {
                'detected': True,
                'confidence': min(0.9, len(rapid_movements) * 0.3),
                'movements': rapid_movements,
                'reason': f"Detected {len(rapid_movements)} rapid movements"
            }
        
        return {
            'detected': False,
            'confidence': 0.0,
            'movements': [],
            'reason': "No rapid movements detected"
        }
    
    def detect_immobility(self, keypoints: Dict, prev_keypoints: Optional[Dict], 
                         immobility_threshold: float = 5.0) -> Dict:
        """
        Detect immobility (freezing episode)
        
        Args:
            keypoints: Current frame keypoints
            prev_keypoints: Previous frame keypoints
            immobility_threshold: Threshold for considering movement as immobile
            
        Returns:
            Dictionary with immobility detection results
        """
        if prev_keypoints is None:
            return {'detected': False, 'confidence': 0.0, 'reason': 'No previous frame'}
        
        # Calculate total movement across all keypoints
        total_movement = 0
        movement_count = 0
        
        for part in keypoints:
            if part in prev_keypoints:
                curr_pos = (keypoints[part]['x'], keypoints[part]['y'])
                prev_pos = (prev_keypoints[part]['x'], prev_keypoints[part]['y'])
                
                movement = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                total_movement += movement
                movement_count += 1
        
        if movement_count > 0:
            avg_movement = total_movement / movement_count
            
            if avg_movement < immobility_threshold:
                return {
                    'detected': True,
                    'confidence': 0.7,
                    'reason': f"Low movement detected (avg: {avg_movement:.2f})",
                    'avg_movement': avg_movement
                }
        
        return {
            'detected': False,
            'confidence': 0.0,
            'reason': "Normal movement detected",
            'avg_movement': avg_movement if movement_count > 0 else 0
        }
    
    def draw_keypoints(self, frame: np.ndarray, keypoints_data: Dict) -> np.ndarray:
        """
        Draw keypoints on the frame for visualization
        
        Args:
            frame: Input frame
            keypoints_data: Keypoints data from extract_keypoints
            
        Returns:
            Frame with keypoints drawn
        """
        if keypoints_data is None or 'landmarks' not in keypoints_data:
            return frame
        
        # Create a copy of the frame
        annotated_frame = frame.copy()
        
        # Draw the pose landmarks
        self.mp_drawing.draw_landmarks(
            annotated_frame,
            keypoints_data['landmarks'],
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        return annotated_frame
    
    def release(self):
        """Release resources"""
        try:
            if hasattr(self, 'pose'):
                self.pose.close()
            logger.info("VideoProcessor resources released")
        except Exception as e:
            logger.error(f"Error releasing VideoProcessor resources: {e}")
