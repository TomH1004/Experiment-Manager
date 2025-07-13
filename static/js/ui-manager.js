/**
 * UI Manager
 * Handles all user interface updates, modal management, and display logic
 */

class UIManager {
    constructor(app) {
        this.app = app;
    }
    
    initialize() {
        // Initialize system time display
        this.updateSystemTime();
        setInterval(() => {
            this.updateSystemTime();
        }, 1000);
    }
    
    updateSystemTime() {
        const systemTimeElement = document.getElementById('system-time');
        if (systemTimeElement) {
            const now = new Date();
            systemTimeElement.textContent = now.toLocaleString('en-US', { 
                year: 'numeric', 
                month: '2-digit', 
                day: '2-digit', 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            });
        }
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('network-indicator');
        const statusText = document.getElementById('status-text');
        
        if (!indicator || !statusText) return;
        
        if (connected) {
            indicator.className = 'network-indicator connected';
            statusText.textContent = 'OPERATIONAL';
            statusText.className = 'text-green-600 font-medium';
        } else {
            indicator.className = 'network-indicator disconnected';
            statusText.textContent = 'DISCONNECTED';
            statusText.className = 'text-red-600 font-medium';
        }
    }
    
    updateSystemStatus(data) {
        // Update control interface
        const startConditionBtn = document.getElementById('start-condition');
        const nextConditionBtn = document.getElementById('next-condition');
        const forceNextBtn = document.getElementById('force-next');
        
        if (startConditionBtn) {
            startConditionBtn.disabled = !data.experiment_configured;
        }
        if (nextConditionBtn) {
            nextConditionBtn.disabled = true;
        }
        if (forceNextBtn) {
            forceNextBtn.disabled = true;
        }
        
        // Update condition status pills
        this.updateConditionStatusPills(data.experiment_sequence, data.current_condition_index);
        
        // Update network configuration inputs
        const udpIpInput = document.getElementById('udp-ip');
        const udpPortInput = document.getElementById('udp-port');
        
        if (udpIpInput) udpIpInput.value = data.udp_ip;
        if (udpPortInput) udpPortInput.value = data.udp_port;
        
        // Populate intervention selectors
        this.populateInterventionSelectors();
    }
    
    populateInterventionSelectors() {
        // Generate matrix first
        this.generateConditionsMatrix();
        
        const conditionCount = this.app.interventionTypes.length;
        
        // Populate intervention type selectors
        for (let i = 1; i <= conditionCount; i++) {
            const select = document.getElementById(`condition-${i}`);
            if (select) {
                select.innerHTML = ''; // Clear existing options
                this.app.interventionTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
                // Select the option at the current dropdown index
                if (this.app.interventionTypes[i - 1]) {
                    select.value = this.app.interventionTypes[i - 1];
                }
            }
        }
        
        // Populate stimulus object selectors
        for (let i = 1; i <= conditionCount; i++) {
            const select = document.getElementById(`object-${i}`);
            if (select) {
                select.innerHTML = ''; // Clear existing options
                this.app.stimulusTypes.forEach(type => {
                    const option = document.createElement('option');
                    option.value = type;
                    option.textContent = type;
                    select.appendChild(option);
                });
                // Select the option at the current dropdown index
                if (this.app.stimulusTypes[i - 1]) {
                    select.value = this.app.stimulusTypes[i - 1];
                }
            }
        }
    }
    
    generateConditionsMatrix() {
        const tbody = document.getElementById('conditions-matrix-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        const conditionCount = this.app.interventionTypes.length;
        
        for (let i = 0; i < conditionCount; i++) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td class="font-semibold">C${i + 1}</td>
                <td>
                    <select id="condition-${i + 1}" class="scientific-input w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                    </select>
                </td>
                <td>
                    <select id="object-${i + 1}" class="scientific-input w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                    </select>
                </td>
            `;
            tbody.appendChild(row);
        }
    }
    
    updateConditionStatusPills(sequence, currentIndex, countdownActive = false) {
        if (!sequence || sequence.length === 0) {
            // Reset all status pills to pending for current matrix
            const conditionCount = this.app.interventionTypes.length;
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
        if (networkDisplay) {
            networkDisplay.textContent = `${this.app.currentTargetIp}:${this.app.currentTargetPort}`;
        }
    }
    
    updateProtocolState(status) {
        const statusDisplay = document.getElementById('status-display');
        if (statusDisplay) {
            statusDisplay.textContent = status;
            
            // Add subtle emphasis to status changes
            statusDisplay.style.transform = 'scale(1.02)';
            setTimeout(() => {
                statusDisplay.style.transform = 'scale(1)';
            }, 300);
        }
    }
    
    updateConditionTimer(text) {
        const timerDisplay = document.getElementById('countdown-display');
        if (!timerDisplay) return;
        
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
        if (!logDisplay) return;
        
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
    
    // Processing state methods
    showProcessingState(message = 'Processing...') {
        const overlay = document.getElementById('loading-overlay');
        const loadingText = document.getElementById('loading-text');
        
        if (overlay && loadingText) {
            loadingText.textContent = message;
            overlay.classList.remove('hidden');
        }
    }
    
    hideProcessingState() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
        }
    }
    
    // Control state methods
    enableControl(controlId) {
        const control = document.getElementById(controlId);
        if (control) {
            control.disabled = false;
        }
    }
    
    disableControl(controlId) {
        const control = document.getElementById(controlId);
        if (control) {
            control.disabled = true;
        }
    }
    
    highlightControl(controlId) {
        const control = document.getElementById(controlId);
        if (control) {
            control.classList.add('pulse-active');
            setTimeout(() => {
                control.classList.remove('pulse-active');
            }, 3000);
        }
    }
    
    resetInterfaceState() {
        // Reset protocol configuration
        this.app.protocolConfigured = false;
        
        // Reset interface elements
        const conditionCount = this.app.interventionTypes.length;
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
    
    // Modal management methods
    showSystemAlert(title, message, type) {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalMessage = document.getElementById('modal-message');
        const modalIcon = document.getElementById('modal-icon');
        
        if (!modal || !modalTitle || !modalMessage || !modalIcon) return;
        
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
        const modal = document.getElementById('modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    showConfirmationDialog(title, message, onConfirm) {
        const modal = document.getElementById('confirm-modal');
        const modalTitle = document.getElementById('confirm-title');
        const modalMessage = document.getElementById('confirm-message');
        const confirmButton = document.getElementById('confirm-ok');
        
        if (!modal || !modalTitle || !modalMessage || !confirmButton) return;
        
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
        const modal = document.getElementById('confirm-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    // Configuration modal methods
    openConfigModal() {
        const modal = document.getElementById('config-modal');
        if (modal) {
            modal.classList.remove('hidden');
            // Refresh the configuration lists when opening
            this.app.configManager.displayConditionTypes();
            this.app.configManager.displayObjectTypes();
        }
    }
    
    closeConfigModal() {
        const modal = document.getElementById('config-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    // Order generator modal methods
    openOrderGenerator() {
        this.app.orderManager.openOrderGenerator();
    }
    
    closeOrderGenerator() {
        this.app.orderManager.closeOrderGenerator();
    }
    
    // First-time setup methods
    showFirstTimeSetup() {
        const modal = document.getElementById('first-time-setup-modal');
        if (modal) {
            modal.classList.remove('hidden');
            this.app.configManager.setupEventListenersForSetup();
        }
    }
} 