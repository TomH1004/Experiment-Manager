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

# Import application modules
from .experiment_manager import VRExperimentManager
from .api_routes import create_api_routes
from .config_routes import create_config_routes
from .order_routes import create_order_routes

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
            
            if not active_sessions:
                break
            
            time.sleep(1)
    
    def _condition_finished(self, session_id):
        """Called when the 5-minute timer expires"""
        session_data = self.manager.get_session(session_id)
        
        self.manager.log_message(session_id, "5-minute timer expired - sending disable_all command")
        
        # Send command to Unity to disable all objects and avatars
        message_data = {
            "command": "disable_all",
            "reason": "timer_expired"
        }
        
        if self.manager.send_udp_message(session_id, message_data):
            # Check if this was the last condition
            is_last_condition = session_data['current_condition_index'] >= len(session_data['experiment_sequence']) - 1
            
            if is_last_condition:
                # This was the last condition - mark experiment as completed
                self.manager.complete_experiment(session_id)
                
                # Emit completion status
                self.socketio.emit('status_update', {
                    'status': 'Final condition completed - Experiment finished!',
                    'countdown_text': 'Experiment Complete',
                    'enable_next': False,
                    'disable_start': True,
                    'disable_next': True,
                    'disable_force_next': True,
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': True,
                    'countdown_active': False
                }, room=session_id)
            else:
                # Not the last condition - enable next button
                self.socketio.emit('status_update', {
                    'status': 'Block finished - All objects disabled. Ready for next condition.',
                    'countdown_text': 'TIME EXPIRED - Block Finished',
                    'enable_next': True,
                    'disable_force_next': True,
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': session_data.get('experiment_completed', False),
                    'countdown_active': False
                }, room=session_id)

# Initialize timer manager
timer_manager = TimerManager(manager, socketio)

# Override the manager's timer methods to use our enhanced timer
def enhanced_start_countdown_timer(session_id):
    """Enhanced start countdown timer with socketio integration"""
    session_data = manager.get_session(session_id)
    session_data['condition_start_time'] = time.time()
    session_data['countdown_active'] = True
    
    manager.log_message(session_id, "5-minute countdown timer started for current condition")
    
    # Emit status update with protocol sequence
    socketio.emit('status_update', {
        'status': f"Condition {session_data['current_condition_index'] + 1} Active - Timer Started",
        'countdown_text': 'Time Remaining: 05:00',
        'protocol_sequence': session_data['experiment_sequence'],
        'current_condition_index': session_data['current_condition_index'],
        'experiment_completed': session_data.get('experiment_completed', False),
        'countdown_active': True
    }, room=session_id)
    
    # Start timer loop
    timer_manager.start_timer_loop()

# Override the manager's start_countdown_timer method
manager.start_countdown_timer = enhanced_start_countdown_timer

# Register blueprints
api_routes = create_api_routes(manager, socketio)
config_routes = create_config_routes(manager)
order_routes = create_order_routes(manager)

app.register_blueprint(api_routes)
app.register_blueprint(config_routes)
app.register_blueprint(order_routes)

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
    """Handle client joining a session"""
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        emit('joined_session', {'session_id': session_id})
        logger.info(f"Client joined session: {session_id}")

# Override the manager's log_message method to emit log updates
original_log_message = manager.log_message

def enhanced_log_message(session_id, message):
    """Enhanced log message with socketio integration"""
    full_message = original_log_message(session_id, message)
    
    # Emit log update
    socketio.emit('log_update', {
        'full_message': full_message
    }, room=session_id)
    
    return full_message

manager.log_message = enhanced_log_message

if __name__ == '__main__':
    logger.info("Starting VR Experiment Manager")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 