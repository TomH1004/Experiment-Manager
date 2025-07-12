#!/usr/bin/env python3
"""
Run script for VR Experiment Supervisor Web Application
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False
    return True

def start_application():
    """Start the Flask application"""
    print("Starting VR Experiment Supervisor Web Application...")
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Import and run the app
        from app import socketio, app
        socketio.run(app, debug=True, host='0.0.0.0', port=5000)
    except ImportError as e:
        print(f"Error importing application: {e}")
        print("Make sure all dependencies are installed correctly.")
        return False
    except KeyboardInterrupt:
        print("\nApplication stopped by user.")
        return True
    except Exception as e:
        print(f"Error starting application: {e}")
        return False

def main():
    """Main function"""
    print("VR Experiment Supervisor Web Application")
    print("=" * 50)
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found!")
        print("Make sure you're running this script from the project directory.")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Start the application
    if not start_application():
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 