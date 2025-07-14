# LSL-Lab Remote Control API Specification

This document describes the API endpoints that LSL-Lab instances must implement to be remotely controlled by the VR Experiment Manager.

## Base URL
All endpoints should be accessible at: `http://{device_ip}:{port}/api/`

Default port: `8080`

## Required Endpoints

### 1. Health Check
**GET** `/api/health`

Returns the health status of the LSL-Lab instance.

**Response:**
```json
{
  "status": "healthy",
  "service": "LSL-Lab",
  "version": "1.0.0",
  "device_connected": true,
  "recording": false
}
```

### 2. Set Participant ID
**POST** `/api/participant/set`

Set the participant ID for the current session.

**Request Body:**
```json
{
  "participant_id": "P001"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Participant ID set to P001"
}
```

### 3. Start Recording
**POST** `/api/recording/start`

Start recording physiological data.

**Response:**
```json
{
  "success": true,
  "message": "Recording started successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Device not connected or already recording"
}
```

### 4. Stop Recording
**POST** `/api/recording/stop`

Stop recording physiological data.

**Response:**
```json
{
  "success": true,
  "message": "Recording stopped successfully"
}
```

### 5. Start Interval
**POST** `/api/interval/start`

Start a new measurement interval.

**Request Body (Optional):**
```json
{
  "interval_name": "Condition_1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Interval started successfully"
}
```

### 6. End Interval
**POST** `/api/interval/end`

End the current measurement interval.

**Response:**
```json
{
  "success": true,
  "message": "Interval ended successfully"
}
```

### 7. Mark Timestamp
**POST** `/api/timestamp/mark`

Mark a specific timestamp during recording.

**Request Body (Optional):**
```json
{
  "timestamp_name": "Event_1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Timestamp marked successfully"
}
```

## Implementation Notes

### Error Handling
All endpoints should return appropriate HTTP status codes:
- `200 OK`: Successful operation
- `400 Bad Request`: Invalid request data
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Device not connected

### CORS Headers
Include CORS headers to allow cross-origin requests:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
```

### Integration with LSL-Lab.py

To integrate these endpoints with the existing LSL-Lab.py, you can add a simple Flask server alongside the GUI:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

class LSLLabAPIServer:
    def __init__(self, polar_recorder_instance, port=8080):
        self.app = Flask(__name__)
        CORS(self.app)
        self.polar_recorder = polar_recorder_instance
        self.port = port
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/api/health', methods=['GET'])
        def health():
            return jsonify({
                "status": "healthy",
                "service": "LSL-Lab",
                "device_connected": self.polar_recorder.connected,
                "recording": self.polar_recorder.recording
            })
            
        @self.app.route('/api/participant/set', methods=['POST'])
        def set_participant():
            data = request.json
            participant_id = data.get('participant_id')
            if participant_id:
                self.polar_recorder.current_participant_id = participant_id
                return jsonify({"success": True, "message": f"Participant ID set to {participant_id}"})
            return jsonify({"success": False, "message": "Participant ID required"}), 400
            
        @self.app.route('/api/recording/start', methods=['POST'])
        def start_recording():
            if self.polar_recorder.connected and not self.polar_recorder.recording:
                self.polar_recorder.toggle_recording()
                return jsonify({"success": True, "message": "Recording started successfully"})
            return jsonify({"success": False, "message": "Cannot start recording"}), 400
            
        @self.app.route('/api/recording/stop', methods=['POST'])
        def stop_recording():
            if self.polar_recorder.recording:
                self.polar_recorder.toggle_recording()
                return jsonify({"success": True, "message": "Recording stopped successfully"})
            return jsonify({"success": False, "message": "Not currently recording"}), 400
            
        @self.app.route('/api/interval/start', methods=['POST'])
        def start_interval():
            if self.polar_recorder.recording:
                self.polar_recorder.start_interval()
                return jsonify({"success": True, "message": "Interval started successfully"})
            return jsonify({"success": False, "message": "Recording not active"}), 400
            
        @self.app.route('/api/interval/end', methods=['POST'])
        def end_interval():
            if self.polar_recorder.recording:
                self.polar_recorder.end_interval()
                return jsonify({"success": True, "message": "Interval ended successfully"})
            return jsonify({"success": False, "message": "Recording not active"}), 400
            
        @self.app.route('/api/timestamp/mark', methods=['POST'])
        def mark_timestamp():
            if self.polar_recorder.recording:
                self.polar_recorder.mark_timestamp()
                return jsonify({"success": True, "message": "Timestamp marked successfully"})
            return jsonify({"success": False, "message": "Recording not active"}), 400
    
    def start_server(self):
        def run_server():
            self.app.run(host='0.0.0.0', port=self.port, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print(f"LSL-Lab API server started on port {self.port}")

# Add to your LSL-Lab.py initialization:
# api_server = LSLLabAPIServer(polar_recorder_instance)
# api_server.start_server()
```

## Security Considerations

1. **Network Security**: Ensure LSL-Lab instances are on a trusted network
2. **Authentication**: Consider adding API key authentication for production use
3. **Input Validation**: Validate all input parameters
4. **Rate Limiting**: Implement rate limiting to prevent API abuse

## Testing

Test the API endpoints using tools like:
- `curl`
- Postman
- Python `requests` library

Example test:
```bash
curl -X GET http://192.168.1.100:8080/api/health
curl -X POST http://192.168.1.100:8080/api/recording/start
``` 