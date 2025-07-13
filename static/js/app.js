/**
 * VR Experiment Manager - Main Application Class
 * Orchestrates all system components and manages the overall application state
 */

class VRExperimentManager {
    constructor() {
        // Core state
        this.sessionId = null;
        this.isConnected = false;
        this.protocolConfigured = false;
        
        // Data arrays
        this.interventionTypes = [];
        this.stimulusTypes = [];
        this.metadata = {};
        
        // Network settings
        this.currentTargetIp = '';
        this.currentTargetPort = 0;
        
        // Initialize managers
        this.configManager = new ConfigurationManager(this);
        this.orderManager = new OrderManager(this);
        this.uiManager = new UIManager(this);
        this.websocketManager = new WebSocketManager(this);
        this.eventManager = new EventManager(this);
        this.settingsManager = new SettingsManager(this);
        
        // Initialize application
        this.init();
    }
    
    async init() {
        try {
            // Start connection monitoring
            this.startConnectionMonitoring();
            
            // Create session
            await this.createSession();
            
            // Initialize all managers
            await this.configManager.initialize();
            await this.orderManager.initialize();
            this.uiManager.initialize();
            this.websocketManager.initialize();
            this.eventManager.initialize();
            
            // Load system status
            await this.loadSystemStatus();
            
            // Check for first-time setup
            if (this.metadata.is_first_time_setup) {
                this.uiManager.showFirstTimeSetup();
            }
            
        } catch (error) {
            console.error('Failed to initialize VR Experiment Manager:', error);
            this.uiManager.showSystemAlert('Initialization Error', 
                'Failed to initialize the system. Please refresh the page.', 'error');
        }
    }
    
    async createSession() {
        try {
            this.uiManager.showProcessingState('Initializing research session...');
            
            const response = await fetch('/api/session/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.sessionId = data.session_id;
                console.log('Research session initialized:', this.sessionId);
            } else {
                throw new Error('Failed to initialize session');
            }
        } catch (error) {
            console.error('Error initializing session:', error);
            this.uiManager.showSystemAlert('Critical Error', 
                'Failed to initialize research session. Please refresh the interface.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async loadSystemStatus() {
        try {
            this.uiManager.showProcessingState('Loading system configuration...');
            
            const response = await fetch(`/api/session/${this.sessionId}/status`);
            const data = await response.json();
            
            // Update application state
            this.interventionTypes = data.condition_types;
            this.stimulusTypes = data.object_types;
            this.protocolConfigured = data.experiment_configured;
            this.currentTargetIp = data.udp_ip;
            this.currentTargetPort = data.udp_port;
            this.metadata = data.metadata || {};
            
            // Update UI components
            this.uiManager.updateSystemStatus(data);
            this.uiManager.updateNetworkDisplay();
            
            // Load existing system logs
            data.logs.forEach(log => {
                this.uiManager.appendSystemLog(log.full_message);
            });
            
        } catch (error) {
            console.error('Error loading system status:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to load system configuration.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    startConnectionMonitoring() {
        // Check connection immediately
        this.checkServerConnection();
        
        // Then check every 5 seconds
        setInterval(() => {
            this.checkServerConnection();
        }, 5000);
    }
    
    async checkServerConnection() {
        try {
            const response = await fetch('/api/health', {
                method: 'GET',
                timeout: 3000
            });
            
            const connected = response.ok;
            if (connected !== this.isConnected) {
                this.isConnected = connected;
                this.uiManager.updateConnectionStatus(connected);
            }
        } catch (error) {
            if (this.isConnected) {
                this.isConnected = false;
                this.uiManager.updateConnectionStatus(false);
            }
        }
    }
    
    // Network configuration methods
    async updateNetworkConfiguration(udpIp, udpPort) {
        if (!udpIp || !udpPort) {
            this.uiManager.showSystemAlert('Configuration Error', 
                'Please enter both target IP address and communication port.', 'error');
            return;
        }
        
        try {
            this.uiManager.showProcessingState('Updating network configuration...');
            
            const response = await fetch(`/api/session/${this.sessionId}/network`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    udp_ip: udpIp,
                    udp_port: udpPort
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.currentTargetIp = udpIp;
                this.currentTargetPort = udpPort;
                this.uiManager.updateNetworkDisplay();
                this.uiManager.showSystemAlert('Configuration Updated', data.message, 'success');
            } else {
                this.uiManager.showSystemAlert('Configuration Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error updating network configuration:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to update network configuration.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    // Session management methods
    async saveSessionData(groupId, notes) {
        if (!groupId.trim()) {
            this.uiManager.showSystemAlert('Archive Error', 'Group ID is required', 'error');
            return;
        }
        
        try {
            this.uiManager.showProcessingState('Archiving session data...');
            
            const response = await fetch(`/api/session/${this.sessionId}/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    group_id: groupId,
                    notes: notes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.uiManager.showSystemAlert('Data Archived', data.message, 'success');
            } else {
                this.uiManager.showSystemAlert('Archive Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error archiving session data:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to archive session data.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    // Experiment control methods
    async validateAndInitializeProtocol() {
        const interventions = [];
        const stimuli = [];
        
        // Collect selected interventions and stimuli
        const conditionCount = this.interventionTypes.length;
        for (let i = 1; i <= conditionCount; i++) {
            const conditionElement = document.getElementById(`condition-${i}`);
            const objectElement = document.getElementById(`object-${i}`);
            
            if (conditionElement && objectElement) {
                interventions.push(conditionElement.value);
                stimuli.push(objectElement.value);
            }
        }
        
        try {
            this.uiManager.showProcessingState('Validating experimental protocol...');
            
            const response = await fetch(`/api/session/${this.sessionId}/configure`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    conditions: interventions,
                    objects: stimuli
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.protocolConfigured = true;
                this.uiManager.showSystemAlert('Protocol Validated', data.message, 'success');
            } else {
                this.uiManager.showSystemAlert('Validation Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error validating protocol:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to validate experimental protocol.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async startCondition() {
        try {
            this.uiManager.showProcessingState('Initiating experimental condition...');
            
            const response = await fetch(`/api/session/${this.sessionId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('Condition initiated:', data.condition_name);
            } else {
                this.uiManager.showSystemAlert('Initiation Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error initiating condition:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to initiate experimental condition.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async startPracticeTrial() {
        try {
            this.uiManager.showProcessingState('Starting practice trial...');
            
            const response = await fetch(`/api/session/${this.sessionId}/practice`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('Practice trial started:', data.condition_name);
            } else {
                this.uiManager.showSystemAlert('Practice Trial Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error starting practice trial:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to start practice trial.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async restartCondition() {
        try {
            this.uiManager.showProcessingState('Restarting current condition...');
            
            const response = await fetch(`/api/session/${this.sessionId}/restart`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('Condition restarted:', data.condition_name);
            } else {
                this.uiManager.showSystemAlert('Restart Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error restarting condition:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to restart condition.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async nextCondition() {
        try {
            this.uiManager.showProcessingState('Progressing to next condition...');
            
            const response = await fetch(`/api/session/${this.sessionId}/next`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                if (data.completed) {
                    this.uiManager.showSystemAlert('Protocol Complete', data.message, 'success');
                } else {
                    console.log('Progressed to next condition:', data.condition_name);
                }
            } else {
                this.uiManager.showSystemAlert('Progression Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error progressing to next condition:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to progress to next condition.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async forceNextCondition() {
        try {
            this.uiManager.showProcessingState('Overriding condition timer...');
            
            const response = await fetch(`/api/session/${this.sessionId}/force-next`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                // UI updates will come via WebSocket
                console.log('Timer overridden successfully');
            } else {
                this.uiManager.showSystemAlert('Override Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error overriding timer:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to override condition timer.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
    
    async resetExperiment() {
        try {
            this.uiManager.showProcessingState('Resetting experimental protocol...');
            
            const response = await fetch(`/api/session/${this.sessionId}/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.protocolConfigured = false;
                this.uiManager.showSystemAlert('Protocol Reset', data.message, 'success');
            } else {
                this.uiManager.showSystemAlert('Reset Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error resetting protocol:', error);
            this.uiManager.showSystemAlert('System Error', 
                'Failed to reset experimental protocol.', 'error');
        } finally {
            this.uiManager.hideProcessingState();
        }
    }
}

// Initialize the application when DOM is ready
let vrExperimentManager;

document.addEventListener('DOMContentLoaded', () => {
    vrExperimentManager = new VRExperimentManager();
    
    // Make it globally accessible for legacy compatibility
    window.controlSystem = vrExperimentManager;
}); 