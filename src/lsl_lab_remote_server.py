#!/usr/bin/env python3
"""
LSL-Lab Remote Control Server
This module provides HTTP API endpoints for remote control of LSL-Lab instances.
Integrate this with your existing LSL-Lab.py file.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import logging
import time

logger = logging.getLogger(__name__)

class LSLLabRemoteServer:
    """
    Flask server that provides remote control API for LSL-Lab instances.
    This should be integrated with your existing PolarStreamRecorder class.
    """
    
    def __init__(self, polar_recorder_instance, port=8080, host='0.0.0.0'):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        self.polar_recorder = polar_recorder_instance
        self.port = port
        self.host = host
        self.server_thread = None
        self.running = False
        
        # Configure Flask logging
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        
        self.setup_routes()
    
    def setup_routes(self):
        """Set up all API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            try:
                return jsonify({
                    "status": "healthy",
                    "service": "LSL-Lab",
                    "version": "1.0.0",
                    "device_connected": getattr(self.polar_recorder, 'connected', False),
                    "recording": getattr(self.polar_recorder, 'recording', False),
                    "participant_id": getattr(self.polar_recorder, 'current_participant_id', None),
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/participant/set', methods=['POST'])
        def set_participant():
            """Set participant ID"""
            try:
                data = request.json
                if not data:
                    return jsonify({"success": False, "message": "No data provided"}), 400
                
                participant_id = data.get('participant_id')
                if not participant_id or not participant_id.strip():
                    return jsonify({"success": False, "message": "Participant ID is required"}), 400
                
                # Set participant ID on the recorder
                if hasattr(self.polar_recorder, 'set_participant_id'):
                    success = self.polar_recorder.set_participant_id(participant_id.strip())
                    if success:
                        return jsonify({
                            "success": True, 
                            "message": f"Participant ID set to {participant_id.strip()}"
                        })
                    else:
                        return jsonify({
                            "success": False, 
                            "message": "Failed to set participant ID"
                        }), 500
                else:
                    # Direct assignment if no method available
                    self.polar_recorder.current_participant_id = participant_id.strip()
                    return jsonify({
                        "success": True, 
                        "message": f"Participant ID set to {participant_id.strip()}"
                    })
                    
            except Exception as e:
                logger.error(f"Set participant error: {e}")
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/api/recording/start', methods=['POST'])
        def start_recording():
            """Start recording"""
            try:
                if not getattr(self.polar_recorder, 'connected', False):
                    return jsonify({
                        "success": False, 
                        "message": "Device not connected"
                    }), 400
                
                if getattr(self.polar_recorder, 'recording', False):
                    return jsonify({
                        "success": False, 
                        "message": "Already recording"
                    }), 400
                
                # Start recording
                if hasattr(self.polar_recorder, 'toggle_recording'):
                    self.polar_recorder.toggle_recording()
                elif hasattr(self.polar_recorder, 'start_recording'):
                    self.polar_recorder.start_recording()
                else:
                    return jsonify({
                        "success": False, 
                        "message": "Recording method not available"
                    }), 500
                
                return jsonify({
                    "success": True, 
                    "message": "Recording started successfully"
                })
                
            except Exception as e:
                logger.error(f"Start recording error: {e}")
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/api/recording/stop', methods=['POST'])
        def stop_recording():
            """Stop recording"""
            try:
                if not getattr(self.polar_recorder, 'recording', False):
                    return jsonify({
                        "success": False, 
                        "message": "Not currently recording"
                    }), 400
                
                # Stop recording
                if hasattr(self.polar_recorder, 'toggle_recording'):
                    self.polar_recorder.toggle_recording()
                elif hasattr(self.polar_recorder, 'stop_recording'):
                    self.polar_recorder.stop_recording()
                else:
                    return jsonify({
                        "success": False, 
                        "message": "Stop recording method not available"
                    }), 500
                
                return jsonify({
                    "success": True, 
                    "message": "Recording stopped successfully"
                })
                
            except Exception as e:
                logger.error(f"Stop recording error: {e}")
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/api/interval/start', methods=['POST'])
        def start_interval():
            """Start measurement interval"""
            try:
                if not getattr(self.polar_recorder, 'recording', False):
                    return jsonify({
                        "success": False, 
                        "message": "Recording not active"
                    }), 400
                
                # Get optional interval name
                data = request.json or {}
                interval_name = data.get('interval_name')
                
                # Start interval
                if hasattr(self.polar_recorder, 'start_interval'):
                    if interval_name:
                        # If the method accepts parameters
                        try:
                            self.polar_recorder.start_interval(interval_name)
                        except TypeError:
                            # Method doesn't accept parameters
                            self.polar_recorder.start_interval()
                    else:
                        self.polar_recorder.start_interval()
                else:
                    return jsonify({
                        "success": False, 
                        "message": "Interval functionality not available"
                    }), 500
                
                message = "Interval started successfully"
                if interval_name:
                    message += f" ({interval_name})"
                
                return jsonify({
                    "success": True, 
                    "message": message
                })
                
            except Exception as e:
                logger.error(f"Start interval error: {e}")
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/api/interval/end', methods=['POST'])
        def end_interval():
            """End measurement interval"""
            try:
                if not getattr(self.polar_recorder, 'recording', False):
                    return jsonify({
                        "success": False, 
                        "message": "Recording not active"
                    }), 400
                
                # End interval
                if hasattr(self.polar_recorder, 'end_interval'):
                    self.polar_recorder.end_interval()
                else:
                    return jsonify({
                        "success": False, 
                        "message": "Interval functionality not available"
                    }), 500
                
                return jsonify({
                    "success": True, 
                    "message": "Interval ended successfully"
                })
                
            except Exception as e:
                logger.error(f"End interval error: {e}")
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.route('/api/timestamp/mark', methods=['POST'])
        def mark_timestamp():
            """Mark timestamp during recording"""
            try:
                if not getattr(self.polar_recorder, 'recording', False):
                    return jsonify({
                        "success": False, 
                        "message": "Recording not active"
                    }), 400
                
                # Get optional timestamp name
                data = request.json or {}
                timestamp_name = data.get('timestamp_name')
                
                # Mark timestamp
                if hasattr(self.polar_recorder, 'mark_timestamp'):
                    if timestamp_name:
                        # If the method accepts parameters
                        try:
                            self.polar_recorder.mark_timestamp(timestamp_name)
                        except TypeError:
                            # Method doesn't accept parameters
                            self.polar_recorder.mark_timestamp()
                    else:
                        self.polar_recorder.mark_timestamp()
                else:
                    return jsonify({
                        "success": False, 
                        "message": "Timestamp functionality not available"
                    }), 500
                
                message = "Timestamp marked successfully"
                if timestamp_name:
                    message += f" ({timestamp_name})"
                
                return jsonify({
                    "success": True, 
                    "message": message
                })
                
            except Exception as e:
                logger.error(f"Mark timestamp error: {e}")
                return jsonify({"success": False, "message": str(e)}), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({"success": False, "message": "Endpoint not found"}), 404
        
        @self.app.errorhandler(405)
        def method_not_allowed(error):
            return jsonify({"success": False, "message": "Method not allowed"}), 405
    
    def start_server(self):
        """Start the Flask server in a separate thread"""
        if self.running:
            logger.warning("Server is already running")
            return
        
        def run_server():
            try:
                self.running = True
                self.app.run(
                    host=self.host, 
                    port=self.port, 
                    debug=False,
                    threaded=True,
                    use_reloader=False
                )
            except Exception as e:
                logger.error(f"Server error: {e}")
            finally:
                self.running = False
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait a moment to ensure server started
        time.sleep(0.5)
        
        logger.info(f"LSL-Lab Remote Control API server started on {self.host}:{self.port}")
        print(f"✓ Remote Control API server running on http://{self.host}:{self.port}")
        print(f"  Health check: http://{self.host}:{self.port}/api/health")
    
    def stop_server(self):
        """Stop the Flask server"""
        self.running = False
        logger.info("LSL-Lab Remote Control API server stopped")

# Integration example for LSL-Lab.py:
"""
To integrate this with your existing LSL-Lab.py, add this code:

1. Add imports at the top:
   from src.lsl_lab_remote_server import LSLLabRemoteServer

2. In your PolarStreamRecorder.__init__ method, add:
   self.api_server = None

3. After creating your PolarStreamRecorder instance, start the API server:
   
   # Create recorder
   recorder = PolarStreamRecorder(parent_frame)
   
   # Start remote control API server
   api_server = LSLLabRemoteServer(recorder, port=8080)
   api_server.start_server()
   
   # Store reference to stop server when closing
   recorder.api_server = api_server

4. In your window close handler, add:
   if hasattr(recorder, 'api_server') and recorder.api_server:
       recorder.api_server.stop_server()

This will make your LSL-Lab instance remotely controllable via HTTP API.
""" 