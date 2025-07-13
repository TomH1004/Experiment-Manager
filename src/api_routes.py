#!/usr/bin/env python3
"""
API Routes Module
Contains all Flask API endpoints for the VR Experiment Manager.
"""

from flask import Blueprint, render_template, request, jsonify
from flask_socketio import emit
import uuid
import logging
import time

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
                'countdown_active': False,
                'practice_trial': False,
                'enable_start': True,
                'enable_practice': True
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
                manager.log_message(session_id, "Attempt to start condition on completed experiment")
                return jsonify({'success': False, 'message': 'Experiment has been completed. No more conditions can be started.'})
            
            # Check if experiment is configured
            if not session_data['experiment_configured']:
                manager.log_message(session_id, "Attempt to start condition on unconfigured experiment")
                return jsonify({'success': False, 'message': 'Experiment not configured'})
            
            # Check if current condition index is valid
            if session_data['current_condition_index'] >= len(session_data['experiment_sequence']):
                manager.log_message(session_id, f"Attempt to start invalid condition index {session_data['current_condition_index']} (max: {len(session_data['experiment_sequence']) - 1})")
                return jsonify({'success': False, 'message': 'No valid condition to start - experiment may be completed'})
            
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
                    'experiment_configured': True,
                    'countdown_active': True,
                    'practice_trial': False
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
    
    @api.route('/api/session/<session_id>/practice', methods=['POST'])
    def start_practice_trial(session_id):
        """Start a practice trial"""
        try:
            session_data = manager.get_session(session_id)
            
            if not session_data['experiment_configured']:
                return jsonify({'success': False, 'message': 'Experiment not configured'})
            
            # Use the first condition for practice trial
            first_condition = session_data['experiment_sequence'][0]
            
            message_data = {
                "command": "start_condition",
                "condition_type": first_condition["condition_type"],
                "object_type": first_condition["object_type"],
                "condition_index": -1,  # -1 indicates practice trial
                "practice_trial": True
            }
            
            if manager.send_udp_message(session_id, message_data):
                condition_name = f"{first_condition['condition_type']} ({first_condition['object_type']})"
                
                # Set practice trial state
                session_data['practice_trial_active'] = True
                session_data['practice_start_time'] = time.time()
                
                manager.log_message(session_id, f"Practice trial started: {condition_name}")
                
                # Start practice timer
                manager.start_countdown_timer(session_id, practice_mode=True)
                
                # Emit practice trial status
                socketio.emit('status_update', {
                    'status': f"Practice Trial: {condition_name}",
                    'countdown_text': 'Practice Time: 05:00',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': -1,
                    'experiment_completed': False,
                    'experiment_configured': True,
                    'practice_trial': True,
                    'countdown_active': True
                }, room=session_id)
                
                return jsonify({
                    'success': True,
                    'message': f'Practice trial started: {condition_name}',
                    'condition_name': condition_name
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to send UDP message'})
                
        except Exception as e:
            manager.log_message(session_id, f"Error starting practice trial: {str(e)}")
            return jsonify({'success': False, 'message': f'Failed to start practice trial: {str(e)}'})
    
    @api.route('/api/session/<session_id>/restart', methods=['POST'])
    def restart_condition(session_id):
        """Restart the current condition"""
        try:
            session_data = manager.get_session(session_id)
            
            if not session_data['experiment_configured']:
                return jsonify({'success': False, 'message': 'Experiment not configured'})
            
            # Check if in practice trial
            if session_data.get('practice_trial_active', False):
                # Restart practice trial
                first_condition = session_data['experiment_sequence'][0]
                message_data = {
                    "command": "start_condition",
                    "condition_type": first_condition["condition_type"],
                    "object_type": first_condition["object_type"],
                    "condition_index": -1,
                    "practice_trial": True
                }
                condition_name = f"{first_condition['condition_type']} ({first_condition['object_type']})"
                status_message = f"Practice Trial: {condition_name}"
                countdown_text = 'Practice Time: 05:00'
                practice_mode = True
            else:
                # Restart current experimental condition
                if session_data['current_condition_index'] >= len(session_data['experiment_sequence']):
                    return jsonify({'success': False, 'message': 'No active condition to restart'})
                
                current_condition = session_data['experiment_sequence'][session_data['current_condition_index']]
                message_data = {
                    "command": "start_condition",
                    "condition_type": current_condition["condition_type"],
                    "object_type": current_condition["object_type"],
                    "condition_index": session_data['current_condition_index']
                }
                condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
                status_message = f"Restarted Condition: {condition_name}"
                countdown_text = 'Time Remaining: 05:00'
                practice_mode = False
            
            if manager.send_udp_message(session_id, message_data):
                # Reset timer
                session_data['countdown_active'] = False
                manager.start_countdown_timer(session_id, practice_mode=practice_mode)
                
                manager.log_message(session_id, f"Condition restarted: {condition_name}")
                
                # Emit restart status
                socketio.emit('status_update', {
                    'status': status_message,
                    'countdown_text': countdown_text,
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': False,
                    'experiment_configured': True,
                    'practice_trial': practice_mode,
                    'countdown_active': True
                }, room=session_id)
                
                return jsonify({
                    'success': True,
                    'message': f'Condition restarted: {condition_name}',
                    'condition_name': condition_name
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to send UDP message'})
                
        except Exception as e:
            manager.log_message(session_id, f"Error restarting condition: {str(e)}")
            return jsonify({'success': False, 'message': f'Failed to restart condition: {str(e)}'})
    
    @api.route('/api/session/<session_id>/next', methods=['POST'])
    def next_condition(session_id):
        """Move to next condition (without starting it)"""
        try:
            session_data = manager.get_session(session_id)
            
            # End practice trial if active
            if session_data.get('practice_trial_active', False):
                session_data['practice_trial_active'] = False
                session_data['practice_start_time'] = None
                session_data['countdown_active'] = False
                
                manager.log_message(session_id, "Practice trial ended")
                
                # Emit status to enable start condition
                socketio.emit('status_update', {
                    'status': 'Practice trial completed - Ready to start experiment',
                    'countdown_text': 'Practice Complete',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': 0,
                    'experiment_completed': False,
                    'experiment_configured': True,
                    'practice_trial': False,
                    'countdown_active': False,
                    'enable_start': True,
                    'enable_practice': True
                }, room=session_id)
                
                return jsonify({
                    'success': True,
                    'message': 'Practice trial completed. Ready to start experiment.',
                    'completed': False
                })
            
            # Check if experiment is completed
            if session_data.get('experiment_completed', False):
                return jsonify({'success': False, 'message': 'Experiment has been completed. No more conditions can be started.'})
            
            if not session_data['experiment_configured']:
                return jsonify({'success': False, 'message': 'Experiment not configured'})
            
            # Stop any active countdown
            session_data['countdown_active'] = False
            
            # Log current state
            manager.log_message(session_id, f"Next condition requested. Current index: {session_data['current_condition_index']}, Sequence length: {len(session_data['experiment_sequence'])}")
            
            # Increment condition index
            session_data['current_condition_index'] += 1
            manager.log_message(session_id, f"Incremented condition index to: {session_data['current_condition_index']}")
            
            # Check if we've reached the end of the experiment
            if session_data['current_condition_index'] >= len(session_data['experiment_sequence']):
                # Experiment completed
                manager.log_message(session_id, f"Experiment completed - condition index {session_data['current_condition_index']} >= sequence length {len(session_data['experiment_sequence'])}")
                manager.complete_experiment(session_id)
                
                # Emit completion status
                socketio.emit('status_update', {
                    'status': 'Experimental Protocol Completed',
                    'countdown_text': 'Protocol Complete',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': True,
                    'experiment_configured': True,
                    'practice_trial': False,
                    'countdown_active': False
                }, room=session_id)
                
                return jsonify({
                    'success': True, 
                    'message': 'Experiment completed! You can now save your session data.',
                    'completed': True
                })
            
            # Prepare next condition (but don't start it)
            current_condition = session_data['experiment_sequence'][session_data['current_condition_index']]
            condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
            
            manager.log_message(session_id, f"Advanced to condition {session_data['current_condition_index'] + 1}: {condition_name}")
            
            # Send status update for ready-to-start state
            socketio.emit('status_update', {
                'status': f"Ready for Condition {session_data['current_condition_index'] + 1}: {condition_name}",
                'countdown_text': 'Ready to Start',
                'protocol_sequence': session_data['experiment_sequence'],
                'current_condition_index': session_data['current_condition_index'],
                'experiment_completed': False,
                'experiment_configured': True,
                'countdown_active': False,
                'practice_trial': False,
                'enable_start': True
            }, room=session_id)
            
            return jsonify({
                'success': True, 
                'message': f'Ready for condition: {condition_name}. Click "Initiate Condition" to start.',
                'condition_name': condition_name,
                'completed': False
            })
                
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
                # Check if this was a practice trial
                if session_data.get('practice_trial_active', False):
                    # Practice trial was overridden - end it and return to experiment ready state
                    session_data['practice_trial_active'] = False
                    session_data['practice_start_time'] = None
                    
                    manager.log_message(session_id, "Practice trial timer overridden - returning to experiment ready state")
                    
                    socketio.emit('status_update', {
                        'status': 'Practice trial timer overridden - Ready to start experiment',
                        'countdown_text': 'Practice Overridden',
                        'protocol_sequence': session_data['experiment_sequence'],
                        'current_condition_index': 0,  # Reset to first condition
                        'experiment_completed': False,
                        'experiment_configured': True,
                        'practice_trial': False,
                        'countdown_active': False,
                        'enable_start': True,
                        'enable_practice': True
                    }, room=session_id)
                    
                    return jsonify({'success': True, 'message': 'Practice trial timer overridden. Ready to start experiment.'})
                
                # Regular condition override - automatically advance to next condition
                session_data['current_condition_index'] += 1
                manager.log_message(session_id, f"Timer overridden - advanced to condition index {session_data['current_condition_index']}")
                
                # Check if we've reached the end of the experiment
                if session_data['current_condition_index'] >= len(session_data['experiment_sequence']):
                    # Experiment completed
                    manager.log_message(session_id, f"Experiment completed after timer override - condition index {session_data['current_condition_index']} >= sequence length {len(session_data['experiment_sequence'])}")
                    manager.complete_experiment(session_id)
                    
                    # Emit completion status
                    socketio.emit('status_update', {
                        'status': 'Timer overridden - Experiment completed!',
                        'countdown_text': 'Experiment Complete',
                        'protocol_sequence': session_data['experiment_sequence'],
                        'current_condition_index': session_data['current_condition_index'],
                        'experiment_completed': True,
                        'experiment_configured': True,
                        'practice_trial': False,
                        'countdown_active': False
                    }, room=session_id)
                    
                    return jsonify({
                        'success': True, 
                        'message': 'Timer overridden - Experiment completed!',
                        'completed': True
                    })
                
                # Prepare next condition (ready to start)
                current_condition = session_data['experiment_sequence'][session_data['current_condition_index']]
                condition_name = f"{current_condition['condition_type']} ({current_condition['object_type']})"
                
                manager.log_message(session_id, f"Timer overridden - ready for condition {session_data['current_condition_index'] + 1}: {condition_name}")
                
                # Emit status for ready-to-start state
                socketio.emit('status_update', {
                    'status': f"Timer overridden - Ready for Condition {session_data['current_condition_index'] + 1}: {condition_name}",
                    'countdown_text': 'Ready to Start',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': False,
                    'experiment_configured': True,
                    'practice_trial': False,
                    'countdown_active': False,
                    'enable_start': True
                }, room=session_id)
                
                return jsonify({
                    'success': True, 
                    'message': f'Timer overridden - Ready for condition: {condition_name}. Click "Initiate Condition" to start.',
                    'condition_name': condition_name
                })
            
            return jsonify({'success': False, 'message': 'Failed to send UDP message'})
            
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
            
            manager.log_message(session_id, "Experiment reset. Ready for new configuration.")
            
            # Emit reset status
            socketio.emit('status_update', {
                'status': 'Standby - Awaiting Configuration',
                'countdown_text': '',
                'protocol_sequence': [],
                'current_condition_index': 0,
                'experiment_configured': False,
                'experiment_completed': False,
                'practice_trial': False,
                'countdown_active': False,
                'reset_interface': True
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
            
            # Emit appropriate status update for current state
            if session_data.get('practice_trial_active', False):
                # Practice trial is active
                socketio.emit('status_update', {
                    'status': 'Practice Trial Active',
                    'countdown_text': 'Practice Time: 05:00',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': -1,
                    'experiment_completed': False,
                    'experiment_configured': True,
                    'practice_trial': True,
                    'countdown_active': session_data['countdown_active']
                }, room=session_id)
            elif session_data['experiment_configured'] and not session_data.get('experiment_completed', False):
                # Experiment is configured but not completed
                if session_data['countdown_active']:
                    # A condition is currently running
                    socketio.emit('status_update', {
                        'status': f"Condition {session_data['current_condition_index'] + 1} Active",
                        'countdown_text': 'Time Remaining: 05:00',
                        'protocol_sequence': session_data['experiment_sequence'],
                        'current_condition_index': session_data['current_condition_index'],
                        'experiment_completed': False,
                        'experiment_configured': True,
                        'practice_trial': False,
                        'countdown_active': True
                    }, room=session_id)
                else:
                    # Ready to start or continue
                    socketio.emit('status_update', {
                        'status': 'Ready to start experiment',
                        'countdown_text': '',
                        'protocol_sequence': session_data['experiment_sequence'],
                        'current_condition_index': session_data['current_condition_index'],
                        'experiment_completed': False,
                        'experiment_configured': True,
                        'practice_trial': False,
                        'countdown_active': False,
                        'enable_start': True,
                        'enable_practice': True
                    }, room=session_id)
            elif session_data.get('experiment_completed', False):
                # Experiment completed
                socketio.emit('status_update', {
                    'status': 'Experiment Completed',
                    'countdown_text': 'Protocol Complete',
                    'protocol_sequence': session_data['experiment_sequence'],
                    'current_condition_index': session_data['current_condition_index'],
                    'experiment_completed': True,
                    'experiment_configured': True,
                    'practice_trial': False,
                    'countdown_active': False
                }, room=session_id)
            else:
                # Default state - not configured
                socketio.emit('status_update', {
                    'status': 'Standby - Awaiting Configuration',
                    'countdown_text': '',
                    'protocol_sequence': [],
                    'current_condition_index': 0,
                    'experiment_completed': False,
                    'experiment_configured': False,
                    'practice_trial': False,
                    'countdown_active': False
                }, room=session_id)
            
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
    
    @api.route('/api/system/reset', methods=['POST'])
    def reset_system():
        """Reset the entire experiment system - delete all configuration files"""
        try:
            import shutil
            import os
            
            # Directories to clean
            config_dir = 'config'
            data_dir = 'data'
            
            # Remove all config files except create directories
            if os.path.exists(config_dir):
                shutil.rmtree(config_dir)
            os.makedirs(config_dir, exist_ok=True)
            
            # Remove all data files except create directories  
            if os.path.exists(data_dir):
                shutil.rmtree(data_dir)
            os.makedirs(data_dir, exist_ok=True)
            
            # Clear all active sessions
            manager.sessions.clear()
            
            # Reload empty configurations
            manager.reload_configurations()
            
            logger.info("System reset completed - all configurations cleared")
            
            return jsonify({
                'success': True,
                'message': 'System reset completed. All configurations have been cleared.'
            })
            
        except Exception as e:
            logger.error(f"Error during system reset: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Failed to reset system: {str(e)}'
            }), 500
    
    return api 