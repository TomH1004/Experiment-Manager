#!/usr/bin/env python3
"""
VR Experiment Manager Launcher
Starts the Flask application and automatically opens the browser.
"""

import os
import sys
import time
import webbrowser
import threading
from src.app import app, socketio, logger

def open_browser():
    """Open the browser to the application URL after a short delay"""
    time.sleep(2)  # Wait for the server to start
    url = "http://localhost:5000"
    logger.info(f"Opening browser to {url}")
    webbrowser.open(url)

def main():
    """Main function to start the application"""
    try:
        # Log startup
        logger.info("=" * 50)
        logger.info("VR Experiment Manager Starting Up")
        logger.info("=" * 50)
        
        # Start browser opening thread
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Start the Flask-SocketIO server
        logger.info("Starting server on http://localhost:5000")
        print("VR Experiment Manager is starting...")
        print("Opening browser automatically...")
        print("Press Ctrl+C to stop the server")
        
        socketio.run(app, debug=False, host='0.0.0.0', port=5000, log_output=False)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\nServer stopped.")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 