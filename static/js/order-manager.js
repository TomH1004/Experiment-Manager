/**
 * Order Manager
 * Handles experimental order generation, selection, and management
 */

class OrderManager {
    constructor(app) {
        this.app = app;
        
        // Order state
        this.availableOrders = [];
        this.selectedOrder = null;
    }
    
    async initialize() {
        // Load available orders on initialization
        await this.loadAvailableOrders();
    }
    
    async loadAvailableOrders() {
        try {
            const response = await fetch('/api/orders');
            const data = await response.json();
            if (data.success) {
                this.availableOrders = data.orders;
                this.displayOrders();
            }
        } catch (error) {
            console.error('Error loading orders:', error);
        }
    }
    
    async generateAllOrders() {
        try {
            this.app.uiManager.showProcessingState('Generating all possible orders...');
            
            const response = await fetch('/api/orders/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.availableOrders = data.orders;
                this.displayOrders();
                this.app.uiManager.showSystemAlert('Orders Generated', 
                    `Generated ${data.orders.length} unique orders.`, 'success');
            } else {
                this.app.uiManager.showSystemAlert('Generation Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error generating orders:', error);
            this.app.uiManager.showSystemAlert('System Error', 'Failed to generate orders.', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    displayOrders() {
        const tbody = document.getElementById('orders-table-body');
        const countElement = document.getElementById('total-orders-count');
        
        if (!tbody || !countElement) return;
        
        const hideUsed = document.getElementById('hide-used-orders')?.checked || false;
        
        tbody.innerHTML = '';
        
        let visibleOrders = this.availableOrders;
        if (hideUsed) {
            visibleOrders = this.availableOrders.filter(order => order.usage_count === 0);
        }
        
        visibleOrders.forEach(order => {
            const row = document.createElement('tr');
            const isUsed = order.usage_count > 0;
            
            // Add highlighting class for used orders
            if (isUsed) {
                row.classList.add('order-row-used');
            }
            
            row.innerHTML = `
                <td class="font-mono text-sm">${order.order_id}</td>
                <td class="text-sm">
                    <div class="max-w-md">
                        ${order.sequence.map((item, index) => 
                            `<span class="inline-block bg-gray-100 px-2 py-1 rounded text-xs mr-1 mb-1">
                                ${index + 1}. ${item.condition_type} → ${item.object_type}
                            </span>`
                        ).join('')}
                    </div>
                </td>
                <td class="text-sm">${order.usage_count}</td>
                <td>
                    <button onclick="vrExperimentManager.orderManager.selectOrder('${order.order_id}')" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                        <i class="fas fa-check mr-1"></i>Select
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        countElement.textContent = this.availableOrders.length;
    }
    
    filterOrdersDisplay() {
        this.displayOrders();
    }
    
    async selectOrder(orderId) {
        try {
            const order = this.availableOrders.find(o => o.order_id === orderId);
            if (!order) {
                this.app.uiManager.showSystemAlert('Selection Error', 'Order not found.', 'error');
                return;
            }
            
            this.selectedOrder = order;
            this.applyOrderToMatrix(order);
            
            // Automatically set the Group ID to the selected order ID
            const groupIdField = document.getElementById('group-id');
            if (groupIdField) {
                groupIdField.value = orderId;
            }
            
            // Mark order as used
            await this.markOrderAsUsed(orderId);
            
            this.app.uiManager.closeOrderGenerator();
            
            this.app.uiManager.showSystemAlert('Order Selected', 
                `Applied order ${orderId} to the experimental matrix and set as Group ID.`, 'success');
            
        } catch (error) {
            console.error('Error selecting order:', error);
            this.app.uiManager.showSystemAlert('System Error', 'Failed to select order.', 'error');
        }
    }
    
    async markOrderAsUsed(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}/use`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: this.app.sessionId
                })
            });
            
            const data = await response.json();
            if (data.success) {
                console.log(`Order ${orderId} marked as used`);
                // Update the local order data
                const order = this.availableOrders.find(o => o.order_id === orderId);
                if (order) {
                    order.usage_count += 1;
                }
            } else {
                console.error('Failed to mark order as used:', data.message);
            }
        } catch (error) {
            console.error('Error marking order as used:', error);
        }
    }
    
    applyOrderToMatrix(order) {
        // Apply the selected order to the conditions matrix
        order.sequence.forEach((item, index) => {
            const conditionSelect = document.getElementById(`condition-${index + 1}`);
            const objectSelect = document.getElementById(`object-${index + 1}`);
            
            if (conditionSelect && objectSelect) {
                conditionSelect.value = item.condition_type;
                objectSelect.value = item.object_type;
            }
        });
    }
    
    async resetOrderUses() {
        this.app.uiManager.showConfirmationDialog(
            'Reset Order Uses',
            'Are you sure you want to reset all order usage counts to zero? This action cannot be undone and will clear all usage history.',
            async () => {
                this.app.uiManager.hideConfirmationDialog();
                
                try {
                    this.app.uiManager.showProcessingState('Resetting order uses...');
                    const response = await fetch(`/api/orders/reset-uses/${this.app.sessionId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    const data = await response.json();
                    if (data.success) {
                        this.app.uiManager.showSystemAlert('Order Uses Reset', data.message, 'success');
                        await this.loadAvailableOrders(); // Reload orders to reflect reset
                    } else {
                        this.app.uiManager.showSystemAlert('Reset Error', data.message, 'error');
                    }
                } catch (error) {
                    console.error('Error resetting order uses:', error);
                    this.app.uiManager.showSystemAlert('System Error', 'Failed to reset order uses.', 'error');
                } finally {
                    this.app.uiManager.hideProcessingState();
                }
            }
        );
    }
    
    openOrderGenerator() {
        const modal = document.getElementById('order-generator-modal');
        if (modal) {
            modal.classList.remove('hidden');
            this.loadAvailableOrders();
        }
    }
    
    closeOrderGenerator() {
        const modal = document.getElementById('order-generator-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
} 