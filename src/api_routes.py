#!/usr/bin/env python3
"""
API Routes Module
Contains all Flask API endpoints for the VR Experiment Manager.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
import uuid
import logging

logger = logging.getLogger(__name__)

def create_api_routes(manager, socketio):
    """Create and configure API routes"""
    api = Blueprint('api', __name__)
    
    @api.route('/')
    def index():
        """Main interface"""
        return render_template('index.html')
    
    @api.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({'status': 'healthy', 'service': 'VR Experiment Manager'})
    
    @api.route('/api/session/create', methods=['POST'])
    def create_session():
        """Create a new experiment session"""
        session_id = str(uuid.uuid4())
        manager.create_session(session_id)
        return jsonify({'success': True, 'session_id': session_id})
    
    @api.route('/api/session/<session_id>/save', methods=['POST'])
    def save_session(session_id):
        """Save session data"""
        try:
            data = request.json
            group_id = data.get('group_id', '').strip()
            notes = data.get('notes', '').strip()
            
            if not group_id:
                return jsonify({'success': False, 'message': 'Group ID is required'})
            
            success, result = manager.save_session_data(session_id, group_id, notes)
            if success:
                return jsonify({'success': True, 'message': f'Session data saved as {result}'})
            else:
                return jsonify({'success': False, 'message': result})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Failed to save session: {str(e)}'})
    
    @api.route('/api/session/<session_id>/configure', methods=['POST'])
    def configure_experiment(session_id):
        """Configure experiment parameters"""
        try:
            data = request.json
            selected_conditions = data.get('conditions', [])
            selected_objects = data.get('objects', [])
            
            # Validate input
            if not selected_conditions or not selected_objects:
                return jsonify({'success': False, 'message': 'Both conditions and objects are required'})
            
            if len(selected_conditions) != len(selected_objects):
                return jsonify({'success': False, 'message': 'Number of conditions must match number of objects'})
            
            # Check for empty selections
            if any(not cond.strip() for cond in selected_conditions) or any(not obj.strip() for obj in selected_objects):
                return jsonify({'success': False, 'message': 'All condition and object selections must be filled'})
            
            # Validate uniqueness
            if len(set(selected_conditions)) != len(selected_conditions):
                return jsonify({'success': False, 'message': 'Each condition type must be used exactly once'})
            
            if len(set(selected_objects)) != len(selected_objects):
                return jsonify({'success': False, 'message': 'Each object type must be used exactly once'})
            
            # Validate against available types
            available_conditions = set(manager.condition_types)
            available_objects = set(manager.object_types)
            
            if not set(selected_conditions).issubset(available_conditions):
                return jsonify({'success': False, 'message': 'Invalid condition type selected'})
            
            if not set(selected_objects).issubset(available_objects):
                return jsonify({'success': False, 'message': 'Invalid object type selected'})
            
            # Configure experiment
            session_data = manager.get_session(session_id)
            session_data['experiment_sequence'] = []
            condition_count = len(selected_conditions)
            
            for i in range(condition_count):
                session_data['experiment_sequence'].append({
                    "condition_index": i,
                    "condition_type": selected_conditions[i],
                    "object_type": selected_objects[i]
                })
            
            session_data['current_condition_index'] = 0
            session_data['experiment_configured'] = True
            session_data['experiment_completed'] = False  # Reset completion flag
            
            manager.log_message(session_id, "Experiment parameters configured successfully")
            
            # Emit protocol configuration status
            socketio.emit('status_update', {
                'status': 'Protocol initialized. Ready to initiate first condition.',
                'protocol_sequence': session_data['experiment_sequence'],
                'current_condition_index': 0,
                'experiment_configured': True,
                'experiment_completed': False,
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
    
    @api.route('/api/session/<session_id>/start', methods=['POST'])
    def start_condition(session_id):
        """Start current condition"""
        try:
            session_data = manager.get_session(session_id)
            
            # Check if experiment is completed
            if session_data.get('experiment_completed', False):
                return jsonify({'success': False, 'message': 'Experiment has been completed. No more conditions can be started.'})
            
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
                    'experiment_completed': session_data.get('experiment_completed', False),
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
    
    @api.route('/api/session/<session_id>/next', methods=['POST'])
    def next_condition(session_id):
        """Move to next condition"""
        try:
            session_data = manager.get_session(session_id)
            
            # Check if experiment is completed
            if session_data.get('experiment_completed', False):
                return jsonify({'success': False, 'message': 'Experiment has been completed. No more conditions can be started.'})
            
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
                manager.complete_experiment(session_id)
                
                # Emit completion status
                socketio.emit('status_update', {
                    'status': 'Experimental Protocol Completed',
                    'countdown_text': 'Protocol Complete',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': True,
                    'disable_start': True,
                    'disable_next': True,
                    'disable_force_next': True,
                    'countdown_active': False
                }, room=session_id)
                
                return jsonify({
                    'success': True, 
                    'message': 'Experiment completed! You can now save your session data.',
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
                    'experiment_completed': session_data.get('experiment_completed', False),
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
    
    @api.route('/api/session/<session_id>/force-next', methods=['POST'])
    def force_next_condition(session_id):
        """Force move to next condition (override timer)"""
        try:
            session_data = manager.get_session(session_id)
            
            # Check if experiment is completed
            if session_data.get('experiment_completed', False):
                return jsonify({'success': False, 'message': 'Experiment has been completed. No more conditions can be started.'})
            
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
                        'experiment_completed': session_data.get('experiment_completed', False),
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
                        'experiment_completed': session_data.get('experiment_completed', False),
                        'countdown_active': False
                    }, room=session_id)
            
            return jsonify({'success': True, 'message': 'Timer overridden. Ready for next condition.'})
            
        except Exception as e:
            manager.log_message(session_id, f"Error forcing next condition: {str(e)}")
            return jsonify({'success': False, 'message': f'Failed to force next condition: {str(e)}'})
    
    @api.route('/api/session/<session_id>/reset', methods=['POST'])
    def reset_experiment(session_id):
        """Reset experiment"""
        try:
            session_data = manager.get_session(session_id)
            
            # Reset state
            session_data['experiment_sequence'] = []
            session_data['current_condition_index'] = 0
            session_data['experiment_configured'] = False
            session_data['experiment_completed'] = False
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
                'experiment_completed': False,
                'reset_interface': True,
                'countdown_active': False
            }, room=session_id)
            
            return jsonify({'success': True, 'message': 'Experiment reset successfully'})
            
        except Exception as e:
            manager.log_message(session_id, f"Error resetting experiment: {str(e)}")
            return jsonify({'success': False, 'message': f'Failed to reset experiment: {str(e)}'})
    
    @api.route('/api/session/<session_id>/network', methods=['POST'])
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
    
    @api.route('/api/session/<session_id>/status', methods=['GET'])
    def get_session_status(session_id):
        """Get session status"""
        try:
            session_data = manager.get_session(session_id)
            return jsonify({
                'success': True,
                'condition_types': manager.condition_types,
                'object_types': manager.object_types,
                'experiment_configured': session_data['experiment_configured'],
                'experiment_completed': session_data.get('experiment_completed', False),
                'experiment_sequence': session_data['experiment_sequence'],
                'current_condition_index': session_data['current_condition_index'],
                'udp_ip': session_data['udp_ip'],
                'udp_port': session_data['udp_port'],
                'logs': session_data['logs'],
                'metadata': manager.metadata
            })
        except Exception as e:
            return jsonify({'success': False, 'message': f'Failed to get session status: {str(e)}'})
    
    return api 