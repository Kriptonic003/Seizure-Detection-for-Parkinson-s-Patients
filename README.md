# Seizure Detection for Parkinson's Patients

A real-time web application for detecting seizures and abnormal movements in Parkinson's patients using computer vision and CCTV footage analysis.

## Features

### 🔍 **Real-time Detection**
- **Fall Detection**: Identifies sudden falls based on body position analysis
- **Rapid Movement Detection**: Detects repetitive limb movements characteristic of seizures
- **Immobility Detection**: Monitors for freezing episodes lasting over 10 seconds
- **Seizure Pattern Recognition**: Analyzes movement patterns for different seizure types

### 🎯 **Detection Types**
- **Tonic-Clonic Seizures**: Rhythmic movements with high velocity
- **Myoclonic Seizures**: Sudden jerks and rapid movements
- **Atonic Seizures**: Sudden loss of muscle tone
- **Freezing Episodes**: Extended periods of immobility
- **Falls**: Horizontal body position with head below hips

### 🚨 **Alert System**
- **Real-time Alerts**: Immediate notification when abnormal movements are detected
- **Audio Alerts**: Text-to-speech announcements for immediate attention
- **Visual Indicators**: Status updates and alert logging
- **WebSocket Communication**: Real-time updates to frontend

### 📊 **Monitoring Interface**
- **Live Video Feed**: Real-time CCTV/webcam stream
- **Status Dashboard**: Current monitoring status and statistics
- **Alert Log**: Historical record of detected events
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Technology Stack

### Backend
- **Flask**: Web framework for API and WebSocket server
- **OpenCV**: Video capture and processing
- **MediaPipe**: Body pose detection and keypoint extraction
- **NumPy**: Numerical computations for movement analysis
- **pyttsx3**: Text-to-speech for audio alerts

### Frontend
- **HTML5/CSS3**: Modern, responsive user interface
- **JavaScript**: Real-time WebSocket communication
- **WebSocket**: Real-time bidirectional communication

## Installation

### Prerequisites
- Python 3.8 or higher
- Webcam or CCTV camera
- Windows/Linux/macOS

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd parkinson
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   cd backend
   python app.py
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The application will start monitoring automatically

## Usage

### Starting Monitoring
1. Open the web application in your browser
2. Click "Start Monitoring" to begin real-time detection
3. The system will analyze video feed for abnormal movements
4. Alerts will be displayed in real-time when detected

### Alert Types
- **Seizure Detected**: Abnormal movement patterns detected
- **Fall Detected**: Person appears to have fallen
- **Freezing Episode**: Extended period of immobility
- **Rapid Movements**: Sudden, repetitive limb movements

### Configuration
The system can be configured by modifying detection thresholds in `backend/detection.py`:
- `fall_threshold`: Sensitivity for fall detection
- `rapid_movement_threshold`: Velocity threshold for rapid movements
- `immobility_threshold`: Movement threshold for freezing detection
- `immobility_duration_threshold`: Duration for immobility alerts

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Video Input   │
│                 │    │                 │    │                 │
│ • HTML/CSS/JS   │◄──►│ • Flask Server  │◄──►│ • Webcam/CCTV   │
│ • WebSocket     │    │ • OpenCV        │    │ • Video Stream  │
│ • Real-time UI  │    │ • MediaPipe     │    │                 │
│ • Alert Display │    │ • Detection     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Detection Algorithm

### 1. **Keypoint Extraction**
- Uses MediaPipe Pose to extract 33 body keypoints
- Converts normalized coordinates to pixel coordinates
- Tracks visibility and confidence scores

### 2. **Movement Analysis**
- Calculates velocity between consecutive frames
- Analyzes movement patterns over time
- Detects sudden changes in body position

### 3. **Pattern Recognition**
- Compares current movements to known seizure patterns
- Uses machine learning thresholds for classification
- Maintains movement history for consistency analysis

### 4. **Alert Generation**
- Combines multiple detection methods
- Applies confidence thresholds
- Generates appropriate alerts with descriptions

## File Structure

```
parkinson/
├── backend/
│   ├── __init__.py
│   ├── app.py              # Main Flask application
│   ├── video_processing.py # OpenCV and MediaPipe processing
│   ├── detection.py        # Seizure detection algorithms
│   └── event_log.txt       # Alert logging
├── frontend/
│   ├── index.html          # Main application page
│   ├── styles.css          # CSS styling
│   └── app.js             # JavaScript functionality
├── requirements.txt        # Python dependencies
└── README.md              # Project documentation
```

## API Endpoints

### HTTP Endpoints
- `GET /`: Main application page
- `GET /api/status`: Get current system status
- `POST /api/start`: Start monitoring
- `POST /api/stop`: Stop monitoring

### WebSocket Events
- `connect`: Client connection
- `disconnect`: Client disconnection
- `start_monitoring`: Start monitoring request
- `stop_monitoring`: Stop monitoring request
- `alert`: Seizure alert notification
- `status`: Status update

## Troubleshooting

### Common Issues

1. **Camera not detected**
   - Ensure webcam is connected and not in use by other applications
   - Check camera permissions in your operating system

2. **MediaPipe installation issues**
   - Update pip: `pip install --upgrade pip`
   - Install MediaPipe: `pip install mediapipe`

3. **WebSocket connection errors**
   - Ensure backend server is running on port 5000
   - Check firewall settings
   - Verify browser supports WebSocket

4. **Performance issues**
   - Reduce video resolution in `video_processing.py`
   - Adjust detection thresholds for your environment
   - Close other applications using the camera

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Medical Disclaimer

⚠️ **Important**: This system is designed for research and monitoring purposes only. It should not replace professional medical diagnosis or treatment. Always consult with healthcare professionals for medical decisions.

## Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Compatibility**: Python 3.8+, Modern Browsers
