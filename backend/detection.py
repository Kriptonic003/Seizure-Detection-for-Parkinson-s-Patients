import numpy as np
import logging
from typing import Dict, List, Optional
from collections import deque
import time

logger = logging.getLogger(__name__)

class SeizureDetector:
    def __init__(self):
        """Initialize seizure detection system"""
        # Detection thresholds
        self.fall_threshold = 0.6
        self.rapid_movement_threshold = 50.0
        self.immobility_threshold = 5.0
        self.immobility_duration_threshold = 10.0  # seconds
        
        # State tracking
        self.prev_keypoints = None
        self.immobility_start_time = None
        self.immobility_detected = False
        self.alert_cooldown = 5.0  # seconds between alerts
        self.last_alert_time = 0
        
        # Movement history for pattern analysis
        self.movement_history = deque(maxlen=30)  # Store last 30 frames
        self.velocity_history = deque(maxlen=30)
        
        # Seizure pattern detection
        self.seizure_patterns = {
            'tonic_clonic': {
                'description': 'Tonic-clonic seizure with rhythmic movements',
                'velocity_threshold': 80.0,
                'pattern_threshold': 0.7
            },
            'myoclonic': {
                'description': 'Myoclonic seizure with sudden jerks',
                'velocity_threshold': 100.0,
                'pattern_threshold': 0.6
            },
            'atonic': {
                'description': 'Atonic seizure with sudden loss of muscle tone',
                'velocity_threshold': 20.0,
                'pattern_threshold': 0.8
            }
        }
        
        logger.info("SeizureDetector initialized successfully")
    
    def analyze_movement(self, keypoints_data: Dict) -> Dict:
        """
        Analyze movement patterns for seizure detection
        
        Args:
            keypoints_data: Keypoints data from video processing
            
        Returns:
            Dictionary with detection results
        """
        if keypoints_data is None or 'keypoints' not in keypoints_data:
            return self._create_no_alert_result()
        
        keypoints = keypoints_data['keypoints']
        current_time = time.time()
        
        # Check alert cooldown
        if current_time - self.last_alert_time < self.alert_cooldown:
            return self._create_no_alert_result()
        
        # Calculate velocities
        velocities = self._calculate_velocities(keypoints)
        
        # Store in history
        self.movement_history.append(keypoints)
        self.velocity_history.append(velocities)
        
        # Perform detection analyses
        detection_results = {
            'fall': self._detect_fall(keypoints),
            'rapid_movements': self._detect_rapid_movements(velocities),
            'immobility': self._detect_immobility(keypoints),
            'seizure_patterns': self._detect_seizure_patterns(velocities)
        }
        
        # Determine overall alert
        alert_result = self._determine_alert(detection_results)
        
        # Update state
        self.prev_keypoints = keypoints
        
        if alert_result['alert']:
            self.last_alert_time = current_time
        
        return alert_result
    
    def _calculate_velocities(self, keypoints: Dict) -> Dict:
        """Calculate movement velocities for key body parts"""
        if self.prev_keypoints is None:
            return {}
        
        velocities = {}
        important_parts = ['left_wrist', 'right_wrist', 'left_ankle', 'right_ankle', 'nose', 'left_shoulder', 'right_shoulder']
        
        for part in important_parts:
            if part in keypoints and part in self.prev_keypoints:
                curr_pos = (keypoints[part]['x'], keypoints[part]['y'])
                prev_pos = (self.prev_keypoints[part]['x'], self.prev_keypoints[part]['y'])
                
                velocity = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                velocities[part] = velocity
        
        return velocities
    
    def _detect_fall(self, keypoints: Dict) -> Dict:
        """Detect potential fall based on body position"""
        try:
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
            is_horizontal = body_width > body_height * 1.5
            is_low_position = nose_y > hip_y
            
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
                'detected': fall_confidence > self.fall_threshold,
                'confidence': fall_confidence,
                'reason': reason,
                'body_height': body_height,
                'body_width': body_width
            }
            
        except Exception as e:
            logger.error(f"Error in fall detection: {e}")
            return {'detected': False, 'confidence': 0.0, 'reason': f'Error: {str(e)}'}
    
    def _detect_rapid_movements(self, velocities: Dict) -> Dict:
        """Detect rapid repetitive movements"""
        rapid_movements = []
        
        for part, velocity in velocities.items():
            if velocity > self.rapid_movement_threshold:
                rapid_movements.append({
                    'part': part,
                    'velocity': velocity,
                    'severity': 'high' if velocity > self.rapid_movement_threshold * 2 else 'medium'
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
    
    def _detect_immobility(self, keypoints: Dict) -> Dict:
        """Detect immobility (freezing episode)"""
        if self.prev_keypoints is None:
            return {'detected': False, 'confidence': 0.0, 'reason': 'No previous frame'}
        
        # Calculate total movement
        total_movement = 0
        movement_count = 0
        
        for part in keypoints:
            if part in self.prev_keypoints:
                curr_pos = (keypoints[part]['x'], keypoints[part]['y'])
                prev_pos = (self.prev_keypoints[part]['x'], self.prev_keypoints[part]['y'])
                
                movement = np.sqrt((curr_pos[0] - prev_pos[0])**2 + (curr_pos[1] - prev_pos[1])**2)
                total_movement += movement
                movement_count += 1
        
        if movement_count > 0:
            avg_movement = total_movement / movement_count
            
            if avg_movement < self.immobility_threshold:
                if not self.immobility_detected:
                    self.immobility_start_time = time.time()
                    self.immobility_detected = True
                
                # Check if immobility has lasted long enough
                if time.time() - self.immobility_start_time > self.immobility_duration_threshold:
                    return {
                        'detected': True,
                        'confidence': 0.8,
                        'reason': f"Freezing episode detected (duration: {time.time() - self.immobility_start_time:.1f}s)",
                        'duration': time.time() - self.immobility_start_time
                    }
            else:
                self.immobility_detected = False
                self.immobility_start_time = None
        
        return {
            'detected': False,
            'confidence': 0.0,
            'reason': "Normal movement detected"
        }
    
    def _detect_seizure_patterns(self, velocities: Dict) -> Dict:
        """Detect specific seizure patterns"""
        detected_patterns = []
        
        for pattern_name, pattern_config in self.seizure_patterns.items():
            pattern_result = self._analyze_seizure_pattern(velocities, pattern_config)
            if pattern_result['detected']:
                detected_patterns.append(pattern_result)
        
        if detected_patterns:
            # Return the most confident pattern
            best_pattern = max(detected_patterns, key=lambda x: x['confidence'])
            return {
                'detected': True,
                'confidence': best_pattern['confidence'],
                'pattern_type': best_pattern['pattern_type'],
                'description': best_pattern['description'],
                'reason': f"Detected {best_pattern['pattern_type']} seizure pattern"
            }
        
        return {
            'detected': False,
            'confidence': 0.0,
            'reason': "No seizure patterns detected"
        }
    
    def _analyze_seizure_pattern(self, velocities: Dict, pattern_config: Dict) -> Dict:
        """Analyze velocities for specific seizure patterns"""
        high_velocity_count = 0
        total_velocity = 0
        
        for part, velocity in velocities.items():
            if velocity > pattern_config['velocity_threshold']:
                high_velocity_count += 1
            total_velocity += velocity
        
        if len(velocities) > 0:
            avg_velocity = total_velocity / len(velocities)
            pattern_consistency = self._calculate_pattern_consistency(velocities, pattern_config)
            
            if pattern_consistency > pattern_config['pattern_threshold']:
                return {
                    'detected': True,
                    'confidence': pattern_consistency,
                    'pattern_type': pattern_config['description'],
                    'description': pattern_config['description'],
                    'avg_velocity': avg_velocity
                }
        
        return {
            'detected': False,
            'confidence': 0.0,
            'pattern_type': pattern_config['description']
        }
    
    def _calculate_pattern_consistency(self, velocities: Dict, pattern_config: Dict) -> float:
        """Calculate consistency of movement pattern"""
        if len(velocities) == 0:
            return 0.0
        
        # Calculate how many movements exceed the threshold
        high_velocity_ratio = sum(1 for v in velocities.values() if v > pattern_config['velocity_threshold']) / len(velocities)
        
        # Calculate average velocity relative to threshold
        avg_velocity = sum(velocities.values()) / len(velocities)
        velocity_ratio = avg_velocity / pattern_config['velocity_threshold']
        
        # Combine both factors
        consistency = (high_velocity_ratio * 0.6) + (min(velocity_ratio, 1.0) * 0.4)
        
        return min(consistency, 1.0)
    
    def _determine_alert(self, detection_results: Dict) -> Dict:
        """Determine if an alert should be triggered based on detection results"""
        alerts = []
        
        # Check each detection type
        for detection_type, result in detection_results.items():
            if result['detected']:
                alerts.append({
                    'type': detection_type,
                    'confidence': result['confidence'],
                    'description': result.get('reason', ''),
                    'details': result
                })
        
        if alerts:
            # Return the most confident alert
            best_alert = max(alerts, key=lambda x: x['confidence'])
            return {
                'alert': True,
                'type': best_alert['type'],
                'confidence': best_alert['confidence'],
                'description': best_alert['description'],
                'details': best_alert['details']
            }
        
        return self._create_no_alert_result()
    
    def _create_no_alert_result(self) -> Dict:
        """Create a result indicating no alert"""
        return {
            'alert': False,
            'type': 'none',
            'confidence': 0.0,
            'description': 'No abnormal movements detected'
        }
    
    def reset_state(self):
        """Reset detector state"""
        self.prev_keypoints = None
        self.immobility_start_time = None
        self.immobility_detected = False
        self.last_alert_time = 0
        self.movement_history.clear()
        self.velocity_history.clear()
        logger.info("SeizureDetector state reset")
