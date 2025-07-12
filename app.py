#!/usr/bin/env python3
"""
VR Experiment Supervisor Web Application
Flask backend for controlling Unity VR experiments via UDP broadcast messages.
"""

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room
import socket
import json
import threading
import time
from datetime import datetime
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

class VRExperimentManager:
    def __init__(self):
        # Configuration directory
        self.config_dir = 'config'
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load experiment configuration from files
        self.condition_types = self.load_condition_types()
        self.object_types = self.load_object_types()
        
        # Session data
        self.sessions = {}
        
        # Default UDP settings
        self.default_udp_ip = "10.195.83.255"
        self.default_udp_port = 1221
        
        # Timer thread
        self.timer_thread = None
        self.timer_active = False
    
    def load_condition_types(self):
        """Load condition types from configuration file"""
        config_file = os.path.join(self.config_dir, 'condition_types.json')
        default_conditions = ["Helpful", "Demotivating", "Control"]
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('condition_types', default_conditions)
            else:
                # Create default configuration file
                self.save_condition_types(default_conditions)
                return default_conditions
        except Exception as e:
            print(f"Error loading condition types: {e}")
            return default_conditions
    
    def load_object_types(self):
        """Load object types from configuration file"""
        config_file = os.path.join(self.config_dir, 'object_types.json')
        default_objects = ["Brick", "Paperclip", "Rope"]
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('object_types', default_objects)
            else:
                # Create default configuration file
                self.save_object_types(default_objects)
                return default_objects
        except Exception as e:
            print(f"Error loading object types: {e}")
            return default_objects
    
    def save_condition_types(self, condition_types):
        """Save condition types to configuration file"""
        config_file = os.path.join(self.config_dir, 'condition_types.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'condition_types': condition_types}, f, indent=2)
            self.condition_types = condition_types
            return True
        except Exception as e:
            print(f"Error saving condition types: {e}")
            return False
    
    def save_object_types(self, object_types):
        """Save object types to configuration file"""
        config_file = os.path.join(self.config_dir, 'object_types.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'object_types': object_types}, f, indent=2)
            self.object_types = object_types
            return True
        except Exception as e:
            print(f"Error saving object types: {e}")
            return False
    
    def reload_configurations(self):
        """Reload all configurations from files"""
        self.condition_types = self.load_condition_types()
        self.object_types = self.load_object_types()
        return True
    
    def create_session(self, session_id):
        """Create a new experiment session"""
        self.sessions[session_id] = {
            'group_id': '',
            'notes': '',
            'experiment_sequence': [],
            'current_condition_index': 0,
            'experiment_configured': False,
            'condition_start_time': None,
            'countdown_active': False,
            'logs': [],
            'udp_ip': self.default_udp_ip,
            'udp_port': self.default_udp_port,
            'condition_overridden': False
        }
        return self.sessions[session_id]
    
    def get_session(self, session_id):
        """Get or create session"""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def log_message(self, session_id, message):
        """Add a timestamped message to the session log"""
        session_data = self.get_session(session_id)
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'full_message': f"[{timestamp}] {message}"
        }
        session_data['logs'].append(log_entry)
        
        # Emit to all clients for this session
        socketio.emit('log_update', log_entry, room=session_id)
    
    def send_udp_message(self, session_id, message_data):
        """Send UDP broadcast message"""
        try:
            session_data = self.get_session(session_id)
            udp_ip = session_data['udp_ip']
            udp_port = session_data['udp_port']
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Convert message to JSON
            json_message = json.dumps(message_data)
            
            # Send message
            sock.sendto(json_message.encode('utf-8'), (udp_ip, udp_port))
            sock.close()
            
            self.log_message(session_id, f"Sent UDP message to {udp_ip}:{udp_port}: {json_message}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to send UDP message: {str(e)}"
            self.log_message(session_id, f"ERROR: {error_msg}")
            return False
    
    def update_network_settings(self, session_id, udp_ip, udp_port):
        """Update network settings for a session"""
        try:
            session_data = self.get_session(session_id)
            
            # Validate IP address format
            import ipaddress
            try:
                ipaddress.ip_address(udp_ip)
            except ValueError:
                return False, "Invalid IP address format"
            
            # Validate port range
            if not (1 <= udp_port <= 65535):
                return False, "Port must be between 1 and 65535"
            
            session_data['udp_ip'] = udp_ip
            session_data['udp_port'] = udp_port
            
            self.log_message(session_id, f"Network settings updated: {udp_ip}:{udp_port}")
            return True, "Network settings updated successfully"
            
        except Exception as e:
            error_msg = f"Failed to update network settings: {str(e)}"
            self.log_message(session_id, f"ERROR: {error_msg}")
            return False, error_msg
    
    def start_countdown_timer(self, session_id):
        """Start the 5-minute countdown timer for the current condition"""
        session_data = self.get_session(session_id)
        session_data['condition_start_time'] = time.time()
        session_data['countdown_active'] = True
        
        self.log_message(session_id, "5-minute countdown timer started for current condition")
        
        # Emit status update with protocol sequence
        socketio.emit('status_update', {
            'status': f"Condition {session_data['current_condition_index'] + 1} Active - Timer Started",
            'countdown_text': 'Time Remaining: 05:00',
            'protocol_sequence': session_data['experiment_sequence'],
            'current_condition_index': session_data['current_condition_index'],
            'countdown_active': True
        }, room=session_id)
        
        # Start timer thread
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
            self.timer_thread.start()
    
    def _timer_loop(self):
        """Timer loop that runs in a separate thread"""
        while True:
            active_sessions = []
            
            for session_id, session_data in self.sessions.items():
                if session_data['countdown_active'] and session_data['condition_start_time'] is not None:
                    elapsed_time = time.time() - session_data['condition_start_time']
                    remaining_time = max(0, 300 - elapsed_time)  # 300 seconds = 5 minutes
                    
                    if remaining_time > 0:
                        minutes = int(remaining_time // 60)
                        seconds = int(remaining_time % 60)
                        countdown_text = f"Time Remaining: {minutes:02d}:{seconds:02d}"
                        
                        # Emit countdown update
                        socketio.emit('countdown_update', {
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
        session_data = self.get_session(session_id)
        
        self.log_message(session_id, "5-minute timer expired - sending disable_all command")
        
        # Send command to Unity to disable all objects and avatars
        message_data = {
            "command": "disable_all",
            "reason": "timer_expired"
        }
        
        if self.send_udp_message(session_id, message_data):
            # Emit comprehensive status update
            socketio.emit('status_update', {
                'status': 'Block finished - All objects disabled. Ready for next condition.',
                'countdown_text': 'TIME EXPIRED - Block Finished',
                'enable_next': session_data['current_condition_index'] < len(session_data['experiment_sequence']) - 1,
                'protocol_sequence': session_data['experiment_sequence'],
                'current_condition_index': session_data['current_condition_index'],
                'countdown_active': False
            }, room=session_id)
    
    def save_session_data(self, session_id, group_id, notes):
        """Save session data to a text file"""
        try:
            session_data = self.get_session(session_id)
            session_data['group_id'] = group_id
            session_data['notes'] = notes
            
            if not group_id.strip():
                return False, "Please enter a Group ID before saving."
            
            if not session_data['experiment_configured']:
                return False, "Please configure the experiment before saving."
            
            # Create filename with group ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"VR_Experiment_{group_id}_{timestamp}.txt"
            
            # Ensure data directory exists
            os.makedirs('data', exist_ok=True)
            filepath = os.path.join('data', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"VR Experiment Session Data\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Group ID: {group_id}\n")
                f.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Current Condition Index: {session_data['current_condition_index']}\n\n")
                
                f.write(f"Experiment Sequence:\n")
                f.write(f"-" * 20 + "\n")
                for i, condition in enumerate(session_data['experiment_sequence']):
                    status = ""
                    if i < session_data['current_condition_index']:
                        status = " [COMPLETED]"
                    elif i == session_data['current_condition_index']:
                        status = " [CURRENT]"
                    else:
                        status = " [PENDING]"
                    
                    f.write(f"Condition {i+1}: {condition['condition_type']} ({condition['object_type']}){status}\n")
                
                f.write(f"\nSupervisor Notes:\n")
                f.write(f"-" * 20 + "\n")
                if notes:
                    f.write(f"{notes}\n")
                else:
                    f.write("No notes provided.\n")
                
                # Add system event log
                f.write(f"\nSystem Event Log:\n")
                f.write(f"-" * 20 + "\n")
                if session_data['logs']:
                    for log_entry in session_data['logs']:
                        f.write(f"{log_entry['full_message']}\n")
                else:
                    f.write("No system events recorded.\n")
            
            self.log_message(session_id, f"Session data saved to: {filename}")
            return True, f"Session data saved to: {filename}"
            
        except Exception as e:
            error_msg = f"Failed to save session data: {str(e)}"
            self.log_message(session_id, f"ERROR: {error_msg}")
            return False, error_msg

    def emit_protocol_status(self, session_id, status_message):
        """Emit protocol status update with current state"""
        session_data = self.get_session(session_id)
        socketio.emit('protocol_status_update', {
            'status': status_message,
            'protocol_sequence': session_data['experiment_sequence'],
            'current_condition_index': session_data['current_condition_index'],
            'experiment_configured': session_data['experiment_configured']
        }, room=session_id)

# Global manager instance
manager = VRExperimentManager()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new session"""
    session_id = str(uuid.uuid4())
    session_data = manager.create_session(session_id)
    manager.log_message(session_id, "Application started. Ready to configure experiment.")
    return jsonify({'session_id': session_id, 'success': True})

@app.route('/api/session/<session_id>/save', methods=['POST'])
def save_session(session_id):
    """Save session data"""
    data = request.json
    success, message = manager.save_session_data(session_id, data['group_id'], data['notes'])
    return jsonify({'success': success, 'message': message})

@app.route('/api/session/<session_id>/configure', methods=['POST'])
def configure_experiment(session_id):
    """Configure experiment parameters"""
    try:
        data = request.json
        session_data = manager.get_session(session_id)
        
        selected_conditions = data['conditions']
        selected_objects = data['objects']
        
        # Get current configuration counts
        condition_count = len(manager.condition_types)
        object_count = len(manager.object_types)
        
        # Validate that all values are provided
        if any(not cond for cond in selected_conditions) or any(not obj for obj in selected_objects):
            return jsonify({'success': False, 'message': 'Please select condition types and objects for all conditions.'})
        
        # Validate that we have the right number of selections
        if len(selected_conditions) != condition_count:
            return jsonify({'success': False, 'message': f'Expected {condition_count} condition selections, got {len(selected_conditions)}.'})
        
        if len(selected_objects) != object_count:
            return jsonify({'success': False, 'message': f'Expected {object_count} object selections, got {len(selected_objects)}.'})
        
        # Validate that each condition type is used exactly once
        if len(set(selected_conditions)) != condition_count or set(selected_conditions) != set(manager.condition_types):
            return jsonify({'success': False, 'message': 'Each condition type must be used exactly once.'})
        
        # Validate that each object type is used exactly once
        if len(set(selected_objects)) != object_count or set(selected_objects) != set(manager.object_types):
            return jsonify({'success': False, 'message': 'Each object type must be used exactly once.'})
        
        # Create experiment sequence
        session_data['experiment_sequence'] = []
        for i in range(condition_count):
            session_data['experiment_sequence'].append({
                "condition_index": i,
                "condition_type": selected_conditions[i],
                "object_type": selected_objects[i]
            })
        
        session_data['current_condition_index'] = 0
        session_data['experiment_configured'] = True
        
        manager.log_message(session_id, "Experiment parameters configured successfully")
        
        # Emit protocol configuration status
        socketio.emit('status_update', {
            'status': 'Protocol initialized. Ready to initiate first condition.',
            'protocol_sequence': session_data['experiment_sequence'],
            'current_condition_index': 0,
            'experiment_configured': True,
            'enable_start': True,
            'countdown_active': False
        }, room=session_id)
        
        return jsonify({
            'success': True, 
            'message': 'Experiment parameters set successfully!',
            'sequence': session_data['experiment_sequence']
        })
        
    except Exception as e:
        manager.log_message(session_id, f"Error configuring experiment: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to configure experiment: {str(e)}'})

@app.route('/api/session/<session_id>/start', methods=['POST'])
def start_condition(session_id):
    """Start current condition"""
    try:
        session_data = manager.get_session(session_id)
        
        if not session_data['experiment_configured'] or session_data['current_condition_index'] >= len(session_data['experiment_sequence']):
            return jsonify({'success': False, 'message': 'No valid condition to start'})
        
        current_condition = session_data['experiment_sequence'][session_data['current_condition_index']]
        
        message_data = {
            "command": "start_condition",
            "condition_type": current_condition["condition_type"],
            "object_type": current_condition["object_type"],
            "condition_index": session_data['current_condition_index']
        }
        
        if manager.send_udp_message(session_id, message_data):
            condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
            manager.start_countdown_timer(session_id)
            
            # Emit detailed status update
            socketio.emit('status_update', {
                'status': f"Active Condition: {condition_name}",
                'countdown_text': 'Time Remaining: 05:00',
                'protocol_sequence': session_data['experiment_sequence'],
                'current_condition_index': session_data['current_condition_index'],
                'disable_start': True,
                'enable_force_next': True,
                'countdown_active': True
            }, room=session_id)
            
            return jsonify({
                'success': True, 
                'message': f'Started condition: {condition_name}',
                'condition_name': condition_name
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to send UDP message'})
            
    except Exception as e:
        manager.log_message(session_id, f"Error starting condition: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to start condition: {str(e)}'})

@app.route('/api/session/<session_id>/next', methods=['POST'])
def next_condition(session_id):
    """Move to next condition"""
    try:
        session_data = manager.get_session(session_id)
        
        if not session_data['experiment_configured']:
            return jsonify({'success': False, 'message': 'Experiment not configured'})
        
        # If condition was overridden, don't increment index, just start current condition
        if not session_data['condition_overridden']:
            session_data['current_condition_index'] += 1
        else:
            # Reset the override flag
            session_data['condition_overridden'] = False
        
        if session_data['current_condition_index'] >= len(session_data['experiment_sequence']):
            # Experiment completed
            manager.log_message(session_id, "Experiment completed")
            
            # Emit completion status
            socketio.emit('status_update', {
                'status': 'Experimental Protocol Completed',
                'countdown_text': 'Protocol Complete',
                'protocol_sequence': session_data['experiment_sequence'],
                'current_condition_index': session_data['current_condition_index'],
                'experiment_completed': True,
                'countdown_active': False
            }, room=session_id)
            
            return jsonify({
                'success': True, 
                'message': 'Experiment completed!',
                'completed': True
            })
        
        current_condition = session_data['experiment_sequence'][session_data['current_condition_index']]
        
        message_data = {
            "command": "next_condition",
            "condition_type": current_condition["condition_type"],
            "object_type": current_condition["object_type"],
            "condition_index": session_data['current_condition_index']
        }
        
        if manager.send_udp_message(session_id, message_data):
            condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
            manager.start_countdown_timer(session_id)
            
            # Emit detailed status update
            socketio.emit('status_update', {
                'status': f"Active Condition: {condition_name}",
                'countdown_text': 'Time Remaining: 05:00',
                'protocol_sequence': session_data['experiment_sequence'],
                'current_condition_index': session_data['current_condition_index'],
                'disable_next': True,
                'enable_force_next': True,
                'countdown_active': True
            }, room=session_id)
            
            return jsonify({
                'success': True, 
                'message': f'Started condition: {condition_name}',
                'condition_name': condition_name,
                'completed': False
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to send UDP message'})
            
    except Exception as e:
        manager.log_message(session_id, f"Error moving to next condition: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to move to next condition: {str(e)}'})

@app.route('/api/session/<session_id>/force-next', methods=['POST'])
def force_next_condition(session_id):
    """Force move to next condition (override timer)"""
    try:
        session_data = manager.get_session(session_id)
        
        # Stop the current timer
        session_data['countdown_active'] = False
        manager.log_message(session_id, "Timer manually overridden by supervisor")
        
        # Send disable_all command to Unity
        message_data = {
            "command": "disable_all",
            "reason": "timer_overridden"
        }
        
        if manager.send_udp_message(session_id, message_data):
            # Move to next condition index for status display
            next_condition_index = session_data['current_condition_index'] + 1
            
            if next_condition_index < len(session_data['experiment_sequence']):
                # Update session to next condition index
                session_data['current_condition_index'] = next_condition_index
                session_data['condition_overridden'] = True
                
                # There is a next condition - show it as "Ready"
                socketio.emit('status_update', {
                    'status': 'Timer overridden - Ready for next condition.',
                    'countdown_text': 'Timer Overridden',
                    'enable_next': True,
                    'disable_force_next': True,
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': next_condition_index,
                    'countdown_active': False
                }, room=session_id)
            else:
                # No more conditions - experiment ready to complete
                session_data['condition_overridden'] = True
                socketio.emit('status_update', {
                    'status': 'Timer overridden - Ready to complete experiment.',
                    'countdown_text': 'Timer Overridden',
                    'enable_next': True,
                    'disable_force_next': True,
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'countdown_active': False
                }, room=session_id)
        
        return jsonify({'success': True, 'message': 'Timer overridden. Ready for next condition.'})
        
    except Exception as e:
        manager.log_message(session_id, f"Error forcing next condition: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to force next condition: {str(e)}'})

@app.route('/api/session/<session_id>/reset', methods=['POST'])
def reset_experiment(session_id):
    """Reset experiment"""
    try:
        session_data = manager.get_session(session_id)
        
        # Reset state
        session_data['experiment_sequence'] = []
        session_data['current_condition_index'] = 0
        session_data['experiment_configured'] = False
        session_data['countdown_active'] = False
        session_data['condition_start_time'] = None
        session_data['condition_overridden'] = False
        
        manager.log_message(session_id, "Experiment reset. Ready for new configuration.")
        
        # Emit reset status
        socketio.emit('status_update', {
            'status': 'Standby - Awaiting Configuration',
            'countdown_text': '',
            'protocol_sequence': [],
            'current_condition_index': 0,
            'experiment_configured': False,
            'reset_interface': True,
            'countdown_active': False
        }, room=session_id)
        
        return jsonify({'success': True, 'message': 'Experiment reset successfully'})
        
    except Exception as e:
        manager.log_message(session_id, f"Error resetting experiment: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to reset experiment: {str(e)}'})

@app.route('/api/session/<session_id>/network', methods=['POST'])
def update_network_settings(session_id):
    """Update network settings"""
    try:
        data = request.json
        udp_ip = data.get('udp_ip', '').strip()
        udp_port = int(data.get('udp_port', 0))
        
        success, message = manager.update_network_settings(session_id, udp_ip, udp_port)
        return jsonify({'success': success, 'message': message})
        
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid port number'})
    except Exception as e:
        manager.log_message(session_id, f"Error updating network settings: {str(e)}")
        return jsonify({'success': False, 'message': f'Failed to update network settings: {str(e)}'})

@app.route('/api/session/<session_id>/status', methods=['GET'])
def get_session_status(session_id):
    """Get current session status"""
    session_data = manager.get_session(session_id)
    
    return jsonify({
        'session_id': session_id,
        'experiment_configured': session_data['experiment_configured'],
        'current_condition_index': session_data['current_condition_index'],
        'experiment_sequence': session_data['experiment_sequence'],
        'countdown_active': session_data['countdown_active'],
        'logs': session_data['logs'][-50:],  # Last 50 log entries
        'condition_types': manager.condition_types,
        'object_types': manager.object_types,
        'udp_ip': session_data['udp_ip'],
        'udp_port': session_data['udp_port']
    })

# Configuration Management API Endpoints
@app.route('/api/config/condition-types', methods=['GET'])
def get_condition_types():
    """Get available condition types"""
    return jsonify({
        'success': True,
        'condition_types': manager.condition_types
    })

@app.route('/api/config/condition-types', methods=['PUT'])
def update_condition_types():
    """Update available condition types"""
    try:
        data = request.json
        condition_types = data.get('condition_types', [])
        
        # Validate input
        if not condition_types or not isinstance(condition_types, list):
            return jsonify({'success': False, 'message': 'Invalid condition types format'})
        
        # Remove empty strings and duplicates
        condition_types = list(dict.fromkeys([ct.strip() for ct in condition_types if ct.strip()]))
        
        if len(condition_types) == 0:
            return jsonify({'success': False, 'message': 'At least one condition type is required'})
        
        if manager.save_condition_types(condition_types):
            return jsonify({
                'success': True,
                'message': 'Condition types updated successfully',
                'condition_types': condition_types
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save condition types'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating condition types: {str(e)}'})

@app.route('/api/config/object-types', methods=['GET'])
def get_object_types():
    """Get available object types"""
    return jsonify({
        'success': True,
        'object_types': manager.object_types
    })

@app.route('/api/config/object-types', methods=['PUT'])
def update_object_types():
    """Update available object types"""
    try:
        data = request.json
        object_types = data.get('object_types', [])
        
        # Validate input
        if not object_types or not isinstance(object_types, list):
            return jsonify({'success': False, 'message': 'Invalid object types format'})
        
        # Remove empty strings and duplicates
        object_types = list(dict.fromkeys([ot.strip() for ot in object_types if ot.strip()]))
        
        if len(object_types) == 0:
            return jsonify({'success': False, 'message': 'At least one object type is required'})
        
        if manager.save_object_types(object_types):
            return jsonify({
                'success': True,
                'message': 'Object types updated successfully',
                'object_types': object_types
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save object types'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating object types: {str(e)}'})

@app.route('/api/config/reload', methods=['POST'])
def reload_configurations():
    """Reload all configurations from files"""
    try:
        manager.reload_configurations()
        return jsonify({
            'success': True,
            'message': 'Configurations reloaded successfully',
            'condition_types': manager.condition_types,
            'object_types': manager.object_types
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error reloading configurations: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join_session')
def handle_join_session(data):
    """Handle client joining a session"""
    session_id = data['session_id']
    join_room(session_id)
    emit('joined_session', {'session_id': session_id})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 