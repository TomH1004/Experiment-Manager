// VR Experimental Control System - Frontend Controller
class VRExperimentalControlSystem {
    constructor() {
        this.sessionId = null;
        this.socket = null;
        this.protocolConfigured = false;
        this.interventionTypes = [];
        this.stimulusTypes = [];
        this.currentTargetIp = '';
        this.currentTargetPort = 0;
        
        // Configuration management
        this.currentConditionTypes = [];
        this.currentObjectTypes = [];
        this.pendingConditionTypes = [];
        this.pendingObjectTypes = [];
        
        this.init();
    }
    
    async init() {
        // Initialize the control system
        await this.createSession();
        this.setupEventListeners();
        this.initializeWebSocket();
        this.loadSystemStatus();
        this.loadConfigurations();
    }
    
    async loadConfigurations() {
        try {
            // Load condition types
            const conditionResponse = await fetch('/api/config/condition-types');
            const conditionData = await conditionResponse.json();
            if (conditionData.success) {
                this.currentConditionTypes = conditionData.condition_types;
                this.pendingConditionTypes = [...conditionData.condition_types];
            }
            
            // Load object types
            const objectResponse = await fetch('/api/config/object-types');
            const objectData = await objectResponse.json();
            if (objectData.success) {
                this.currentObjectTypes = objectData.object_types;
                this.pendingObjectTypes = [...objectData.object_types];
            }
            
            // Display in UI
            this.displayConditionTypes();
            this.displayObjectTypes();
            
        } catch (error) {
            console.error('Error loading configurations:', error);
        }
    }
    
    displayConditionTypes() {
        const container = document.getElementById('condition-types-list');
        const countElement = document.getElementById('condition-count');
        container.innerHTML = '';
        
        this.pendingConditionTypes.forEach((type, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between bg-white px-3 py-2 border border-gray-200 rounded-md';
            item.innerHTML = `
                <span class="text-sm font-medium text-gray-700">${type}</span>
                <button class="text-red-600 hover:text-red-800 text-sm" onclick="controlSystem.removeConditionType(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
        
        countElement.textContent = `(${this.pendingConditionTypes.length})`;
        this.validateConfiguration();
    }
    
    displayObjectTypes() {
        const container = document.getElementById('object-types-list');
        const countElement = document.getElementById('object-count');
        container.innerHTML = '';
        
        this.pendingObjectTypes.forEach((type, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between bg-white px-3 py-2 border border-gray-200 rounded-md';
            item.innerHTML = `
                <span class="text-sm font-medium text-gray-700">${type}</span>
                <button class="text-red-600 hover:text-red-800 text-sm" onclick="controlSystem.removeObjectType(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
        
        countElement.textContent = `(${this.pendingObjectTypes.length})`;
        this.validateConfiguration();
    }
    
    validateConfiguration() {
        const messageElement = document.getElementById('config-validation-message');
        const textElement = document.getElementById('config-validation-text');
        const saveButton = document.getElementById('save-all-config');
        
        const conditionCount = this.pendingConditionTypes.length;
        const objectCount = this.pendingObjectTypes.length;
        
        if (conditionCount === 0 || objectCount === 0) {
            messageElement.className = 'mb-4 p-3 rounded-md bg-red-50 border border-red-200 text-red-700';
            textElement.textContent = 'Both intervention types and stimulus objects must have at least one item.';
            messageElement.classList.remove('hidden');
            saveButton.disabled = true;
            saveButton.classList.add('opacity-50', 'cursor-not-allowed');
        } else if (conditionCount !== objectCount) {
            messageElement.className = 'mb-4 p-3 rounded-md bg-orange-50 border border-orange-200 text-orange-700';
            textElement.textContent = `Number of intervention types (${conditionCount}) must match number of stimulus objects (${objectCount}).`;
            messageElement.classList.remove('hidden');
            saveButton.disabled = true;
            saveButton.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            messageElement.classList.add('hidden');
            saveButton.disabled = false;
            saveButton.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }
    
    addConditionType() {
        const input = document.getElementById('new-condition-type');
        const newType = input.value.trim();
        
        if (newType && !this.pendingConditionTypes.includes(newType)) {
            this.pendingConditionTypes.push(newType);
            input.value = '';
            this.displayConditionTypes();
        }
    }
    
    removeConditionType(index) {
        this.pendingConditionTypes.splice(index, 1);
        this.displayConditionTypes();
    }
    
    addObjectType() {
        const input = document.getElementById('new-object-type');
        const newType = input.value.trim();
        
        if (newType && !this.pendingObjectTypes.includes(newType)) {
            this.pendingObjectTypes.push(newType);
            input.value = '';
            this.displayObjectTypes();
        }
    }
    
    removeObjectType(index) {
        this.pendingObjectTypes.splice(index, 1);
        this.displayObjectTypes();
    }
    
    async saveAllConfig() {
        try {
            this.showProcessingState('Saving configuration changes...');
            
            // Save both condition types and object types
            const conditionResponse = await fetch('/api/config/condition-types', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    condition_types: this.pendingConditionTypes
                })
            });
            
            const objectResponse = await fetch('/api/config/object-types', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    object_types: this.pendingObjectTypes
                })
            });
            
            const conditionData = await conditionResponse.json();
            const objectData = await objectResponse.json();
            
            if (conditionData.success && objectData.success) {
                this.currentConditionTypes = [...this.pendingConditionTypes];
                this.currentObjectTypes = [...this.pendingObjectTypes];
                this.closeConfigModal();
                
                // Show success message briefly before reload
                this.showSystemAlert('Configuration Updated', 'All changes saved successfully. Reloading interface...', 'success');
                
                // Reload page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                const errorMessage = !conditionData.success ? conditionData.message : objectData.message;
                this.showSystemAlert('Save Error', errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error saving configurations:', error);
            this.showSystemAlert('System Error', 'Failed to save configuration changes.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    cancelConfigChanges() {
        // Reset pending changes to current values
        this.pendingConditionTypes = [...this.currentConditionTypes];
        this.pendingObjectTypes = [...this.currentObjectTypes];
        
        // Update displays
        this.displayConditionTypes();
        this.displayObjectTypes();
        
        // Close modal
        this.closeConfigModal();
    }
    
    generateConditionsMatrix() {
        const tbody = document.getElementById('conditions-matrix-body');
        tbody.innerHTML = '';
        
        const conditionCount = this.interventionTypes.length;
        
        for (let i = 0; i < conditionCount; i++) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="font-semibold">C${i + 1}</td>
                <td>
                    <select id="condition-${i + 1}" class="scientific-input w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                    </select>
                </td>
                <td class="text-gray-600">Virtual Object</td>
                <td>
                    <select id="object-${i + 1}" class="scientific-input w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                    </select>
                </td>
                <td><span id="status-${i + 1}" class="px-2 py-1 text-xs rounded-full status-pending">Pending</span></td>
            `;
            tbody.appendChild(row);
        }
    }
    
    async createSession() {
        try {
            this.showProcessingState('Initializing research session...');
            
            const response = await fetch('/api/session/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.sessionId = data.session_id;
                document.getElementById('session-id').textContent = this.sessionId.substring(0, 8);
                console.log('Research session initialized:', this.sessionId);
            } else {
                throw new Error('Failed to initialize session');
            }
        } catch (error) {
            console.error('Error initializing session:', error);
            this.showSystemAlert('Critical Error', 'Failed to initialize research session. Please refresh the interface.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    initializeWebSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Real-time communication established');
            if (this.sessionId) {
                this.socket.emit('join_session', { session_id: this.sessionId });
            }
        });
        
        this.socket.on('disconnect', () => {
            console.log('Real-time communication lost');
        });
        
        this.socket.on('joined_session', (data) => {
            console.log('Joined research session:', data.session_id);
        });
        
        this.socket.on('log_update', (data) => {
            this.appendSystemLog(data.full_message);
        });
        
        this.socket.on('countdown_update', (data) => {
            this.updateConditionTimer(data.countdown_text);
        });
        
        this.socket.on('status_update', (data) => {
            this.updateProtocolState(data.status);
            if (data.countdown_text) {
                this.updateConditionTimer(data.countdown_text);
            }
            if (data.enable_next) {
                this.enableControl('next-condition');
                this.highlightControl('next-condition');
            }
            if (data.enable_start) {
                this.enableControl('start-condition');
                this.highlightControl('start-condition');
            }
            if (data.disable_start) {
                this.disableControl('start-condition');
            }
            if (data.enable_force_next) {
                this.enableControl('force-next');
            }
            if (data.disable_force_next) {
                this.disableControl('force-next');
            }
            if (data.disable_next) {
                this.disableControl('next-condition');
            }
            if (data.experiment_completed) {
                this.disableControl('next-condition');
                this.disableControl('force-next');
                this.updateConditionTimer('Protocol Complete');
            }
            if (data.protocol_sequence && data.current_condition_index !== undefined) {
                this.updateConditionStatusPills(data.protocol_sequence, data.current_condition_index, data.countdown_active);
            }
            if (data.reset_interface) {
                this.resetInterfaceState();
            }
        });
        
        this.socket.on('protocol_status_update', (data) => {
            this.updateProtocolState(data.status);
            if (data.protocol_sequence && data.current_condition_index !== undefined) {
                this.updateConditionStatusPills(data.protocol_sequence, data.current_condition_index, data.countdown_active);
            }
        });
    }
    
    async loadSystemStatus() {
        try {
            this.showProcessingState('Loading system configuration...');
            
            const response = await fetch(`/api/session/${this.sessionId}/status`);
            const data = await response.json();
            
            this.interventionTypes = data.condition_types;
            this.stimulusTypes = data.object_types;
            this.protocolConfigured = data.experiment_configured;
            this.currentTargetIp = data.udp_ip;
            this.currentTargetPort = data.udp_port;
            
            this.populateInterventionSelectors();
            this.updateControlInterface(data);
            this.updateNetworkDisplay();
            
            // Load existing system logs
            data.logs.forEach(log => {
                this.appendSystemLog(log.full_message);
            });
            
        } catch (error) {
            console.error('Error loading system status:', error);
            this.showSystemAlert('System Error', 'Failed to load system configuration.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    populateInterventionSelectors() {
        // Generate matrix first
        this.generateConditionsMatrix();
        
        const conditionCount = this.interventionTypes.length;
        
        // Populate intervention type selectors
        for (let i = 1; i <= conditionCount; i++) {
            const select = document.getElementById(`condition-${i}`);
            if (select) {
                select.innerHTML = ''; // Clear existing options
                this.interventionTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
            }
        }
        
        // Populate stimulus object selectors
        for (let i = 1; i <= conditionCount; i++) {
            const select = document.getElementById(`object-${i}`);
            if (select) {
                select.innerHTML = ''; // Clear existing options
                this.stimulusTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
            }
        }
    }
    
    updateControlInterface(data) {
        // Update control button states
        document.getElementById('start-condition').disabled = !data.experiment_configured;
        document.getElementById('next-condition').disabled = true;
        document.getElementById('force-next').disabled = true;
        
        // Update condition status pills
        this.updateConditionStatusPills(data.experiment_sequence, data.current_condition_index);
        
        // Update network configuration inputs
        document.getElementById('udp-ip').value = data.udp_ip;
        document.getElementById('udp-port').value = data.udp_port;
    }
    
    updateConditionStatusPills(sequence, currentIndex, countdownActive = false) {
        if (!sequence || sequence.length === 0) {
            // Reset all status pills to pending for current matrix
            const conditionCount = this.interventionTypes.length;
            for (let i = 1; i <= conditionCount; i++) {
                const statusElement = document.getElementById(`status-${i}`);
                if (statusElement) {
                    statusElement.textContent = 'Pending';
                    statusElement.className = 'px-2 py-1 text-xs rounded-full status-pending';
                }
            }
            return;
        }
        
        sequence.forEach((condition, index) => {
            const statusElement = document.getElementById(`status-${index + 1}`);
            if (statusElement) {
                if (index < currentIndex) {
                    statusElement.textContent = 'Completed';
                    statusElement.className = 'px-2 py-1 text-xs rounded-full status-completed';
                } else if (index === currentIndex) {
                    if (countdownActive) {
                        statusElement.textContent = 'Active';
                        statusElement.className = 'px-2 py-1 text-xs rounded-full status-active';
                    } else {
                        statusElement.textContent = 'Ready';
                        statusElement.className = 'px-2 py-1 text-xs rounded-full status-warning';
                    }
                } else {
                    statusElement.textContent = 'Pending';
                    statusElement.className = 'px-2 py-1 text-xs rounded-full status-pending';
                }
            }
        });
    }
    
    updateNetworkDisplay() {
        const networkDisplay = document.getElementById('current-network');
        networkDisplay.textContent = `${this.currentTargetIp}:${this.currentTargetPort}`;
    }
    
    updateProtocolState(status) {
        const statusDisplay = document.getElementById('status-display');
        statusDisplay.textContent = status;
        
        // Add subtle emphasis to status changes
        statusDisplay.style.transform = 'scale(1.02)';
        setTimeout(() => {
            statusDisplay.style.transform = 'scale(1)';
        }, 300);
    }
    
    updateConditionTimer(text) {
        const timerDisplay = document.getElementById('countdown-display');
        
        if (text.includes('Time Remaining')) {
            // Extract time from text and format
            const timeMatch = text.match(/(\d{2}):(\d{2})/);
            if (timeMatch) {
                timerDisplay.textContent = `${timeMatch[1]}:${timeMatch[2]}`;
                timerDisplay.classList.add('pulse-active');
            }
        } else if (text.includes('EXPIRED')) {
            timerDisplay.textContent = '00:00';
            timerDisplay.classList.remove('pulse-active');
        } else if (text.includes('Complete')) {
            timerDisplay.textContent = 'COMPLETE';
            timerDisplay.classList.remove('pulse-active');
        } else {
            timerDisplay.textContent = '00:00';
            timerDisplay.classList.remove('pulse-active');
        }
    }
    
    appendSystemLog(message) {
        const logDisplay = document.getElementById('log-display');
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logEntry.style.opacity = '0';
        logEntry.style.transform = 'translateY(5px)';
        
        logDisplay.appendChild(logEntry);
        logDisplay.scrollTop = logDisplay.scrollHeight;
        
        // Animate log entry appearance
        setTimeout(() => {
            logEntry.style.transition = 'all 0.2s ease';
            logEntry.style.opacity = '1';
            logEntry.style.transform = 'translateY(0)';
        }, 10);
    }
    
    showProcessingState(message = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        loadingText.textContent = message;
        overlay.classList.remove('hidden');
    }
    
    hideProcessingState() {
        const overlay = document.getElementById('loading-overlay');
        overlay.classList.add('hidden');
    }
    
    enableControl(controlId) {
        const control = document.getElementById(controlId);
        control.disabled = false;
    }
    
    disableControl(controlId) {
        const control = document.getElementById(controlId);
        control.disabled = true;
    }
    
    highlightControl(controlId) {
        const control = document.getElementById(controlId);
        control.classList.add('pulse-active');
        setTimeout(() => {
            control.classList.remove('pulse-active');
        }, 3000);
    }
    
    setupEventListeners() {
        // Configuration modal controls
        document.getElementById('open-config-modal').addEventListener('click', () => {
            this.openConfigModal();
        });
        
        document.getElementById('close-config-modal').addEventListener('click', () => {
            this.closeConfigModal();
        });
        
        document.getElementById('cancel-config-changes').addEventListener('click', () => {
            this.cancelConfigChanges();
        });
        
        document.getElementById('save-all-config').addEventListener('click', () => {
            this.saveAllConfig();
        });
        
        // Close modal when clicking outside
        document.getElementById('config-modal').addEventListener('click', (e) => {
            if (e.target.id === 'config-modal') {
                this.closeConfigModal();
            }
        });
        
        // Configuration management
        document.getElementById('add-condition-type').addEventListener('click', () => {
            this.addConditionType();
        });
        
        document.getElementById('add-object-type').addEventListener('click', () => {
            this.addObjectType();
        });
        
        // Allow adding types with Enter key
        document.getElementById('new-condition-type').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.addConditionType();
            }
        });
        
        document.getElementById('new-object-type').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.addObjectType();
            }
        });
        
        // Network configuration
        document.getElementById('update-network').addEventListener('click', () => {
            this.updateNetworkConfiguration();
        });
        
        // Session data archival
        document.getElementById('save-session').addEventListener('click', () => {
            this.archiveSessionData();
        });
        
        // Protocol configuration
        document.getElementById('set-params').addEventListener('click', () => {
            this.validateAndInitializeProtocol();
        });
        
        // Experimental controls
        document.getElementById('start-condition').addEventListener('click', () => {
            this.initiateCondition();
        });
        
        document.getElementById('next-condition').addEventListener('click', () => {
            this.progressToNextCondition();
        });
        
        document.getElementById('force-next').addEventListener('click', () => {
            this.overrideConditionTimer();
        });
        
        document.getElementById('reset-experiment').addEventListener('click', () => {
            this.resetProtocol();
        });
        
        // Modal controls
        document.getElementById('modal-close').addEventListener('click', () => {
            this.hideSystemAlert();
        });
        
        document.getElementById('confirm-cancel').addEventListener('click', () => {
            this.hideConfirmationDialog();
        });
        
        // Keyboard shortcuts for research efficiency
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        this.archiveSessionData();
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (!this.protocolConfigured) {
                            this.validateAndInitializeProtocol();
                        }
                        break;
                }
            }
            // Close config modal with Escape key
            if (e.key === 'Escape') {
                this.closeConfigModal();
            }
        });
    }
    
    openConfigModal() {
        const modal = document.getElementById('config-modal');
        modal.classList.remove('hidden');
        // Refresh the configuration lists when opening
        this.displayConditionTypes();
        this.displayObjectTypes();
    }
    
    closeConfigModal() {
        const modal = document.getElementById('config-modal');
        modal.classList.add('hidden');
    }
    
    async updateNetworkConfiguration() {
        const targetIp = document.getElementById('udp-ip').value.trim();
        const targetPort = parseInt(document.getElementById('udp-port').value);
        
        if (!targetIp || !targetPort) {
            this.showSystemAlert('Configuration Error', 'Please enter both target IP address and communication port.', 'error');
            return;
        }
        
        try {
            this.showProcessingState('Updating network configuration...');
            
            const response = await fetch(`/api/session/${this.sessionId}/network`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    udp_ip: targetIp,
                    udp_port: targetPort
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.currentTargetIp = targetIp;
                this.currentTargetPort = targetPort;
                this.updateNetworkDisplay();
                this.showSystemAlert('Configuration Updated', data.message, 'success');
            } else {
                this.showSystemAlert('Configuration Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error updating network configuration:', error);
            this.showSystemAlert('System Error', 'Failed to update network configuration.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    async archiveSessionData() {
        const groupId = document.getElementById('group-id').value;
        const researchNotes = document.getElementById('notes').value;
        
        try {
            this.showProcessingState('Archiving session data...');
            
            const response = await fetch(`/api/session/${this.sessionId}/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    group_id: groupId,
                    notes: researchNotes
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.showSystemAlert('Data Archived', data.message, 'success');
            } else {
                this.showSystemAlert('Archive Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error archiving session data:', error);
            this.showSystemAlert('System Error', 'Failed to archive session data.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    async validateAndInitializeProtocol() {
        const interventions = [];
        const stimuli = [];
        
        // Collect selected interventions and stimuli
        const conditionCount = this.interventionTypes.length;
        for (let i = 1; i <= conditionCount; i++) {
            interventions.push(document.getElementById(`condition-${i}`).value);
            stimuli.push(document.getElementById(`object-${i}`).value);
        }
        
        try {
            this.showProcessingState('Validating experimental protocol...');
            
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
                this.showSystemAlert('Protocol Validated', data.message, 'success');
                // Protocol sequence and status updates will come via WebSocket
            } else {
                this.showSystemAlert('Validation Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error validating protocol:', error);
            this.showSystemAlert('System Error', 'Failed to validate experimental protocol.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    async initiateCondition() {
        try {
            this.showProcessingState('Initiating experimental condition...');
            
            const response = await fetch(`/api/session/${this.sessionId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                // Status updates will come via WebSocket
                console.log('Condition initiated:', data.condition_name);
            } else {
                this.showSystemAlert('Initiation Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error initiating condition:', error);
            this.showSystemAlert('System Error', 'Failed to initiate experimental condition.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    async progressToNextCondition() {
        try {
            this.showProcessingState('Progressing to next condition...');
            
            const response = await fetch(`/api/session/${this.sessionId}/next`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                if (data.completed) {
                    this.showSystemAlert('Protocol Complete', data.message, 'success');
                    // Status updates will come via WebSocket
                } else {
                    // Status updates will come via WebSocket
                    console.log('Progressed to next condition:', data.condition_name);
                }
            } else {
                this.showSystemAlert('Progression Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error progressing to next condition:', error);
            this.showSystemAlert('System Error', 'Failed to progress to next condition.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    overrideConditionTimer() {
        this.showConfirmationDialog(
            'Timer Override',
            'Are you sure you want to override the condition timer and proceed immediately? This action will be logged.',
            () => this.confirmTimerOverride()
        );
    }
    
    async confirmTimerOverride() {
        this.hideConfirmationDialog();
        
        try {
            this.showProcessingState('Overriding condition timer...');
            
            const response = await fetch(`/api/session/${this.sessionId}/force-next`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.disableControl('force-next');
                this.enableControl('next-condition');
                this.highlightControl('next-condition');
            } else {
                this.showSystemAlert('Override Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error overriding timer:', error);
            this.showSystemAlert('System Error', 'Failed to override condition timer.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    resetProtocol() {
        this.showConfirmationDialog(
            'Reset Protocol',
            'Are you sure you want to reset the experimental protocol? This will clear all current configurations and cannot be undone.',
            () => this.confirmProtocolReset()
        );
    }
    
    async confirmProtocolReset() {
        this.hideConfirmationDialog();
        
        try {
            this.showProcessingState('Resetting experimental protocol...');
            
            const response = await fetch(`/api/session/${this.sessionId}/reset`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            if (data.success) {
                this.showSystemAlert('Protocol Reset', data.message, 'success');
                // Interface reset will come via WebSocket
            } else {
                this.showSystemAlert('Reset Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error resetting protocol:', error);
            this.showSystemAlert('System Error', 'Failed to reset experimental protocol.', 'error');
        } finally {
            this.hideProcessingState();
        }
    }
    
    resetInterfaceState() {
        // Reset protocol configuration
        this.protocolConfigured = false;
        
        // Reset interface elements
        const conditionCount = this.interventionTypes.length;
        for (let i = 1; i <= conditionCount; i++) {
            const conditionSelect = document.getElementById(`condition-${i}`);
            const objectSelect = document.getElementById(`object-${i}`);
            if (conditionSelect) conditionSelect.value = '';
            if (objectSelect) objectSelect.value = '';
        }
        
        // Reset control buttons
        this.disableControl('start-condition');
        this.disableControl('next-condition');
        this.disableControl('force-next');
        
        // Reset displays
        this.updateProtocolState('Standby - Awaiting Configuration');
        this.updateConditionStatusPills([], 0); // Reset status pills
        this.updateConditionTimer('');
        
        // Clear any active animations
        document.querySelectorAll('.pulse-active').forEach(el => {
            el.classList.remove('pulse-active');
        });
    }
    
    showSystemAlert(title, message, type) {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalMessage = document.getElementById('modal-message');
        const modalIcon = document.getElementById('modal-icon');
        
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        
        // Set icon based on alert type
        if (type === 'success') {
            modalIcon.className = 'fas fa-check-circle text-green-600 text-3xl mr-4';
        } else if (type === 'error') {
            modalIcon.className = 'fas fa-exclamation-circle text-red-600 text-3xl mr-4';
        } else {
            modalIcon.className = 'fas fa-info-circle text-blue-600 text-3xl mr-4';
        }
        
        modal.classList.remove('hidden');
    }
    
    hideSystemAlert() {
        document.getElementById('modal').classList.add('hidden');
    }
    
    showConfirmationDialog(title, message, onConfirm) {
        const modal = document.getElementById('confirm-modal');
        const modalTitle = document.getElementById('confirm-title');
        const modalMessage = document.getElementById('confirm-message');
        const confirmButton = document.getElementById('confirm-ok');
        
        modalTitle.textContent = title;
        modalMessage.textContent = message;
        
        // Remove any existing event listeners
        const newConfirmButton = confirmButton.cloneNode(true);
        confirmButton.parentNode.replaceChild(newConfirmButton, confirmButton);
        
        // Add new event listener
        newConfirmButton.addEventListener('click', onConfirm);
        
        modal.classList.remove('hidden');
    }
    
    hideConfirmationDialog() {
        document.getElementById('confirm-modal').classList.add('hidden');
    }
}

// Initialize the experimental control system when DOM is ready
let controlSystem;

document.addEventListener('DOMContentLoaded', () => {
    controlSystem = new VRExperimentalControlSystem();
}); 