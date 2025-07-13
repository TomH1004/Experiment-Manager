/**
 * WebSocket Manager
 * Handles real-time communication with the server via Socket.IO
 */

class WebSocketManager {
    constructor(app) {
        this.app = app;
        this.socket = null;
    }
    
    initialize() {
        this.socket = io();
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        this.socket.on('connect', () => {
            console.log('Real-time communication established');
            if (this.app.sessionId) {
                this.socket.emit('join_session', { session_id: this.app.sessionId });
            }
        });
        
        this.socket.on('disconnect', () => {
            console.log('Real-time communication lost');
        });
        
        this.socket.on('joined_session', (data) => {
            console.log('Joined research session:', data.session_id);
        });
        
        this.socket.on('log_update', (data) => {
            this.app.uiManager.appendSystemLog(data.full_message);
        });
        
        this.socket.on('countdown_update', (data) => {
            this.app.uiManager.updateConditionTimer(data.countdown_text);
        });
        
        this.socket.on('status_update', (data) => {
            this.handleStatusUpdate(data);
        });
        
        this.socket.on('protocol_status_update', (data) => {
            this.app.uiManager.updateProtocolState(data.status);
            if (data.protocol_sequence && data.current_condition_index !== undefined) {
                this.app.uiManager.updateConditionStatusPills(
                    data.protocol_sequence, 
                    data.current_condition_index, 
                    data.countdown_active
                );
            }
        });
    }
    
    handleStatusUpdate(data) {
        // Update protocol state
        this.app.uiManager.updateProtocolState(data.status);
        
        // Update countdown timer
        if (data.countdown_text) {
            this.app.uiManager.updateConditionTimer(data.countdown_text);
        }
        
        // Handle control button states
        if (data.enable_next) {
            this.app.uiManager.enableControl('next-condition');
            this.app.uiManager.highlightControl('next-condition');
        }
        
        if (data.enable_start) {
            this.app.uiManager.enableControl('start-condition');
            this.app.uiManager.highlightControl('start-condition');
        }
        
        if (data.disable_start) {
            this.app.uiManager.disableControl('start-condition');
        }
        
        if (data.enable_force_next) {
            this.app.uiManager.enableControl('force-next');
        }
        
        if (data.disable_force_next) {
            this.app.uiManager.disableControl('force-next');
        }
        
        if (data.disable_next) {
            this.app.uiManager.disableControl('next-condition');
        }
        
        // Handle experiment completion
        if (data.experiment_completed) {
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.disableControl('force-next');
            this.app.uiManager.updateConditionTimer('Protocol Complete');
        }
        
        // Update condition status pills
        if (data.protocol_sequence && data.current_condition_index !== undefined) {
            this.app.uiManager.updateConditionStatusPills(
                data.protocol_sequence, 
                data.current_condition_index, 
                data.countdown_active
            );
        }
        
        // Handle interface reset
        if (data.reset_interface) {
            this.app.uiManager.resetInterfaceState();
        }
    }
    
    // Method to join a session room
    joinSession(sessionId) {
        if (this.socket && sessionId) {
            this.socket.emit('join_session', { session_id: sessionId });
        }
    }
    
    // Method to check if socket is connected
    isConnected() {
        return this.socket && this.socket.connected;
    }
} 