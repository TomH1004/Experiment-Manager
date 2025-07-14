#!/usr/bin/env python3
"""
VR Experiment Manager Web Application
Flask backend for controlling Unity VR experiments via UDP broadcast messages.
"""

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room
import logging
from logging.handlers import RotatingFileHandler
import os
import time
import threading
import atexit

# Import application modules
from .experiment_manager import VRExperimentManager
from .api_routes import create_api_routes
from .config_routes import create_config_routes
from .order_routes import create_order_routes
from .lsl_routes import create_lsl_routes
from .lsl_remote_controller import cleanup_lsl_controller

# Initialize Flask app
app = Flask(__name__, template_folder='../static', static_folder='../static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

def setup_logging():
    """Setup file logging for the application"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create a rotating file handler
    log_file = os.path.join('logs', 'vr_experiment_manager.log')
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Set logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Configure app logger
    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # Configure socketio logger
    socketio_logger = logging.getLogger('socketio')
    socketio_logger.setLevel(logging.INFO)
    socketio_logger.addHandler(file_handler)
    
    # Configure werkzeug logger (Flask's HTTP server)
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)  # Reduce HTTP request noise
    werkzeug_logger.addHandler(file_handler)
    
    return app.logger

# Initialize logging
logger = setup_logging()

# Initialize experiment manager
manager = VRExperimentManager()

# Enhanced timer loop with socketio integration
class TimerManager:
    def __init__(self, manager, socketio):
        self.manager = manager
        self.socketio = socketio
        self.timer_thread = None
        
    def start_timer_loop(self):
        """Start the timer loop if not already running"""
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
    
    def _timer_loop(self):
        """Enhanced timer loop that runs in a separate thread"""
        while True:
            active_sessions = []
            
            for session_id, session_data in self.manager.sessions.items():
                if session_data['countdown_active'] and session_data['condition_start_time'] is not None:
                    elapsed_time = time.time() - session_data['condition_start_time']
                    remaining_time = max(0, 300 - elapsed_time)  # 300 seconds = 5 minutes
                    
                    if remaining_time > 0:
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        countdown_text = f"Time Remaining: {minutes:02d}:{seconds:02d}"
                        
                        # Emit countdown update
                        self.socketio.emit('countdown_update', {
                            'countdown_text': countdown_text,
                            'remaining_time': remaining_time
                        }, room=session_id)
                        
                        active_sessions.append(session_id)
                    else:
                        # Timer expired
                        session_data['countdown_active'] = False
                        self._condition_finished(session_id)
            
            # Check for sessions that need their timer started
            for session_id, session_data in self.manager.sessions.items():
                if session_data.get('practice_trial_active') and session_data.get('practice_start_time'):
                    elapsed_time = time.time() - session_data['practice_start_time']
                    remaining_time = max(0, 60 - elapsed_time)  # 60 seconds for practice
                    
                    if remaining_time > 0:
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        countdown_text = f"Practice Time: {minutes:02d}:{seconds:02d}"
                        
                        # Emit countdown update
                        self.socketio.emit('countdown_update', {
                            'countdown_text': countdown_text,
                            'remaining_time': remaining_time
                        }, room=session_id)
                    else:
                        # Practice timer expired
                        session_data['practice_trial_active'] = False
                        session_data['practice_start_time'] = None
                        
                        # Emit practice completion
                        self.socketio.emit('practice_complete', {
                            'message': 'Practice trial completed'
                        }, room=session_id)
                        
                        # Update status
                        self.socketio.emit('status_update', {
                            'status': 'Practice trial completed',
                            'practice_trial': False,
                            'countdown_active': False
                        }, room=session_id)
            
            time.sleep(1)  # Check every second
    
    def _condition_finished(self, session_id):
        """Handle when a condition timer expires"""
        try:
            # Emit condition finished event
            self.socketio.emit('condition_finished', {
                'message': 'Condition time expired'
            }, room=session_id)
            
            # Emit status update showing timer expired
            self.socketio.emit('status_update', {
                'status': 'Condition time expired - Ready for next condition',
                'countdown_text': 'Time Expired',
                'countdown_active': False,
                'enable_next': True,
                'enable_force_next': False
            }, room=session_id)
            
            # Send UDP message to disable all objects
            session_data = self.manager.get_session(session_id)
            self.manager.send_udp_message({
                "command": "disable_all",
                "reason": "timer_expired"
            }, session_data)
            
            self.manager.log_message(session_id, "Condition timer expired - all objects disabled")
            
        except Exception as e:
            logger.error(f"Error handling condition finish for session {session_id}: {e}")

# Create timer manager
timer_manager = TimerManager(manager, socketio)

def enhanced_start_countdown_timer(session_id):
    """Enhanced version of start_countdown_timer with socketio support"""
    session_data = manager.get_session(session_id)
    session_data['countdown_active'] = True
    session_data['condition_start_time'] = time.time()
    
    # Start timer thread if not running
    timer_manager.start_timer_loop()
    
    # Log the timer start
    manager.log_message(session_id, "Condition countdown timer started (5:00)")
    
    # Emit initial countdown state
    socketio.emit('countdown_update', {
        'countdown_text': "Time Remaining: 05:00",
        'remaining_time': 300
    }, room=session_id)

def enhanced_log_message(session_id, message):
    """Enhanced version of log_message with socketio support"""
    log_entry = manager.log_message(session_id, message)
    
    # Emit log update via socketio
    socketio.emit('log_update', {
        'timestamp': log_entry.split(']')[0][1:],  # Extract timestamp
        'message': message,
        'full_message': log_entry
    }, room=session_id)
    
    return log_entry

# Override the manager's start_countdown_timer method
manager.start_countdown_timer = enhanced_start_countdown_timer

# Register blueprints
api_routes = create_api_routes(manager, socketio)
config_routes = create_config_routes(manager)
order_routes = create_order_routes(manager)
lsl_routes = create_lsl_routes(manager, socketio)

app.register_blueprint(api_routes)
app.register_blueprint(config_routes)
app.register_blueprint(order_routes)
app.register_blueprint(lsl_routes)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    """Handle joining a session room"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined_session', {'session_id': session_id})
        logger.info(f"Client {request.sid} joined session {session_id}")

# Override the manager's log_message method to use socketio
manager.log_message = enhanced_log_message

# Setup cleanup function for application shutdown
def cleanup_on_exit():
    """Cleanup function to run on application exit"""
    import asyncio
    try:
        # Run the cleanup in an event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup_lsl_controller())
        loop.close()
        logger.info("LSL controller cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Register cleanup function
atexit.register(cleanup_on_exit)

if __name__ == '__main__':
    logger.info("Starting VR Experiment Manager")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 