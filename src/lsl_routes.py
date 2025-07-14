#!/usr/bin/env python3
"""
LSL Routes Module
Contains all LSL device management API endpoints for the VR Experiment Manager.
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit
import asyncio
import uuid
import logging
from typing import Dict, Any

from .lsl_remote_controller import get_lsl_controller

logger = logging.getLogger(__name__)

def create_lsl_routes(manager, socketio):
    """Create and configure LSL device management routes"""
    lsl_api = Blueprint('lsl_api', __name__)
    
    def run_async(coro):
        """Helper to run async functions in the Flask context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    
    @lsl_api.route('/api/lsl/devices', methods=['GET'])
    def get_lsl_devices():
        """Get all LSL devices"""
        try:
            async def _get_devices():
                controller = await get_lsl_controller(socketio)
                devices = controller.get_all_devices()
                return [device.to_dict() for device in devices]
            
            devices = run_async(_get_devices())
            return jsonify({
                'success': True,
                'devices': devices
            })
        except Exception as e:
            logger.error(f"Error getting LSL devices: {e}")
            return jsonify({'success': False, 'message': f'Failed to get devices: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices', methods=['POST'])
    def add_lsl_device():
        """Add a new LSL device"""
        try:
            data = request.json
            name = data.get('name', '').strip()
            ip = data.get('ip', '').strip()
            port = data.get('port')
            participant_id = data.get('participant_id', '').strip()
            
            # Validation
            if not name:
                return jsonify({'success': False, 'message': 'Device name is required'})
            if not ip:
                return jsonify({'success': False, 'message': 'IP address is required'})
            if not port or not isinstance(port, int) or port < 1 or port > 65535:
                return jsonify({'success': False, 'message': 'Valid port number is required'})
            if not participant_id:
                return jsonify({'success': False, 'message': 'Participant ID is required'})
            
            async def _add_device():
                controller = await get_lsl_controller(socketio)
                
                # Test connection first
                success, message = await controller.test_device_connection(ip, port)
                if not success:
                    return False, f"Connection test failed: {message}"
                
                # Add device
                device_id = str(uuid.uuid4())
                device = controller.add_device(device_id, name, ip, port, participant_id)
                
                # Set participant ID on the device
                success, message = await controller.set_participant_id(device_id, participant_id)
                if not success:
                    logger.warning(f"Failed to set participant ID on device {name}: {message}")
                
                return True, device.to_dict()
            
            success, result = run_async(_add_device())
            if success:
                # Emit device update to all clients
                socketio.emit('lsl_devices_update', {
                    'action': 'device_added',
                    'device': result
                })
                
                return jsonify({
                    'success': True,
                    'message': 'Device added successfully',
                    'device': result
                })
            else:
                return jsonify({'success': False, 'message': result})
                
        except Exception as e:
            logger.error(f"Error adding LSL device: {e}")
            return jsonify({'success': False, 'message': f'Failed to add device: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>', methods=['DELETE'])
    def remove_lsl_device(device_id):
        """Remove an LSL device"""
        try:
            async def _remove_device():
                controller = await get_lsl_controller(socketio)
                return controller.remove_device(device_id)
            
            success = run_async(_remove_device())
            if success:
                # Emit device update to all clients
                socketio.emit('lsl_devices_update', {
                    'action': 'device_removed',
                    'device_id': device_id
                })
                
                return jsonify({
                    'success': True,
                    'message': 'Device removed successfully'
                })
            else:
                return jsonify({'success': False, 'message': 'Device not found'})
                
        except Exception as e:
            logger.error(f"Error removing LSL device: {e}")
            return jsonify({'success': False, 'message': f'Failed to remove device: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/test', methods=['POST'])
    def test_lsl_device(device_id):
        """Test connection to an LSL device"""
        try:
            async def _test_device():
                controller = await get_lsl_controller(socketio)
                device = controller.get_device(device_id)
                if not device:
                    return False, "Device not found"
                
                return await controller.test_device_connection(device.ip, device.port)
            
            success, message = run_async(_test_device())
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error testing LSL device: {e}")
            return jsonify({'success': False, 'message': f'Connection test failed: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/participant', methods=['PUT'])
    def set_device_participant(device_id):
        """Set participant ID for a device"""
        try:
            data = request.json
            participant_id = data.get('participant_id', '').strip()
            
            if not participant_id:
                return jsonify({'success': False, 'message': 'Participant ID is required'})
            
            async def _set_participant():
                controller = await get_lsl_controller(socketio)
                return await controller.set_participant_id(device_id, participant_id)
            
            success, message = run_async(_set_participant())
            
            if success:
                # Emit device update to all clients
                socketio.emit('lsl_devices_update', {
                    'action': 'device_updated',
                    'device_id': device_id,
                    'participant_id': participant_id
                })
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error setting participant ID: {e}")
            return jsonify({'success': False, 'message': f'Failed to set participant ID: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/recording/start', methods=['POST'])
    def start_device_recording(device_id):
        """Start recording on a specific device"""
        try:
            async def _start_recording():
                controller = await get_lsl_controller(socketio)
                return await controller.start_recording(device_id)
            
            success, message = run_async(_start_recording())
            
            if success:
                # Emit recording status update
                socketio.emit('lsl_recording_update', {
                    'action': 'recording_started',
                    'device_id': device_id
                })
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return jsonify({'success': False, 'message': f'Failed to start recording: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/recording/stop', methods=['POST'])
    def stop_device_recording(device_id):
        """Stop recording on a specific device"""
        try:
            async def _stop_recording():
                controller = await get_lsl_controller(socketio)
                return await controller.stop_recording(device_id)
            
            success, message = run_async(_stop_recording())
            
            if success:
                # Emit recording status update
                socketio.emit('lsl_recording_update', {
                    'action': 'recording_stopped',
                    'device_id': device_id
                })
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return jsonify({'success': False, 'message': f'Failed to stop recording: {str(e)}'})
    
    @lsl_api.route('/api/lsl/recording/start-all', methods=['POST'])
    def start_all_recording():
        """Start recording on all devices"""
        try:
            async def _start_all():
                controller = await get_lsl_controller(socketio)
                return await controller.start_all_recording()
            
            success_count, total_count, errors = run_async(_start_all())
            
            # Emit recording status update
            socketio.emit('lsl_recording_update', {
                'action': 'all_recording_started',
                'success_count': success_count,
                'total_count': total_count,
                'errors': errors
            })
            
            if success_count == total_count:
                return jsonify({
                    'success': True,
                    'message': f'Recording started on all {total_count} devices'
                })
            elif success_count > 0:
                return jsonify({
                    'success': True,
                    'message': f'Recording started on {success_count}/{total_count} devices',
                    'errors': errors
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to start recording on any device',
                    'errors': errors
                })
                
        except Exception as e:
            logger.error(f"Error starting all recordings: {e}")
            return jsonify({'success': False, 'message': f'Failed to start recordings: {str(e)}'})
    
    @lsl_api.route('/api/lsl/recording/stop-all', methods=['POST'])
    def stop_all_recording():
        """Stop recording on all devices"""
        try:
            async def _stop_all():
                controller = await get_lsl_controller(socketio)
                return await controller.stop_all_recording()
            
            success_count, total_count, errors = run_async(_stop_all())
            
            # Emit recording status update
            socketio.emit('lsl_recording_update', {
                'action': 'all_recording_stopped',
                'success_count': success_count,
                'total_count': total_count,
                'errors': errors
            })
            
            if success_count == total_count:
                return jsonify({
                    'success': True,
                    'message': f'Recording stopped on all {total_count} devices'
                })
            elif success_count > 0:
                return jsonify({
                    'success': True,
                    'message': f'Recording stopped on {success_count}/{total_count} devices',
                    'errors': errors
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to stop recording on any device',
                    'errors': errors
                })
                
        except Exception as e:
            logger.error(f"Error stopping all recordings: {e}")
            return jsonify({'success': False, 'message': f'Failed to stop recordings: {str(e)}'})
    
    @lsl_api.route('/api/lsl/intervals/start-all', methods=['POST'])
    def start_all_intervals():
        """Start intervals on all devices"""
        try:
            data = request.json or {}
            interval_name = data.get('interval_name')
            
            async def _start_all():
                controller = await get_lsl_controller(socketio)
                return await controller.start_all_intervals(interval_name)
            
            success_count, total_count, errors = run_async(_start_all())
            
            # Emit interval status update
            socketio.emit('lsl_interval_update', {
                'action': 'all_intervals_started',
                'interval_name': interval_name,
                'success_count': success_count,
                'total_count': total_count,
                'errors': errors
            })
            
            if success_count == total_count:
                message = f'Intervals started on all {total_count} devices'
                if interval_name:
                    message += f' ({interval_name})'
                return jsonify({
                    'success': True,
                    'message': message
                })
            elif success_count > 0:
                return jsonify({
                    'success': True,
                    'message': f'Intervals started on {success_count}/{total_count} devices',
                    'errors': errors
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to start intervals on any device',
                    'errors': errors
                })
                
        except Exception as e:
            logger.error(f"Error starting all intervals: {e}")
            return jsonify({'success': False, 'message': f'Failed to start intervals: {str(e)}'})
    
    @lsl_api.route('/api/lsl/intervals/end-all', methods=['POST'])
    def end_all_intervals():
        """End intervals on all devices"""
        try:
            async def _end_all():
                controller = await get_lsl_controller(socketio)
                return await controller.end_all_intervals()
            
            success_count, total_count, errors = run_async(_end_all())
            
            # Emit interval status update
            socketio.emit('lsl_interval_update', {
                'action': 'all_intervals_ended',
                'success_count': success_count,
                'total_count': total_count,
                'errors': errors
            })
            
            if success_count == total_count:
                return jsonify({
                    'success': True,
                    'message': f'Intervals ended on all {total_count} devices'
                })
            elif success_count > 0:
                return jsonify({
                    'success': True,
                    'message': f'Intervals ended on {success_count}/{total_count} devices',
                    'errors': errors
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to end intervals on any device',
                    'errors': errors
                })
                
        except Exception as e:
            logger.error(f"Error ending all intervals: {e}")
            return jsonify({'success': False, 'message': f'Failed to end intervals: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/interval/start', methods=['POST'])
    def start_device_interval(device_id):
        """Start interval on a specific device"""
        try:
            data = request.json or {}
            interval_name = data.get('interval_name')
            
            async def _start_interval():
                controller = await get_lsl_controller(socketio)
                return await controller.start_interval(device_id, interval_name)
            
            success, message = run_async(_start_interval())
            
            if success:
                # Emit interval status update
                socketio.emit('lsl_interval_update', {
                    'action': 'interval_started',
                    'device_id': device_id,
                    'interval_name': interval_name
                })
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error starting interval: {e}")
            return jsonify({'success': False, 'message': f'Failed to start interval: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/interval/end', methods=['POST'])
    def end_device_interval(device_id):
        """End interval on a specific device"""
        try:
            async def _end_interval():
                controller = await get_lsl_controller(socketio)
                return await controller.end_interval(device_id)
            
            success, message = run_async(_end_interval())
            
            if success:
                # Emit interval status update
                socketio.emit('lsl_interval_update', {
                    'action': 'interval_ended',
                    'device_id': device_id
                })
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error ending interval: {e}")
            return jsonify({'success': False, 'message': f'Failed to end interval: {str(e)}'})
    
    @lsl_api.route('/api/lsl/devices/<device_id>/timestamp', methods=['POST'])
    def mark_device_timestamp(device_id):
        """Mark timestamp on a specific device"""
        try:
            data = request.json or {}
            timestamp_name = data.get('timestamp_name')
            
            async def _mark_timestamp():
                controller = await get_lsl_controller(socketio)
                return await controller.mark_timestamp(device_id, timestamp_name)
            
            success, message = run_async(_mark_timestamp())
            
            if success:
                # Emit timestamp update
                socketio.emit('lsl_timestamp_update', {
                    'action': 'timestamp_marked',
                    'device_id': device_id,
                    'timestamp_name': timestamp_name
                })
            
            return jsonify({
                'success': success,
                'message': message
            })
            
        except Exception as e:
            logger.error(f"Error marking timestamp: {e}")
            return jsonify({'success': False, 'message': f'Failed to mark timestamp: {str(e)}'})
    
    return lsl_api 