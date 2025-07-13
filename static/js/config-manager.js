/**
 * Configuration Manager
 * Handles all configuration-related functionality including variable types, metadata, and validation
 */

class ConfigurationManager {
    constructor(app) {
        this.app = app;
        
        // Configuration state
        this.currentConditionTypes = [];
        this.currentObjectTypes = [];
        this.pendingConditionTypes = [];
        this.pendingObjectTypes = [];
        
        // First-time setup state
        this.setupVariable1Values = [];
        this.setupVariable2Values = [];
    }
    
    async initialize() {
        await this.loadConfigurations();
    }
    
    async loadConfigurations() {
        try {
            // Load metadata first
            const metadataResponse = await fetch('/api/config/metadata');
            const metadataData = await metadataResponse.json();
            if (metadataData.success) {
                this.app.metadata = metadataData.metadata;
                this.updateVariableNames();
            }
            
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
    
    updateVariableNames() {
        // Update UI elements with dynamic variable names
        if (this.app.metadata.variable1_name) {
            const variable1Title = document.getElementById('variable1-title');
            const matrixHeader1 = document.getElementById('matrix-header-variable1');
            
            if (variable1Title) {
                variable1Title.textContent = this.app.metadata.variable1_plural || 'Variable 1';
            }
            if (matrixHeader1) {
                matrixHeader1.textContent = this.app.metadata.variable1_name || 'Variable 1';
            }
            
            // Update placeholders
            const newConditionInput = document.getElementById('new-condition-type');
            if (newConditionInput) {
                newConditionInput.placeholder = `Add new ${this.app.metadata.variable1_name.toLowerCase()}...`;
            }
        }
        
        if (this.app.metadata.variable2_name) {
            const variable2Title = document.getElementById('variable2-title');
            const matrixHeader2 = document.getElementById('matrix-header-variable2');
            
            if (variable2Title) {
                variable2Title.textContent = this.app.metadata.variable2_plural || 'Variable 2';
            }
            if (matrixHeader2) {
                matrixHeader2.textContent = this.app.metadata.variable2_name || 'Variable 2';
            }
            
            // Update placeholders
            const newObjectInput = document.getElementById('new-object-type');
            if (newObjectInput) {
                newObjectInput.placeholder = `Add new ${this.app.metadata.variable2_name.toLowerCase()}...`;
            }
        }
        
        // Update variable name inputs in config modal
        const variable1Name = document.getElementById('variable1-name');
        const variable1Plural = document.getElementById('variable1-plural');
        const variable2Name = document.getElementById('variable2-name');
        const variable2Plural = document.getElementById('variable2-plural');
        
        if (variable1Name) variable1Name.value = this.app.metadata.variable1_name || '';
        if (variable1Plural) variable1Plural.value = this.app.metadata.variable1_plural || '';
        if (variable2Name) variable2Name.value = this.app.metadata.variable2_name || '';
        if (variable2Plural) variable2Plural.value = this.app.metadata.variable2_plural || '';
    }
    
    displayConditionTypes() {
        const container = document.getElementById('condition-types-list');
        const countElement = document.getElementById('condition-count');
        
        if (!container || !countElement) return;
        
        container.innerHTML = '';
        
        this.pendingConditionTypes.forEach((type, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between bg-white px-3 py-2 border border-gray-200 rounded-md';
            item.innerHTML = `
                <span class="text-sm font-medium text-gray-700">${type}</span>
                <div class="flex space-x-2">
                    <button class="text-red-600 hover:text-red-800 text-sm" onclick="vrExperimentManager.configManager.removeConditionType(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="text-red-600 hover:text-red-800 text-sm" onclick="vrExperimentManager.configManager.deleteConditionType('${type}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            container.appendChild(item);
        });
        
        countElement.textContent = `(${this.pendingConditionTypes.length})`;
        this.validateConfiguration();
    }
    
    displayObjectTypes() {
        const container = document.getElementById('object-types-list');
        const countElement = document.getElementById('object-count');
        
        if (!container || !countElement) return;
        
        container.innerHTML = '';
        
        this.pendingObjectTypes.forEach((type, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between bg-white px-3 py-2 border border-gray-200 rounded-md';
            item.innerHTML = `
                <span class="text-sm font-medium text-gray-700">${type}</span>
                <div class="flex space-x-2">
                    <button class="text-red-600 hover:text-red-800 text-sm" onclick="vrExperimentManager.configManager.removeObjectType(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                    <button class="text-red-600 hover:text-red-800 text-sm" onclick="vrExperimentManager.configManager.deleteObjectType('${type}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
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
        
        if (!messageElement || !textElement || !saveButton) return;
        
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
        if (!input) return;
        
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
    
    async deleteConditionType(type) {
        this.app.uiManager.showConfirmationDialog(
            'Delete Condition Type',
            `Are you sure you want to delete the condition type "${type}"? This action cannot be undone.`,
            async () => {
                this.app.uiManager.hideConfirmationDialog();
                try {
                    this.app.uiManager.showProcessingState('Deleting condition type...');
                    const response = await fetch('/api/config/condition-types', {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            condition_type: type
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        this.app.uiManager.showSystemAlert('Condition Type Deleted', data.message, 'success');
                        this.currentConditionTypes = data.condition_types;
                        this.pendingConditionTypes = [...data.condition_types];
                        this.displayConditionTypes();
                        this.validateConfiguration();
                    } else {
                        this.app.uiManager.showSystemAlert('Delete Error', data.message, 'error');
                    }
                } catch (error) {
                    console.error('Error deleting condition type:', error);
                    this.app.uiManager.showSystemAlert('System Error', 'Failed to delete condition type.', 'error');
                } finally {
                    this.app.uiManager.hideProcessingState();
                }
            }
        );
    }
    
    addObjectType() {
        const input = document.getElementById('new-object-type');
        if (!input) return;
        
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
    
    async deleteObjectType(type) {
        this.app.uiManager.showConfirmationDialog(
            'Delete Object Type',
            `Are you sure you want to delete the object type "${type}"? This action cannot be undone.`,
            async () => {
                this.app.uiManager.hideConfirmationDialog();
                try {
                    this.app.uiManager.showProcessingState('Deleting object type...');
                    const response = await fetch('/api/config/object-types', {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            object_type: type
                        })
                    });
                    const data = await response.json();
                    if (data.success) {
                        this.app.uiManager.showSystemAlert('Object Type Deleted', data.message, 'success');
                        this.currentObjectTypes = data.object_types;
                        this.pendingObjectTypes = [...data.object_types];
                        this.displayObjectTypes();
                        this.validateConfiguration();
                    } else {
                        this.app.uiManager.showSystemAlert('Delete Error', data.message, 'error');
                    }
                } catch (error) {
                    console.error('Error deleting object type:', error);
                    this.app.uiManager.showSystemAlert('System Error', 'Failed to delete object type.', 'error');
                } finally {
                    this.app.uiManager.hideProcessingState();
                }
            }
        );
    }
    
    async saveAllConfig() {
        try {
            this.app.uiManager.showProcessingState('Saving configuration changes...');
            
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
                this.app.uiManager.closeConfigModal();
                
                // Show success message briefly before reload
                this.app.uiManager.showSystemAlert('Configuration Updated', 'All changes saved successfully. Reloading interface...', 'success');
                
                // Reload page after short delay
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                const errorMessage = !conditionData.success ? conditionData.message : objectData.message;
                this.app.uiManager.showSystemAlert('Save Error', errorMessage, 'error');
            }
        } catch (error) {
            console.error('Error saving configurations:', error);
            this.app.uiManager.showSystemAlert('System Error', 'Failed to save configuration changes.', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
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
        this.app.uiManager.closeConfigModal();
    }
    
    async updateVariableNamesConfig() {
        try {
            const variable1Name = document.getElementById('variable1-name').value.trim();
            const variable1Plural = document.getElementById('variable1-plural').value.trim();
            const variable2Name = document.getElementById('variable2-name').value.trim();
            const variable2Plural = document.getElementById('variable2-plural').value.trim();
            
            if (!variable1Name || !variable1Plural || !variable2Name || !variable2Plural) {
                this.app.uiManager.showSystemAlert('Update Error', 'All variable names are required.', 'error');
                return;
            }
            
            this.app.uiManager.showProcessingState('Updating variable names...');
            
            const metadata = {
                ...this.app.metadata,
                variable1_name: variable1Name,
                variable1_plural: variable1Plural,
                variable2_name: variable2Name,
                variable2_plural: variable2Plural
            };
            
            const response = await fetch('/api/config/metadata', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ metadata })
            });
            
            const data = await response.json();
            if (data.success) {
                this.app.metadata = data.metadata;
                this.updateVariableNames();
                this.app.uiManager.showSystemAlert('Variable Names Updated', 'Variable names have been updated successfully.', 'success');
            } else {
                this.app.uiManager.showSystemAlert('Update Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error updating variable names:', error);
            this.app.uiManager.showSystemAlert('System Error', 'Failed to update variable names.', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
    
    // First-time setup methods
    setupEventListenersForSetup() {
        // Variable name change listeners
        const setupVariable1Name = document.getElementById('setup-variable1-name');
        const setupVariable2Name = document.getElementById('setup-variable2-name');
        
        if (setupVariable1Name) {
            setupVariable1Name.addEventListener('input', () => {
                this.updateSetupTitles();
            });
        }
        
        if (setupVariable2Name) {
            setupVariable2Name.addEventListener('input', () => {
                this.updateSetupTitles();
            });
        }
        
        // Add value buttons
        const setupAddVariable1 = document.getElementById('setup-add-variable1');
        const setupAddVariable2 = document.getElementById('setup-add-variable2');
        
        if (setupAddVariable1) {
            setupAddVariable1.addEventListener('click', () => {
                this.addSetupVariable1();
            });
        }
        
        if (setupAddVariable2) {
            setupAddVariable2.addEventListener('click', () => {
                this.addSetupVariable2();
            });
        }
        
        // Enter key support
        const setupNewVariable1 = document.getElementById('setup-new-variable1');
        const setupNewVariable2 = document.getElementById('setup-new-variable2');
        
        if (setupNewVariable1) {
            setupNewVariable1.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.addSetupVariable1();
                }
            });
        }
        
        if (setupNewVariable2) {
            setupNewVariable2.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.addSetupVariable2();
                }
            });
        }
        
        // Complete setup button
        const completeSetup = document.getElementById('complete-setup');
        if (completeSetup) {
            completeSetup.addEventListener('click', () => {
                this.completeFirstTimeSetup();
            });
        }
    }
    
    updateSetupTitles() {
        const var1Name = document.getElementById('setup-variable1-name').value || 'First Variable';
        const var2Name = document.getElementById('setup-variable2-name').value || 'Second Variable';
        
        const setupVariable1Title = document.getElementById('setup-variable1-title');
        const setupVariable2Title = document.getElementById('setup-variable2-title');
        
        if (setupVariable1Title) {
            setupVariable1Title.textContent = `${var1Name} Values`;
        }
        
        if (setupVariable2Title) {
            setupVariable2Title.textContent = `${var2Name} Values`;
        }
    }
    
    addSetupVariable1() {
        const input = document.getElementById('setup-new-variable1');
        if (!input) return;
        
        const value = input.value.trim();
        
        if (value && !this.setupVariable1Values.includes(value)) {
            this.setupVariable1Values.push(value);
            input.value = '';
            this.displaySetupVariable1();
            this.validateSetup();
        }
    }
    
    addSetupVariable2() {
        const input = document.getElementById('setup-new-variable2');
        if (!input) return;
        
        const value = input.value.trim();
        
        if (value && !this.setupVariable2Values.includes(value)) {
            this.setupVariable2Values.push(value);
            input.value = '';
            this.displaySetupVariable2();
            this.validateSetup();
        }
    }
    
    displaySetupVariable1() {
        const container = document.getElementById('setup-variable1-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.setupVariable1Values.forEach((value, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between bg-white px-3 py-2 border border-gray-200 rounded-md';
            item.innerHTML = `
                <span class="text-sm font-medium text-gray-700">${value}</span>
                <button class="text-red-600 hover:text-red-800 text-sm" onclick="vrExperimentManager.configManager.removeSetupVariable1(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
    }
    
    displaySetupVariable2() {
        const container = document.getElementById('setup-variable2-list');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.setupVariable2Values.forEach((value, index) => {
            const item = document.createElement('div');
            item.className = 'flex items-center justify-between bg-white px-3 py-2 border border-gray-200 rounded-md';
            item.innerHTML = `
                <span class="text-sm font-medium text-gray-700">${value}</span>
                <button class="text-red-600 hover:text-red-800 text-sm" onclick="vrExperimentManager.configManager.removeSetupVariable2(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
    }
    
    removeSetupVariable1(index) {
        this.setupVariable1Values.splice(index, 1);
        this.displaySetupVariable1();
        this.validateSetup();
    }
    
    removeSetupVariable2(index) {
        this.setupVariable2Values.splice(index, 1);
        this.displaySetupVariable2();
        this.validateSetup();
    }
    
    validateSetup() {
        const messageElement = document.getElementById('setup-validation-message');
        const textElement = document.getElementById('setup-validation-text');
        const completeButton = document.getElementById('complete-setup');
        
        if (!messageElement || !textElement || !completeButton) return;
        
        const var1Count = this.setupVariable1Values.length;
        const var2Count = this.setupVariable2Values.length;
        
        if (var1Count === 0 || var2Count === 0) {
            messageElement.className = 'p-3 rounded-md bg-red-50 border border-red-200 text-red-700';
            textElement.textContent = 'Both variables must have at least one value.';
            messageElement.classList.remove('hidden');
            completeButton.disabled = true;
            completeButton.classList.add('opacity-50', 'cursor-not-allowed');
        } else if (var1Count !== var2Count) {
            messageElement.className = 'p-3 rounded-md bg-orange-50 border border-orange-200 text-orange-700';
            textElement.textContent = `Number of values must match (${var1Count} vs ${var2Count}).`;
            messageElement.classList.remove('hidden');
            completeButton.disabled = true;
            completeButton.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            messageElement.classList.add('hidden');
            completeButton.disabled = false;
            completeButton.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }
    
    async completeFirstTimeSetup() {
        try {
            const variable1Name = document.getElementById('setup-variable1-name').value.trim();
            const variable1Plural = document.getElementById('setup-variable1-plural').value.trim();
            const variable2Name = document.getElementById('setup-variable2-name').value.trim();
            const variable2Plural = document.getElementById('setup-variable2-plural').value.trim();
            
            if (!variable1Name || !variable1Plural || !variable2Name || !variable2Plural) {
                this.app.uiManager.showSystemAlert('Setup Error', 'All variable names are required.', 'error');
                return;
            }
            
            this.app.uiManager.showProcessingState('Completing setup...');
            
            const response = await fetch('/api/config/first-time-setup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    variable1_name: variable1Name,
                    variable1_plural: variable1Plural,
                    variable2_name: variable2Name,
                    variable2_plural: variable2Plural,
                    variable1_values: this.setupVariable1Values,
                    variable2_values: this.setupVariable2Values
                })
            });
            
            const data = await response.json();
            if (data.success) {
                this.app.metadata = data.metadata;
                this.app.uiManager.showSystemAlert('Setup Complete', 'Your experiment configuration has been saved successfully!', 'success');
                
                // Hide setup modal and reload
                document.getElementById('first-time-setup-modal').classList.add('hidden');
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                this.app.uiManager.showSystemAlert('Setup Error', data.message, 'error');
            }
        } catch (error) {
            console.error('Error completing setup:', error);
            this.app.uiManager.showSystemAlert('System Error', 'Failed to complete setup.', 'error');
        } finally {
            this.app.uiManager.hideProcessingState();
        }
    }
} 