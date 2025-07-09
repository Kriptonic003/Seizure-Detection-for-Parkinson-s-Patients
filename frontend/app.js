// Seizure Detection Frontend Application
class SeizureDetectionApp {
    constructor() {
        this.socket = null;
        this.isMonitoring = false;
        this.alertCount = 0;
        this.lastAlert = null;
        this.stream = null; // Store camera stream
        this.canvas = null;
        this.ctx = null;
        this.frameInterval = null;
        
        // DOM elements
        this.videoFeed = document.getElementById('videoFeed');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.alertLog = document.getElementById('alertLog');
        this.totalAlerts = document.getElementById('totalAlerts');
        this.lastAlertElement = document.getElementById('lastAlert');
        
        this.initializeEventListeners();
        this.initializeSocketIO();
        this.initializeCamera(); // Initialize camera access
        this.setupCanvas(); // Setup canvas for frame capture
    }

    setupCanvas() {
        // Create canvas for frame capture
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
    }

    initializeCamera() {
        // Simple camera permission request
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                this.stream = stream;
                this.videoFeed.srcObject = stream;
                
                // Set canvas size to match video
                this.videoFeed.addEventListener('loadedmetadata', () => {
                    this.canvas.width = this.videoFeed.videoWidth;
                    this.canvas.height = this.videoFeed.videoHeight;
                });
                
                this.updateStatus('Camera connected', 'connected');
                console.log('Camera initialized successfully');
            })
            .catch(error => {
                console.error('Camera access error:', error);
                this.updateStatus('Camera access denied', 'error');
                this.showNotification('Please allow camera access to use this application', 'error');
            });
    }

    initializeEventListeners() {
        this.startBtn.addEventListener('click', () => this.startMonitoring());
        this.stopBtn.addEventListener('click', () => this.stopMonitoring());
    }

    initializeSocketIO() {
        try {
            this.socket = io('http://localhost:5000');
            
            this.socket.on('connect', () => {
                this.updateStatus('Connected to server', 'connected');
            });
            
            this.socket.on('disconnect', () => {
                this.updateStatus('Disconnected from server', 'disconnected');
            });
            
            this.socket.on('status', (data) => {
                this.handleWebSocketMessage(data);
            });
            
            this.socket.on('alert', (data) => {
                this.handleWebSocketMessage({type: 'alert', ...data});
            });

            this.socket.on('processing_result', (data) => {
                console.log('Processing result:', data);
            });
        } catch (error) {
            console.error('Failed to connect to Socket.IO:', error);
            this.updateStatus('Server not available', 'error');
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'status':
                this.updateStatus(data.message, data.status);
                break;
            case 'alert':
                this.handleAlert(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    startMonitoring() {
        if (!this.stream) {
            this.showNotification('Camera not available. Please allow camera access.', 'error');
            return;
        }
        
        if (this.socket) {
            this.socket.emit('start_monitoring');
            this.isMonitoring = true;
            this.startBtn.disabled = true;
            this.stopBtn.disabled = false;
            this.updateStatus('Monitoring...', 'monitoring');
            
            // Start sending frames to backend
            this.startFrameCapture();
        } else {
            this.showNotification('Cannot start monitoring - server not connected', 'error');
        }
    }

    stopMonitoring() {
        if (this.socket) {
            this.socket.emit('stop_monitoring');
            this.isMonitoring = false;
            this.startBtn.disabled = false;
            this.stopBtn.disabled = true;
            this.updateStatus('Monitoring stopped', 'stopped');
            
            // Stop sending frames
            this.stopFrameCapture();
        }
    }

    startFrameCapture() {
        // Send frames every 200ms (5 FPS) to reduce load
        this.frameInterval = setInterval(() => {
            if (this.isMonitoring) {
                this.captureAndSendFrame();
            }
        }, 200);
    }

    stopFrameCapture() {
        if (this.frameInterval) {
            clearInterval(this.frameInterval);
            this.frameInterval = null;
        }
    }

    captureAndSendFrame() {
        try {
            // Draw current video frame to canvas
            this.ctx.drawImage(this.videoFeed, 0, 0, this.canvas.width, this.canvas.height);
            
            // Convert canvas to base64 data
            const frameData = this.canvas.toDataURL('image/jpeg', 0.8);
            
            // Send frame data to backend via WebSocket
            if (this.socket) {
                this.socket.emit('frame_data', {
                    frame: frameData,
                    timestamp: Date.now()
                });
            }
            
            // Also send via HTTP POST for compatibility
            this.sendFrameViaHTTP(frameData);
            
        } catch (error) {
            console.error('Error capturing frame:', error);
        }
    }

    async sendFrameViaHTTP(frameData) {
        try {
            const response = await fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: frameData
                })
            });
            
            const result = await response.json();
            
            if (result.seizure_detected) {
                this.handleAlert({
                    alert_type: 'Seizure Detected',
                    timestamp: new Date().toISOString(),
                    description: result.detection_result?.description || 'Seizure detected'
                });
            }
            
        } catch (error) {
            console.error('Error sending frame via HTTP:', error);
        }
    }

    updateStatus(message, status) {
        this.statusText.textContent = message;
        this.statusIndicator.className = 'status-indicator';
        
        switch (status) {
            case 'alert':
                this.statusIndicator.classList.add('alert');
                this.playAlertSound();
                break;
            case 'monitoring':
                this.statusIndicator.classList.add('monitoring');
                break;
            case 'connected':
                this.statusIndicator.classList.add('connected');
                break;
            case 'disconnected':
            case 'error':
                this.statusIndicator.classList.add('error');
                break;
        }
    }

    handleAlert(alertData) {
        this.alertCount++;
        this.lastAlert = new Date();
        
        // Update stats
        this.totalAlerts.textContent = this.alertCount;
        this.lastAlertElement.textContent = this.lastAlert.toLocaleTimeString();
        
        // Add alert to log
        this.addAlertToLog(alertData);
        
        // Update status
        this.updateStatus('Seizure Detected!', 'alert');
        
        // Show notification
        this.showNotification(`Seizure detected at ${this.lastAlert.toLocaleTimeString()}`, 'alert');
    }

    addAlertToLog(alertData) {
        // Remove "no alerts" message if present
        const noAlerts = this.alertLog.querySelector('.no-alerts');
        if (noAlerts) {
            noAlerts.remove();
        }
        
        // Create alert item
        const alertItem = document.createElement('div');
        alertItem.className = 'alert-item';
        
        const alertTime = document.createElement('span');
        alertTime.className = 'alert-time';
        alertTime.textContent = new Date().toLocaleTimeString();
        
        const alertType = document.createElement('span');
        alertType.className = 'alert-type';
        alertType.textContent = alertData.alert_type || 'Seizure';
        
        alertItem.appendChild(alertTime);
        alertItem.appendChild(alertType);
        
        // Add to top of log
        this.alertLog.insertBefore(alertItem, this.alertLog.firstChild);
        
        // Keep only last 10 alerts
        const alerts = this.alertLog.querySelectorAll('.alert-item');
        if (alerts.length > 10) {
            alerts[alerts.length - 1].remove();
        }
    }

    playAlertSound() {
        // Create audio context for alert sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.log('Could not play alert sound:', error);
        }
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'alert' ? '#e74c3c' : '#3498db'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        
        // Add animation keyframes
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(notification);
        
        // Remove notification after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new SeizureDetectionApp();
    
    // Make app globally available for debugging
    window.seizureDetectionApp = app;
});
