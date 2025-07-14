/**
 * LSL Device Manager
 * Handles LSL device management, recording control, and automatic interval management
 */

class LSLManager {
    constructor(app) {
        this.app = app;
        this.devices = [];
        this.currentRecordingState = 'stopped'; // 'stopped', 'recording'
        this.autoIntervalManagement = true; // Automatically manage intervals based on experiment conditions
        
        // UI elements
        this.devicesContainer = null;
        this.noDevicesMessage = null;
        this.addDeviceModal = null;
        this.deviceModal = null;
        
        // Device form elements
        this.deviceNameInput = null;
        this.deviceIpInput = null;
        this.devicePortInput = null;
        this.participantIdInput = null;
    }
    
    initialize() {
        this.setupUIElements();
        this.setupEventListeners();
        this.loadDevices();
        this.setupWebSocketHandlers();
    }
    
    setupUIElements() {
        // Main container elements
        this.devicesContainer = document.getElementById('lsl-devices-container');
        this.noDevicesMessage = document.getElementById('no-devices-message');
        
        // Modal elements
        this.addDeviceModal = document.getElementById('lsl-device-modal');
        
        // Form elements
        this.deviceNameInput = document.getElementById('lsl-device-name');
        this.deviceIpInput = document.getElementById('lsl-device-ip');
        this.devicePortInput = document.getElementById('lsl-device-port');
        this.participantIdInput = document.getElementById('lsl-participant-id');
        
        // Set default port
        if (this.devicePortInput) {
            this.devicePortInput.value = '8080';
        }
    }
    
    setupEventListeners() {
        // Add device button
        const addDeviceBtn = document.getElementById('add-lsl-device');
        if (addDeviceBtn) {
            addDeviceBtn.addEventListener('click', () => this.showAddDeviceModal());
        }
        
        // Start/Stop all recording buttons
        const startAllBtn = document.getElementById('start-all-recording');
        const stopAllBtn = document.getElementById('stop-all-recording');
        
        if (startAllBtn) {
            startAllBtn.addEventListener('click', () => this.startAllRecording());
        }
        
        if (stopAllBtn) {
            stopAllBtn.addEventListener('click', () => this.stopAllRecording());
        }
        
        // Modal close buttons
        const closeModalBtn = document.getElementById('close-lsl-device-modal');
        const cancelBtn = document.getElementById('cancel-lsl-device');
        
        if (closeModalBtn) {
            closeModalBtn.addEventListener('click', () => this.hideAddDeviceModal());
        }
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.hideAddDeviceModal());
        }
        
        // Test connection button
        const testConnectionBtn = document.getElementById('test-lsl-connection');
        if (testConnectionBtn) {
            testConnectionBtn.addEventListener('click', () => this.testConnection());
        }
        
        // Save device button
        const saveDeviceBtn = document.getElementById('save-lsl-device');
        if (saveDeviceBtn) {
            saveDeviceBtn.addEventListener('click', () => this.saveDevice());
        }
        
        // Close modal when clicking outside
        if (this.addDeviceModal) {
            this.addDeviceModal.addEventListener('click', (event) => {
                if (event.target === this.addDeviceModal) {
                    this.hideAddDeviceModal();
                }
            });
        }
        
        // Enter key handling in forms
        [this.deviceNameInput, this.deviceIpInput, this.devicePortInput, this.participantIdInput].forEach(input => {
            if (input) {
                input.addEventListener('keypress', (event) => {
                    if (event.key === 'Enter') {
                        this.saveDevice();
                    }
                });
            }
        });
    }
    
    setupWebSocketHandlers() {
        if (!this.app.websocketManager || !this.app.websocketManager.socket) {
            return;
        }
        
        const socket = this.app.websocketManager.socket;
        
        // Device management updates
        socket.on('lsl_devices_update', (data) => {
            this.handleDeviceUpdate(data);
        });
        
        // Recording status updates
        socket.on('lsl_recording_update', (data) => {
            this.handleRecordingUpdate(data);
        });
        
        // Interval updates
        socket.on('lsl_interval_update', (data) => {
            this.handleIntervalUpdate(data);
        });
        
        // Timestamp updates
        socket.on('lsl_timestamp_update', (data) => {
            this.handleTimestampUpdate(data);
        });
        
        // Experiment status updates for automatic interval management
        socket.on('status_update', (data) => {
            this.handleExperimentStatusUpdate(data);
        });
    }
    
    async loadDevices() {
        try {
            const response = await fetch('/api/lsl/devices');
            const data = await response.json();
            
            if (data.success) {
                this.devices = data.devices;
                this.renderDevices();
                this.updateControlButtons();
            } else {
                console.error('Failed to load LSL devices:', data.message);
                this.app.uiManager.showSystemAlert('Error', 'Failed to load LSL devices: ' + data.message, 'error');
            }
        } catch (error) {
            console.error('Error loading LSL devices:', error);
            this.app.uiManager.showSystemAlert('Error', 'Failed to load LSL devices', 'error');
        }
    }
    
    renderDevices() {
        if (!this.devicesContainer || !this.noDevicesMessage) {
            return;
        }
        
        // Clear existing devices
        this.devicesContainer.innerHTML = '';
        
        if (this.devices.length === 0) {
            this.noDevicesMessage.style.display = 'block';
            return;
        }
        
        this.noDevicesMessage.style.display = 'none';
        
        this.devices.forEach(device => {
            const deviceElement = this.createDeviceElement(device);
            this.devicesContainer.appendChild(deviceElement);
        });
    }
    
    createDeviceElement(device) {
        const deviceDiv = document.createElement('div');
        deviceDiv.className = 'bg-white border rounded-lg p-4 shadow-sm';
        deviceDiv.setAttribute('data-device-id', device.device_id);
        
        const connectionStatusClass = device.is_connected ? 'text-green-600' : 'text-red-600';
        const connectionStatusIcon = device.is_connected ? 'fa-check-circle' : 'fa-times-circle';
        const recordingStatusClass = device.is_recording ? 'text-blue-600' : 'text-gray-600';
        const recordingStatusIcon = device.is_recording ? 'fa-record-vinyl' : 'fa-stop-circle';
        
        deviceDiv.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <div class="flex items-center">
                    <i class="fas fa-heartbeat text-red-600 mr-2"></i>
                    <h3 class="text-lg font-semibold text-gray-800">${this.escapeHtml(device.name)}</h3>
                </div>
                <div class="flex items-center space-x-2">
                    <div class="flex items-center">
                        <i class="fas ${connectionStatusIcon} ${connectionStatusClass} mr-1"></i>
                        <span class="text-sm ${connectionStatusClass}">${device.connection_status}</span>
                    </div>
                    <div class="flex items-center">
                        <i class="fas ${recordingStatusIcon} ${recordingStatusClass} mr-1"></i>
                        <span class="text-sm ${recordingStatusClass}">${device.recording_status}</span>
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4 text-sm">
                <div>
                    <span class="text-gray-600">IP Address:</span>
                    <span class="font-mono ml-2">${this.escapeHtml(device.ip)}:${device.port}</span>
                </div>
                <div>
                    <span class="text-gray-600">Participant:</span>
                    <span class="ml-2">${this.escapeHtml(device.participant_id)}</span>
                </div>
            </div>
            
            <div class="flex space-x-2">
                <button onclick="lslManager.testDevice('${device.device_id}')" 
                        class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                    <i class="fas fa-wifi mr-1"></i>Test
                </button>
                <button onclick="lslManager.toggleRecording('${device.device_id}')" 
                        class="recording-btn bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        ${!device.is_connected ? 'disabled' : ''}>
                    <i class="fas ${device.is_recording ? 'fa-stop' : 'fa-play'} mr-1"></i>
                    ${device.is_recording ? 'Stop' : 'Start'}
                </button>
                <button onclick="lslManager.editParticipant('${device.device_id}')" 
                        class="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm">
                    <i class="fas fa-user-edit mr-1"></i>Edit
                </button>
                <button onclick="lslManager.removeDevice('${device.device_id}')" 
                        class="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm">
                    <i class="fas fa-trash mr-1"></i>Remove
                </button>
            </div>
        `;
        
        return deviceDiv;
    }
    
    showAddDeviceModal() {
        if (this.addDeviceModal) {
            this.addDeviceModal.classList.remove('hidden');
            // Clear form
            if (this.deviceNameInput) this.deviceNameInput.value = '';
            if (this.deviceIpInput) this.deviceIpInput.value = '';
            if (this.devicePortInput) this.devicePortInput.value = '8080';
            if (this.participantIdInput) this.participantIdInput.value = '';
            
            // Focus on first input
            if (this.deviceNameInput) {
                setTimeout(() => this.deviceNameInput.focus(), 100);
            }
        }
    }
    
    hideAddDeviceModal() {
        if (this.addDeviceModal) {
            this.addDeviceModal.classList.add('hidden');
        }
    }
    
    async testConnection() {
        const ip = this.deviceIpInput?.value?.trim();
        const port = parseInt(this.devicePortInput?.value);
        
        if (!ip || !port) {
            this.app.uiManager.showSystemAlert('Error', 'Please enter IP address and port', 'error');
            return;
        }
        
        try {
            this.app.uiManager.showProcessingState('Testing connection...');
            
            // Create a temporary device for testing
            const testResponse = await fetch('/api/lsl/devices/test-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ip, port })
            });
            
            const data = await testResponse.json();
            
            if (data.success) {
                this.app.uiManager.showSystemAlert('Connection Test', data.message, 'success');
            } else {
                this.app.uiManager.showSystemAlert('Connection Test Failed', data.message, 'error');
            }
        } catch (error) {
            console.error('Error testing connection:', error);
            this.app.uiManager.showSystemAlert('Error', 'Connection test failed', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async saveDevice() {
        const name = this.deviceNameInput?.value?.trim();
        const ip = this.deviceIpInput?.value?.trim();
        const port = parseInt(this.devicePortInput?.value);
        const participantId = this.participantIdInput?.value?.trim();
        
        // Validation
        if (!name) {
            this.app.uiManager.showSystemAlert('Error', 'Please enter a device name', 'error');
            return;
        }
        
        if (!ip) {
            this.app.uiManager.showSystemAlert('Error', 'Please enter an IP address', 'error');
            return;
        }
        
        if (!port || port < 1 || port > 65535) {
            this.app.uiManager.showSystemAlert('Error', 'Please enter a valid port number (1-65535)', 'error');
            return;
        }
        
        if (!participantId) {
            this.app.uiManager.showSystemAlert('Error', 'Please enter a participant ID', 'error');
            return;
        }
        
        try {
            this.app.uiManager.showProcessingState('Adding device...');
            
            const response = await fetch('/api/lsl/devices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    ip,
                    port,
                    participant_id: participantId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.hideAddDeviceModal();
                this.app.uiManager.showSystemAlert('Success', 'Device added successfully', 'success');
                // Device will be updated via WebSocket
            } else {
                this.app.uiManager.showSystemAlert('Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error adding device:', error);
            this.app.uiManager.showSystemAlert('Error', 'Failed to add device', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async testDevice(deviceId) {
        try {
            this.app.uiManager.showProcessingState('Testing device connection...');
            
            const response = await fetch(`/api/lsl/devices/${deviceId}/test`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.app.uiManager.showSystemAlert('Connection Test', data.message, 'success');
            } else {
                this.app.uiManager.showSystemAlert('Connection Test Failed', data.message, 'error');
            }
        } catch (error) {
            console.error('Error testing device:', error);
            this.app.uiManager.showSystemAlert('Error', 'Connection test failed', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async toggleRecording(deviceId) {
        const device = this.devices.find(d => d.device_id === deviceId);
        if (!device) {
            return;
        }
        
        const action = device.is_recording ? 'stop' : 'start';
        
        try {
            this.app.uiManager.showProcessingState(`${action === 'start' ? 'Starting' : 'Stopping'} recording...`);
            
            const response = await fetch(`/api/lsl/devices/${deviceId}/recording/${action}`, {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.app.uiManager.showSystemAlert('Recording', data.message, 'success');
                // Device status will be updated via WebSocket
            } else {
                this.app.uiManager.showSystemAlert('Error', data.message, 'error');
            }
        } catch (error) {
            console.error(`Error ${action}ing recording:`, error);
            this.app.uiManager.showSystemAlert('Error', `Failed to ${action} recording`, 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async editParticipant(deviceId) {
        const device = this.devices.find(d => d.device_id === deviceId);
        if (!device) {
            return;
        }
        
        const newParticipantId = prompt('Enter new participant ID:', device.participant_id);
        if (newParticipantId && newParticipantId.trim() !== device.participant_id) {
            try {
                this.app.uiManager.showProcessingState('Updating participant ID...');
                
                const response = await fetch(`/api/lsl/devices/${deviceId}/participant`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        participant_id: newParticipantId.trim()
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.app.uiManager.showSystemAlert('Success', data.message, 'success');
                    // Device will be updated via WebSocket
                } else {
                    this.app.uiManager.showSystemAlert('Error', data.message, 'error');
                }
            } catch (error) {
                console.error('Error updating participant ID:', error);
                this.app.uiManager.showSystemAlert('Error', 'Failed to update participant ID', 'error');
            } finally {
                this.app.uiManager.hideProcessingState();
            }
        }
    }
    
    async removeDevice(deviceId) {
        const device = this.devices.find(d => d.device_id === deviceId);
        if (!device) {
            return;
        }
        
        if (!confirm(`Are you sure you want to remove device "${device.name}"?`)) {
            return;
        }
        
        try {
            this.app.uiManager.showProcessingState('Removing device...');
            
            const response = await fetch(`/api/lsl/devices/${deviceId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.app.uiManager.showSystemAlert('Success', data.message, 'success');
                // Device will be removed via WebSocket
            } else {
                this.app.uiManager.showSystemAlert('Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error removing device:', error);
            this.app.uiManager.showSystemAlert('Error', 'Failed to remove device', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async startAllRecording() {
        if (this.devices.length === 0) {
            this.app.uiManager.showSystemAlert('Error', 'No devices configured', 'error');
            return;
        }
        
        try {
            this.app.uiManager.showProcessingState('Starting recording on all devices...');
            
            const response = await fetch('/api/lsl/recording/start-all', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.app.uiManager.showSystemAlert('Recording Started', data.message, 'success');
                // Update current recording state
                this.currentRecordingState = 'recording';
                this.updateControlButtons();
            } else {
                this.app.uiManager.showSystemAlert('Error', data.message, 'error');
                if (data.errors && data.errors.length > 0) {
                    console.error('Recording errors:', data.errors);
                }
            }
        } catch (error) {
            console.error('Error starting all recordings:', error);
            this.app.uiManager.showSystemAlert('Error', 'Failed to start recordings', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async stopAllRecording() {
        if (this.devices.length === 0) {
            this.app.uiManager.showSystemAlert('Error', 'No devices configured', 'error');
            return;
        }
        
        try {
            this.app.uiManager.showProcessingState('Stopping recording on all devices...');
            
            const response = await fetch('/api/lsl/recording/stop-all', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.app.uiManager.showSystemAlert('Recording Stopped', data.message, 'success');
                // Update current recording state
                this.currentRecordingState = 'stopped';
                this.updateControlButtons();
            } else {
                this.app.uiManager.showSystemAlert('Error', data.message, 'error');
                if (data.errors && data.errors.length > 0) {
                    console.error('Recording errors:', data.errors);
                }
            }
        } catch (error) {
            console.error('Error stopping all recordings:', error);
            this.app.uiManager.showSystemAlert('Error', 'Failed to stop recordings', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    async startAllIntervals(intervalName = null) {
        if (this.devices.length === 0) {
            return;
        }
        
        try {
            const response = await fetch('/api/lsl/intervals/start-all', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    interval_name: intervalName
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('Intervals started on all devices:', data.message);
            } else {
                console.error('Error starting intervals:', data.message);
            }
        } catch (error) {
            console.error('Error starting all intervals:', error);
        }
    }
    
    async endAllIntervals() {
        if (this.devices.length === 0) {
            return;
        }
        
        try {
            const response = await fetch('/api/lsl/intervals/end-all', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log('Intervals ended on all devices:', data.message);
            } else {
                console.error('Error ending intervals:', data.message);
            }
        } catch (error) {
            console.error('Error ending all intervals:', error);
        }
    }
    
    updateControlButtons() {
        const startAllBtn = document.getElementById('start-all-recording');
        const stopAllBtn = document.getElementById('stop-all-recording');
        
        const hasDevices = this.devices.length > 0;
        const hasConnectedDevices = this.devices.some(d => d.is_connected);
        
        if (startAllBtn) {
            startAllBtn.disabled = !hasConnectedDevices;
        }
        
        if (stopAllBtn) {
            stopAllBtn.disabled = !hasDevices;
        }
    }
    
    // WebSocket event handlers
    handleDeviceUpdate(data) {
        console.log('Device update:', data);
        
        switch (data.action) {
            case 'device_added':
                this.devices.push(data.device);
                this.renderDevices();
                this.updateControlButtons();
                break;
                
            case 'device_removed':
                this.devices = this.devices.filter(d => d.device_id !== data.device_id);
                this.renderDevices();
                this.updateControlButtons();
                break;
                
            case 'device_updated':
                const deviceIndex = this.devices.findIndex(d => d.device_id === data.device_id);
                if (deviceIndex !== -1) {
                    if (data.participant_id) {
                        this.devices[deviceIndex].participant_id = data.participant_id;
                    }
                    this.renderDevices();
                }
                break;
        }
    }
    
    handleRecordingUpdate(data) {
        console.log('Recording update:', data);
        
        switch (data.action) {
            case 'recording_started':
                const deviceStart = this.devices.find(d => d.device_id === data.device_id);
                if (deviceStart) {
                    deviceStart.is_recording = true;
                    deviceStart.recording_status = 'Recording';
                    this.renderDevices();
                }
                break;
                
            case 'recording_stopped':
                const deviceStop = this.devices.find(d => d.device_id === data.device_id);
                if (deviceStop) {
                    deviceStop.is_recording = false;
                    deviceStop.recording_status = 'Stopped';
                    this.renderDevices();
                }
                break;
                
            case 'all_recording_started':
                this.currentRecordingState = 'recording';
                this.updateControlButtons();
                break;
                
            case 'all_recording_stopped':
                this.currentRecordingState = 'stopped';
                this.updateControlButtons();
                break;
        }
    }
    
    handleIntervalUpdate(data) {
        console.log('Interval update:', data);
        // Could be used to show visual feedback about interval status
    }
    
    handleTimestampUpdate(data) {
        console.log('Timestamp update:', data);
        // Could be used to show visual feedback about timestamp marking
    }
    
    handleExperimentStatusUpdate(data) {
        // Automatic interval management based on experiment conditions
        if (!this.autoIntervalManagement) {
            return;
        }
        
        // Start intervals when a condition starts
        if (data.status && data.status.includes('Condition') && data.countdown_active) {
            const conditionIndex = data.current_condition_index || 0;
            const intervalName = `Condition_${conditionIndex + 1}`;
            this.startAllIntervals(intervalName);
        }
        
        // End intervals when condition ends (next condition or experiment complete)
        if (data.status && (data.status.includes('Next condition') || data.status.includes('Completed'))) {
            this.endAllIntervals();
        }
    }
    
    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Public API for integration with experiment manager
    setAutoIntervalManagement(enabled) {
        this.autoIntervalManagement = enabled;
    }
    
    getRecordingState() {
        return this.currentRecordingState;
    }
    
    getConnectedDeviceCount() {
        return this.devices.filter(d => d.is_connected).length;
    }
    
    getRecordingDeviceCount() {
        return this.devices.filter(d => d.is_recording).length;
    }
}

// Global instance
let lslManager = null;

// Make it available globally for onclick handlers
window.lslManager = null; 