#!/usr/bin/env python3
"""
Configuration Routes Module
Contains all configuration-related API endpoints for the VR Experiment Manager.
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

def create_config_routes(manager):
    """Create and configure configuration routes"""
    config_api = Blueprint('config_api', __name__)
    
    @config_api.route('/api/config/metadata', methods=['GET'])
    def get_metadata():
        """Get metadata configuration"""
        return jsonify({
            'success': True,
            'metadata': manager.metadata
        })
    
    @config_api.route('/api/config/metadata', methods=['PUT'])
    def update_metadata():
        """Update metadata configuration"""
        try:
            data = request.json
            metadata = data.get('metadata', {})
            
            # Validate required fields
            required_fields = ['variable1_name', 'variable2_name', 'variable1_plural', 'variable2_plural']
            for field in required_fields:
                if field not in metadata or not metadata[field].strip():
                    return jsonify({'success': False, 'message': f'Missing required field: {field}'})
            
            # Update metadata
            if manager.save_metadata(metadata):
                return jsonify({'success': True, 'message': 'Metadata updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to save metadata'})
                
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            return jsonify({'success': False, 'message': f'Failed to update metadata: {str(e)}'})
    
    @config_api.route('/api/config/first-time-setup', methods=['POST'])
    def first_time_setup():
        """Complete first-time setup"""
        try:
            data = request.json
            
            # Extract metadata
            metadata = {
                'variable1_name': data.get('variable1_name', '').strip(),
                'variable2_name': data.get('variable2_name', '').strip(),
                'variable1_plural': data.get('variable1_plural', '').strip(),
                'variable2_plural': data.get('variable2_plural', '').strip(),
                'is_first_time_setup': False,
                'setup_completed_at': manager.metadata.get('created_at')
            }
            
            # Validate required fields
            required_fields = ['variable1_name', 'variable2_name', 'variable1_plural', 'variable2_plural']
            for field in required_fields:
                if not metadata[field]:
                    return jsonify({'success': False, 'message': f'Missing required field: {field}'})
            
            # Extract variable values
            variable1_values = data.get('variable1_values', [])
            variable2_values = data.get('variable2_values', [])
            
            if not variable1_values or not variable2_values:
                return jsonify({'success': False, 'message': 'Variable values are required'})
            
            if len(variable1_values) != len(variable2_values):
                return jsonify({'success': False, 'message': 'Variable lists must have equal length'})
            
            # Save all configurations
            if not manager.save_metadata(metadata):
                return jsonify({'success': False, 'message': 'Failed to save metadata'})
            
            if not manager.save_condition_types(variable1_values):
                return jsonify({'success': False, 'message': 'Failed to save condition types'})
            
            if not manager.save_object_types(variable2_values):
                return jsonify({'success': False, 'message': 'Failed to save object types'})
            
            # Reload configurations
            manager.reload_configurations()
            
            return jsonify({
                'success': True,
                'message': 'First-time setup completed successfully',
                'metadata': manager.metadata
            })
            
        except Exception as e:
            logger.error(f"Error completing first-time setup: {e}")
            return jsonify({'success': False, 'message': f'Failed to complete setup: {str(e)}'})
    
    @config_api.route('/api/config/condition-types', methods=['GET'])
    def get_condition_types():
        """Get condition types"""
        return jsonify({
            'success': True,
            'condition_types': manager.condition_types
        })
    
    @config_api.route('/api/config/condition-types', methods=['PUT'])
    def update_condition_types():
        """Update condition types"""
        try:
            data = request.json
            condition_types = data.get('condition_types', [])
            
            # Validate input
            if not condition_types:
                return jsonify({'success': False, 'message': 'At least one condition type is required'})
            
            # Remove empty strings and duplicates while preserving order
            cleaned_types = []
            seen = set()
            for ct in condition_types:
                ct = ct.strip()
                if ct and ct not in seen:
                    cleaned_types.append(ct)
                    seen.add(ct)
            
            if not cleaned_types:
                return jsonify({'success': False, 'message': 'At least one valid condition type is required'})
            
            if manager.save_condition_types(cleaned_types):
                return jsonify({'success': True, 'message': 'Condition types updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to save condition types'})
                
        except Exception as e:
            logger.error(f"Error updating condition types: {e}")
            return jsonify({'success': False, 'message': f'Failed to update condition types: {str(e)}'})
    
    @config_api.route('/api/config/condition-types', methods=['DELETE'])
    def delete_condition_type():
        """Delete a condition type"""
        try:
            data = request.json
            type_to_delete = data.get('type', '').strip()
            
            if not type_to_delete:
                return jsonify({'success': False, 'message': 'Type to delete is required'})
            
            if type_to_delete not in manager.condition_types:
                return jsonify({'success': False, 'message': 'Condition type not found'})
            
            # Remove the type
            updated_types = [ct for ct in manager.condition_types if ct != type_to_delete]
            
            if not updated_types:
                return jsonify({'success': False, 'message': 'Cannot delete the last condition type'})
            
            if manager.save_condition_types(updated_types):
                return jsonify({'success': True, 'message': f'Condition type "{type_to_delete}" deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to delete condition type'})
                
        except Exception as e:
            logger.error(f"Error deleting condition type: {e}")
            return jsonify({'success': False, 'message': f'Failed to delete condition type: {str(e)}'})
    
    @config_api.route('/api/config/object-types', methods=['GET'])
    def get_object_types():
        """Get object types"""
        return jsonify({
            'success': True,
            'object_types': manager.object_types
        })
    
    @config_api.route('/api/config/object-types', methods=['PUT'])
    def update_object_types():
        """Update object types"""
        try:
            data = request.json
            object_types = data.get('object_types', [])
            
            # Validate input
            if not object_types:
                return jsonify({'success': False, 'message': 'At least one object type is required'})
            
            # Remove empty strings and duplicates while preserving order
            cleaned_types = []
            seen = set()
            for ot in object_types:
                ot = ot.strip()
                if ot and ot not in seen:
                    cleaned_types.append(ot)
                    seen.add(ot)
            
            if not cleaned_types:
                return jsonify({'success': False, 'message': 'At least one valid object type is required'})
            
            if manager.save_object_types(cleaned_types):
                return jsonify({'success': True, 'message': 'Object types updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to save object types'})
                
        except Exception as e:
            logger.error(f"Error updating object types: {e}")
            return jsonify({'success': False, 'message': f'Failed to update object types: {str(e)}'})
    
    @config_api.route('/api/config/object-types', methods=['DELETE'])
    def delete_object_type():
        """Delete an object type"""
        try:
            data = request.json
            type_to_delete = data.get('type', '').strip()
            
            if not type_to_delete:
                return jsonify({'success': False, 'message': 'Type to delete is required'})
            
            if type_to_delete not in manager.object_types:
                return jsonify({'success': False, 'message': 'Object type not found'})
            
            # Remove the type
            updated_types = [ot for ot in manager.object_types if ot != type_to_delete]
            
            if not updated_types:
                return jsonify({'success': False, 'message': 'Cannot delete the last object type'})
            
            if manager.save_object_types(updated_types):
                return jsonify({'success': True, 'message': f'Object type "{type_to_delete}" deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to delete object type'})
                
        except Exception as e:
            logger.error(f"Error deleting object type: {e}")
            return jsonify({'success': False, 'message': f'Failed to delete object type: {str(e)}'})
    
    @config_api.route('/api/config/reload', methods=['POST'])
    def reload_configurations():
        """Reload all configurations from files"""
        try:
            manager.reload_configurations()
            return jsonify({
                'success': True,
                'message': 'Configurations reloaded successfully',
                'condition_types': manager.condition_types,
                'object_types': manager.object_types,
                'metadata': manager.metadata
            })
        except Exception as e:
            logger.error(f"Error reloading configurations: {e}")
            return jsonify({'success': False, 'message': f'Failed to reload configurations: {str(e)}'})
    
    return config_api 