/**
 * Settings Manager
 * Handles application settings including theme switching and experiment reset
 */

class SettingsManager {
    constructor(app) {
        this.app = app;
        this.currentTheme = 'light';
        this.settingsMenuVisible = false;
        
        this.init();
    }
    
    init() {
        // Load saved theme
        this.loadTheme();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Close settings menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.settings-button') && !e.target.closest('.settings-menu')) {
                this.hideSettingsMenu();
            }
        });
    }
    
    setupEventListeners() {
        // Settings button
        const settingsButton = document.getElementById('settings-button');
        if (settingsButton) {
            settingsButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleSettingsMenu();
            });
        }
        
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
                this.hideSettingsMenu();
            });
        }
        
        // Reset experiment
        const resetButton = document.getElementById('reset-experiment');
        if (resetButton) {
            resetButton.addEventListener('click', () => {
                this.showResetConfirmation();
                this.hideSettingsMenu();
            });
        }
    }
    
    toggleSettingsMenu() {
        const settingsMenu = document.getElementById('settings-menu');
        if (settingsMenu) {
            if (this.settingsMenuVisible) {
                this.hideSettingsMenu();
            } else {
                this.showSettingsMenu();
            }
        }
    }
    
    showSettingsMenu() {
        const settingsMenu = document.getElementById('settings-menu');
        if (settingsMenu) {
            settingsMenu.classList.remove('hidden');
            this.settingsMenuVisible = true;
        }
    }
    
    hideSettingsMenu() {
        const settingsMenu = document.getElementById('settings-menu');
        if (settingsMenu) {
            settingsMenu.classList.add('hidden');
            this.settingsMenuVisible = false;
        }
    }
    
    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.saveTheme();
    }
    
    applyTheme() {
        const body = document.body;
        const themeText = document.getElementById('theme-text');
        const themeIcon = document.querySelector('#theme-toggle i');
        
        if (this.currentTheme === 'dark') {
            body.setAttribute('data-theme', 'dark');
            if (themeText) themeText.textContent = 'Light Mode';
            if (themeIcon) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            }
        } else {
            body.removeAttribute('data-theme');
            if (themeText) themeText.textContent = 'Dark Mode';
            if (themeIcon) {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        }
    }
    
    saveTheme() {
        localStorage.setItem('vr-experiment-theme', this.currentTheme);
    }
    
    loadTheme() {
        const savedTheme = localStorage.getItem('vr-experiment-theme');
        if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
            this.currentTheme = savedTheme;
        } else {
            this.currentTheme = 'light';
        }
        this.applyTheme();
    }
    
    showResetConfirmation() {
        const confirmed = confirm(
            'Are you sure you want to reset the entire experiment?\n\n' +
            'This will:\n' +
            '• Delete all configuration files\n' +
            '• Remove all experimental variables\n' +
            '• Delete generated orders\n' +
            '• Clear all session data\n\n' +
            'This action cannot be undone!'
        );
        
        if (confirmed) {
            this.resetExperiment();
        }
    }
    
    async resetExperiment() {
        try {
            // Show loading state
            const resetButton = document.getElementById('reset-experiment');
            const originalText = resetButton.innerHTML;
            resetButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Resetting...';
            resetButton.disabled = true;
            
            // Call API to reset experiment
            const response = await fetch('/api/system/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                // Show success message
                alert('Experiment reset successfully. The page will now reload.');
                
                // Reload the page to reset the interface
                window.location.reload();
            } else {
                const error = await response.json();
                throw new Error(error.message || 'Failed to reset experiment');
            }
        } catch (error) {
            console.error('Error resetting experiment:', error);
            alert('Error resetting experiment: ' + error.message);
            
            // Restore button state
            const resetButton = document.getElementById('reset-experiment');
            resetButton.innerHTML = '<i class="fas fa-trash-alt mr-2"></i>Reset Experiment';
            resetButton.disabled = false;
        }
    }
} 