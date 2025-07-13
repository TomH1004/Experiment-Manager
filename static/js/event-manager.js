/**
 * Event Manager
 * Handles all DOM event listeners and user interactions
 */

class EventManager {
    constructor(app) {
        this.app = app;
    }
    
    initialize() {
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Configuration modal controls
        this.setupConfigurationEvents();
        
        // Order generator modal controls
        this.setupOrderGeneratorEvents();
        
        // Network configuration events
        this.setupNetworkEvents();
        
        // Session management events
        this.setupSessionEvents();
        
        // Protocol configuration events
        this.setupProtocolEvents();
        
        // Experimental control events
        this.setupExperimentalControlEvents();
        
        // Modal control events
        this.setupModalEvents();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    setupConfigurationEvents() {
        // Configuration modal controls
        const openConfigModal = document.getElementById('open-config-modal');
        const closeConfigModal = document.getElementById('close-config-modal');
        const cancelConfigChanges = document.getElementById('cancel-config-changes');
        const saveAllConfig = document.getElementById('save-all-config');
        
        if (openConfigModal) {
            openConfigModal.addEventListener('click', () => {
                this.app.uiManager.openConfigModal();
            });
        }
        
        if (closeConfigModal) {
            closeConfigModal.addEventListener('click', () => {
                this.app.uiManager.closeConfigModal();
            });
        }
        
        if (cancelConfigChanges) {
            cancelConfigChanges.addEventListener('click', () => {
                this.app.configManager.cancelConfigChanges();
            });
        }
        
        if (saveAllConfig) {
            saveAllConfig.addEventListener('click', () => {
                this.app.configManager.saveAllConfig();
            });
        }
        
        // Close modal when clicking outside
        const configModal = document.getElementById('config-modal');
        if (configModal) {
            configModal.addEventListener('click', (e) => {
                if (e.target.id === 'config-modal') {
                    this.app.uiManager.closeConfigModal();
                }
            });
        }
        
        // Configuration management
        const addConditionType = document.getElementById('add-condition-type');
        const addObjectType = document.getElementById('add-object-type');
        
        if (addConditionType) {
            addConditionType.addEventListener('click', () => {
                this.app.configManager.addConditionType();
            });
        }
        
        if (addObjectType) {
            addObjectType.addEventListener('click', () => {
                this.app.configManager.addObjectType();
            });
        }
        
        // Update variable names button
        const updateVariableNames = document.getElementById('update-variable-names');
        if (updateVariableNames) {
            updateVariableNames.addEventListener('click', () => {
                this.app.configManager.updateVariableNamesConfig();
            });
        }
        
        // Allow adding types with Enter key
        const newConditionType = document.getElementById('new-condition-type');
        const newObjectType = document.getElementById('new-object-type');
        
        if (newConditionType) {
            newConditionType.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.app.configManager.addConditionType();
                }
            });
        }
        
        if (newObjectType) {
            newObjectType.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.app.configManager.addObjectType();
                }
            });
        }
    }
    
    setupOrderGeneratorEvents() {
        // Order generator modal controls
        const openOrderGenerator = document.getElementById('open-order-generator');
        const closeOrderGenerator = document.getElementById('close-order-generator');
        const closeOrderGeneratorBtn = document.getElementById('close-order-generator-btn');
        const generateAllOrders = document.getElementById('generate-all-orders');
        const hideUsedOrders = document.getElementById('hide-used-orders');
        const resetOrderUses = document.getElementById('reset-order-uses');
        
        if (openOrderGenerator) {
            openOrderGenerator.addEventListener('click', () => {
                this.app.uiManager.openOrderGenerator();
            });
        }
        
        if (closeOrderGenerator) {
            closeOrderGenerator.addEventListener('click', () => {
                this.app.uiManager.closeOrderGenerator();
            });
        }
        
        if (closeOrderGeneratorBtn) {
            closeOrderGeneratorBtn.addEventListener('click', () => {
                this.app.uiManager.closeOrderGenerator();
            });
        }
        
        if (generateAllOrders) {
            generateAllOrders.addEventListener('click', () => {
                this.app.orderManager.generateAllOrders();
            });
        }
        
        if (hideUsedOrders) {
            hideUsedOrders.addEventListener('change', () => {
                this.app.orderManager.filterOrdersDisplay();
            });
        }
        
        if (resetOrderUses) {
            resetOrderUses.addEventListener('click', () => {
                this.app.orderManager.resetOrderUses();
            });
        }
        
        // Close order generator modal when clicking outside
        const orderGeneratorModal = document.getElementById('order-generator-modal');
        if (orderGeneratorModal) {
            orderGeneratorModal.addEventListener('click', (e) => {
                if (e.target.id === 'order-generator-modal') {
                    this.app.uiManager.closeOrderGenerator();
                }
            });
        }
    }
    
    setupNetworkEvents() {
        // Network configuration
        const updateNetwork = document.getElementById('update-network');
        if (updateNetwork) {
            updateNetwork.addEventListener('click', () => {
                const udpIp = document.getElementById('udp-ip').value.trim();
                const udpPort = parseInt(document.getElementById('udp-port').value);
                this.app.updateNetworkConfiguration(udpIp, udpPort);
            });
        }
    }
    
    setupSessionEvents() {
        // Session data archival
        const saveSession = document.getElementById('save-session');
        if (saveSession) {
            saveSession.addEventListener('click', () => {
                const groupId = document.getElementById('group-id').value;
                const notes = document.getElementById('notes').value;
                this.app.saveSessionData(groupId, notes);
            });
        }
    }
    
    setupProtocolEvents() {
        // Protocol configuration
        const setParams = document.getElementById('set-params');
        if (setParams) {
            setParams.addEventListener('click', () => {
                this.app.validateAndInitializeProtocol();
            });
        }
    }
    
    setupExperimentalControlEvents() {
        // Experimental controls
        const startCondition = document.getElementById('start-condition');
        const nextCondition = document.getElementById('next-condition');
        const forceNext = document.getElementById('force-next');
        const resetExperiment = document.getElementById('reset-experiment');
        
        if (startCondition) {
            startCondition.addEventListener('click', () => {
                this.app.startCondition();
            });
        }
        
        if (nextCondition) {
            nextCondition.addEventListener('click', () => {
                this.app.nextCondition();
            });
        }
        
        if (forceNext) {
            forceNext.addEventListener('click', () => {
                this.showForceNextConfirmation();
            });
        }
        
        if (resetExperiment) {
            resetExperiment.addEventListener('click', () => {
                this.showResetExperimentConfirmation();
            });
        }
    }
    
    setupModalEvents() {
        // Modal controls
        const modalClose = document.getElementById('modal-close');
        const confirmCancel = document.getElementById('confirm-cancel');
        
        if (modalClose) {
            modalClose.addEventListener('click', () => {
                this.app.uiManager.hideSystemAlert();
            });
        }
        
        if (confirmCancel) {
            confirmCancel.addEventListener('click', () => {
                this.app.uiManager.hideConfirmationDialog();
            });
        }
    }
    
    setupKeyboardShortcuts() {
        // Keyboard shortcuts for research efficiency
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 's':
                        e.preventDefault();
                        const groupId = document.getElementById('group-id').value;
                        const notes = document.getElementById('notes').value;
                        this.app.saveSessionData(groupId, notes);
                        break;
                    case 'Enter':
                        e.preventDefault();
                        if (!this.app.protocolConfigured) {
                            this.app.validateAndInitializeProtocol();
                        }
                        break;
                }
            }
            // Close modals with Escape key
            if (e.key === 'Escape') {
                this.app.uiManager.closeConfigModal();
                this.app.uiManager.closeOrderGenerator();
            }
        });
    }
    
    // Helper methods for confirmations
    showForceNextConfirmation() {
        this.app.uiManager.showConfirmationDialog(
            'Timer Override',
            'Are you sure you want to override the condition timer and proceed immediately? This action will be logged.',
            () => {
                this.app.uiManager.hideConfirmationDialog();
                this.app.forceNextCondition();
            }
        );
    }
    
    showResetExperimentConfirmation() {
        this.app.uiManager.showConfirmationDialog(
            'Reset Protocol',
            'Are you sure you want to reset the experimental protocol? This will clear all current configurations and cannot be undone.',
            () => {
                this.app.uiManager.hideConfirmationDialog();
                this.app.resetExperiment();
            }
        );
    }
} 