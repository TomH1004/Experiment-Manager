#!/usr/bin/env python3
"""
Order Routes Module
Contains all order-related API endpoints for the VR Experiment Manager.
"""

from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

def create_order_routes(manager):
    """Create and configure order routes"""
    order_api = Blueprint('order_api', __name__)
    
    @order_api.route('/api/orders/generate', methods=['POST'])
    def generate_orders():
        """Generate experimental orders"""
        try:
            if manager.generate_all_orders():
                orders = manager.get_orders()
                return jsonify({
                    'success': True,
                    'message': f'Generated {len(orders)} experimental orders',
                    'orders': orders
                })
            else:
                return jsonify({'success': False, 'message': 'Failed to generate orders'})
        except Exception as e:
            logger.error(f"Error generating orders: {e}")
            return jsonify({'success': False, 'message': f'Failed to generate orders: {str(e)}'})
    
    @order_api.route('/api/orders', methods=['GET'])
    def get_orders():
        """Get all experimental orders"""
        try:
            orders = manager.get_orders()
            return jsonify({
                'success': True,
                'orders': orders
            })
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return jsonify({'success': False, 'message': f'Failed to get orders: {str(e)}'})
    
    @order_api.route('/api/orders/<order_id>/use', methods=['POST'])
    def use_order(order_id):
        """Mark an order as used"""
        try:
            data = request.json
            session_id = data.get('session_id')
            
            if manager.mark_order_used(order_id, session_id):
                return jsonify({'success': True, 'message': f'Order {order_id} marked as used'})
            else:
                return jsonify({'success': False, 'message': 'Failed to mark order as used'})
        except Exception as e:
            logger.error(f"Error marking order as used: {e}")
            return jsonify({'success': False, 'message': f'Failed to mark order as used: {str(e)}'})
    
    @order_api.route('/api/orders/reset-uses/<session_id>', methods=['POST'])
    def reset_order_uses(session_id):
        """Reset all order usage counts (for testing)"""
        try:
            orders = manager.load_orders()
            for order in orders:
                order['usage_count'] = 0
                if 'last_used' in order:
                    del order['last_used']
                if 'sessions' in order:
                    order['sessions'] = []
            
            if manager.save_orders(orders):
                manager.log_message(session_id, "All order usage counts reset")
                return jsonify({'success': True, 'message': 'All order usage counts reset successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to reset order usage counts'})
        except Exception as e:
            logger.error(f"Error resetting order uses: {e}")
            return jsonify({'success': False, 'message': f'Failed to reset order uses: {str(e)}'})
    
    return order_api 