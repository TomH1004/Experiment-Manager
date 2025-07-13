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
        
        // Reset all button states first to avoid conflicts
        this.resetAllButtonStates();
        
        // Apply new button states based on comprehensive state management
        this.applyButtonStates(data);
        
        // Update condition status pills
        if (data.protocol_sequence && data.current_condition_index !== undefined) {
            this.app.uiManager.updateConditionStatusPills(
                data.protocol_sequence, 
                data.current_condition_index, 
                data.countdown_active
            );
        }
        
        // Update experiment timeline
        this.app.uiManager.updateExperimentTimeline(data);
        
        // Handle interface reset
        if (data.reset_interface) {
            this.app.uiManager.resetInterfaceState();
        }
    }
    
    resetAllButtonStates() {
        // Reset all experiment control buttons to disabled state
        const buttons = ['practice-trial', 'start-condition', 'restart-condition', 'next-condition', 'force-next'];
        buttons.forEach(buttonId => {
            this.app.uiManager.disableControl(buttonId);
        });
    }
    
    applyButtonStates(data) {
        // Determine button states based on experiment state
        const experimentConfigured = data.experiment_configured || false;
        const experimentCompleted = data.experiment_completed || false;
        const practiceTrialActive = data.practice_trial || false;
        const countdownActive = data.countdown_active || false;
        const enableStart = data.enable_start || false;
        const enableNext = data.enable_next || false;
        
        if (experimentCompleted) {
            // Experiment completed - no buttons available except reset
            this.app.uiManager.disableControl('practice-trial');
            this.app.uiManager.disableControl('start-condition');
            this.app.uiManager.disableControl('restart-condition');
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.disableControl('force-next');
            
        } else if (!experimentConfigured) {
            // Not configured - no buttons available except reset
            this.app.uiManager.disableControl('practice-trial');
            this.app.uiManager.disableControl('start-condition');
            this.app.uiManager.disableControl('restart-condition');
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.disableControl('force-next');
            
        } else if (practiceTrialActive && countdownActive) {
            // Practice trial is actively running
            this.app.uiManager.disableControl('practice-trial');
            this.app.uiManager.disableControl('start-condition');
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.enableControl('restart-condition');
            this.app.uiManager.enableControl('force-next');
            
        } else if (countdownActive && !practiceTrialActive) {
            // Regular condition is actively running
            this.app.uiManager.disableControl('practice-trial');
            this.app.uiManager.disableControl('start-condition');
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.enableControl('restart-condition');
            this.app.uiManager.enableControl('force-next');
            
        } else if (enableNext) {
            // A condition just finished - ready to move to next condition
            this.app.uiManager.disableControl('practice-trial');
            this.app.uiManager.disableControl('start-condition');
            this.app.uiManager.disableControl('restart-condition');
            this.app.uiManager.disableControl('force-next');
            this.app.uiManager.enableControl('next-condition');
            this.app.uiManager.highlightControl('next-condition');
            
        } else if (enableStart) {
            // Ready to start a specific condition (first condition or moved to next)
            this.app.uiManager.enableControl('practice-trial');
            this.app.uiManager.enableControl('start-condition');
            this.app.uiManager.disableControl('restart-condition');
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.disableControl('force-next');
            this.app.uiManager.highlightControl('start-condition');
            
        } else {
            // Default configured state - can do practice trial or start first condition
            this.app.uiManager.enableControl('practice-trial');
            this.app.uiManager.enableControl('start-condition');
            this.app.uiManager.disableControl('restart-condition');
            this.app.uiManager.disableControl('next-condition');
            this.app.uiManager.disableControl('force-next');
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