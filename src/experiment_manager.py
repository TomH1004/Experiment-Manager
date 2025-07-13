#!/usr/bin/env python3
"""
VR Experiment Manager Core Module
Handles experiment configuration, session management, and UDP communication.
"""

import os
import json
import socket
import time
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VRExperimentManager:
    def __init__(self):
        # Configuration directory
        self.config_dir = 'config'
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load metadata configuration first
        self.metadata = self.load_metadata()
        
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
        
        logger.info("VR Experiment Manager initialized")
    
    def load_metadata(self):
        """Load metadata configuration (variable names, etc.)"""
        config_file = os.path.join(self.config_dir, 'metadata.json')
        default_metadata = {
            "variable1_name": "Condition Type",
            "variable2_name": "Object Type",
            "variable1_plural": "Condition Types",
            "variable2_plural": "Object Types",
            "created_at": datetime.now().isoformat(),
            "is_first_time_setup": True
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure all required fields exist
                    for key, value in default_metadata.items():
                        if key not in data:
                            data[key] = value
                    return data
            else:
                # Create default metadata file
                self.save_metadata(default_metadata)
                return default_metadata
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return default_metadata
    
    def save_metadata(self, metadata):
        """Save metadata configuration"""
        config_file = os.path.join(self.config_dir, 'metadata.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            self.metadata = metadata
            logger.info("Metadata configuration saved")
            return True
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
            return False
    
    def load_condition_types(self):
        """Load condition types from configuration file"""
        config_file = os.path.join(self.config_dir, 'condition_types.json')
        
        # Check if this is first-time setup
        if self.metadata.get('is_first_time_setup', True):
            default_conditions = []
        else:
            default_conditions = ["Variable1 A", "Variable1 B", "Variable1 C"]
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('condition_types', default_conditions)
            else:
                # Only create default if not first-time setup
                if not self.metadata.get('is_first_time_setup', True):
                    self.save_condition_types(default_conditions)
                return default_conditions
        except Exception as e:
            logger.error(f"Error loading condition types: {e}")
            return default_conditions
    
    def load_object_types(self):
        """Load object types from configuration file"""
        config_file = os.path.join(self.config_dir, 'object_types.json')
        
        # Check if this is first-time setup
        if self.metadata.get('is_first_time_setup', True):
            default_objects = []
        else:
            default_objects = ["Variable2 1", "Variable2 2", "Variable2 3"]
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('object_types', default_objects)
            else:
                # Only create default if not first-time setup
                if not self.metadata.get('is_first_time_setup', True):
                    self.save_object_types(default_objects)
                return default_objects
        except Exception as e:
            logger.error(f"Error loading object types: {e}")
            return default_objects
    
    def save_condition_types(self, condition_types):
        """Save condition types to configuration file"""
        config_file = os.path.join(self.config_dir, 'condition_types.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'condition_types': condition_types}, f, indent=2)
            self.condition_types = condition_types
            logger.info(f"Condition types saved: {condition_types}")
            return True
        except Exception as e:
            logger.error(f"Error saving condition types: {e}")
            return False
    
    def save_object_types(self, object_types):
        """Save object types to configuration file"""
        config_file = os.path.join(self.config_dir, 'object_types.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'object_types': object_types}, f, indent=2)
            self.object_types = object_types
            logger.info(f"Object types saved: {object_types}")
            return True
        except Exception as e:
            logger.error(f"Error saving object types: {e}")
            return False
    
    def reload_configurations(self):
        """Reload all configurations from files"""
        self.metadata = self.load_metadata()
        self.condition_types = self.load_condition_types()
        self.object_types = self.load_object_types()
        logger.info("All configurations reloaded")
    
    def load_orders(self):
        """Load experimental orders from configuration file"""
        config_file = os.path.join(self.config_dir, 'orders.json')
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('orders', [])
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading orders: {e}")
            return []
    
    def save_orders(self, orders):
        """Save experimental orders to configuration file"""
        config_file = os.path.join(self.config_dir, 'orders.json')
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'orders': orders}, f, indent=2)
            logger.info(f"Orders saved: {len(orders)} orders")
            return True
        except Exception as e:
            logger.error(f"Error saving orders: {e}")
            return False
    
    def generate_all_orders(self):
        """Generate all possible experimental orders using Latin Square design"""
        if not self.condition_types or not self.object_types:
            logger.error("Cannot generate orders: condition types or object types not configured")
            return False
        
        if len(self.condition_types) != len(self.object_types):
            logger.error("Cannot generate orders: condition types and object types must have equal length")
            return False
        
        def generate_latin_square(n):
            """Generate a Latin square of size n x n"""
            square = []
            for i in range(n):
                row = []
                for j in range(n):
                    row.append((i + j) % n)
                square.append(row)
            return square
        
        def rotate_square(square):
            """Rotate a Latin square to generate a new one"""
            n = len(square)
            rotated = []
            for i in range(n):
                row = []
                for j in range(n):
                    row.append(square[(i + 1) % n][j])
                rotated.append(row)
            return rotated
        
        n = len(self.condition_types)
        orders = []
        
        # Generate base Latin square
        base_square = generate_latin_square(n)
        
        # Generate multiple squares by rotation
        squares = [base_square]
        current_square = base_square
        for _ in range(n - 1):
            current_square = rotate_square(current_square)
            squares.append(current_square)
        
        # Convert squares to orders
        order_id = 1
        for square in squares:
            for row_idx, row in enumerate(square):
                order = {
                    'order_id': f'ORD-{order_id:04d}',
                    'sequence': [],
                    'usage_count': 0,
                    'created_at': datetime.now().isoformat()
                }
                
                for col_idx, condition_idx in enumerate(row):
                    order['sequence'].append({
                        'position': col_idx + 1,
                        'condition_type': self.condition_types[condition_idx],
                        'object_type': self.object_types[col_idx]
                    })
                
                orders.append(order)
                order_id += 1
        
        # Save orders
        if self.save_orders(orders):
            logger.info(f"Generated {len(orders)} experimental orders")
            return True
        else:
            return False
    
    def get_orders(self):
        """Get all experimental orders"""
        return self.load_orders()
    
    def mark_order_used(self, order_id, session_id=None):
        """Mark an order as used and increment usage count"""
        orders = self.load_orders()
        
        for order in orders:
            if order['order_id'] == order_id:
                order['usage_count'] += 1
                order['last_used'] = datetime.now().isoformat()
                if session_id:
                    if 'sessions' not in order:
                        order['sessions'] = []
                    order['sessions'].append({
                        'session_id': session_id,
                        'used_at': datetime.now().isoformat()
                    })
                break
        
        self.save_orders(orders)
        logger.info(f"Order {order_id} marked as used by session {session_id}")
        return True
    
    def create_session(self, session_id):
        """Create a new experiment session"""
        self.sessions[session_id] = {
            'group_id': '',
            'notes': '',
            'experiment_sequence': [],
            'current_condition_index': 0,
            'experiment_configured': False,
            'experiment_completed': False,  # Add completion flag
            'condition_start_time': None,
            'countdown_active': False,
            'logs': [],
            'udp_ip': self.default_udp_ip,
            'udp_port': self.default_udp_port,
            'condition_overridden': False,
            'selected_order_id': None,
            'order_marked_used': False
        }
        logger.info(f"Created new session: {session_id}")
        return self.sessions[session_id]
    
    def get_session(self, session_id):
        """Get or create session"""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def log_message(self, session_id, message):
        """Log a message for the session"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        
        session_data = self.get_session(session_id)
        session_data['logs'].append({
            'timestamp': timestamp,
            'message': message,
            'full_message': full_message
        })
        
        # Also log to file
        logger.info(f"Session {session_id}: {message}")
        
        # Emit log update via socketio (will be handled by the main app)
        return full_message
    
    def send_udp_message(self, session_id, message_data):
        """Send UDP message to Unity application"""
        session_data = self.get_session(session_id)
        
        try:
            # Convert message to JSON
            json_message = json.dumps(message_data)
            
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            # Send message
            sock.sendto(json_message.encode('utf-8'), (session_data['udp_ip'], session_data['udp_port']))
            sock.close()
            
            self.log_message(session_id, f"Sent UDP message to {session_data['udp_ip']}:{session_data['udp_port']}: {json_message}")
            return True
            
        except Exception as e:
            self.log_message(session_id, f"Failed to send UDP message: {str(e)}")
            return False
    
    def update_network_settings(self, session_id, udp_ip, udp_port):
        """Update network settings for a session"""
        if not udp_ip or udp_port <= 0 or udp_port > 65535:
            return False, "Invalid IP address or port number"
        
        session_data = self.get_session(session_id)
        session_data['udp_ip'] = udp_ip
        session_data['udp_port'] = udp_port
        
        self.log_message(session_id, f"Network settings updated: {udp_ip}:{udp_port}")
        return True, "Network settings updated successfully"
    
    def start_countdown_timer(self, session_id):
        """Start the 5-minute countdown timer for the current condition"""
        session_data = self.get_session(session_id)
        session_data['condition_start_time'] = time.time()
        session_data['countdown_active'] = True
        
        self.log_message(session_id, "5-minute countdown timer started for current condition")
        
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
        
        self.send_udp_message(session_id, message_data)
        
        # Return session_id so the main app can emit socketio events
        return session_id
    
    def complete_experiment(self, session_id):
        """Mark experiment as completed"""
        session_data = self.get_session(session_id)
        session_data['experiment_completed'] = True
        self.log_message(session_id, "Experiment completed - no more conditions can be started")
    
    def save_session_data(self, session_id, group_id, notes):
        """Save session data to a text file"""
        try:
            session_data = self.get_session(session_id)
            
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Create filename with group ID and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"VR_Experiment_{group_id}_{timestamp}.txt"
            filepath = os.path.join('data', filename)
            
            # Prepare data to save
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("VR Experiment Session Data\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Group ID: {group_id}\n")
                f.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Current Condition Index: {session_data['current_condition_index']}\n\n")
                
                f.write("Experiment Sequence:\n")
                f.write("-" * 20 + "\n")
                for i, condition in enumerate(session_data['experiment_sequence']):
                    status = "COMPLETED" if i < session_data['current_condition_index'] else "PENDING"
                    f.write(f"Condition {i + 1}: {condition['condition_type']} ({condition['object_type']}) [{status}]\n")
                
                f.write(f"\nSupervisor Notes:\n")
                f.write("-" * 20 + "\n")
                f.write(f"{notes}\n\n")
                
                f.write("System Event Log:\n")
                f.write("-" * 20 + "\n")
                for log_entry in session_data['logs']:
                    f.write(f"{log_entry['full_message']}\n")
            
            self.log_message(session_id, f"Session data saved to {filename}")
            return True, filename
            
        except Exception as e:
            self.log_message(session_id, f"Error saving session data: {str(e)}")
            return False, str(e) 