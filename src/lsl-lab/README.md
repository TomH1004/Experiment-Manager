# LSL-Lab Remote Control - Polar H10 Data Acquisition System

This application provides real-time physiological data acquisition from Polar H10 devices with integrated remote control capabilities for VR experiment coordination.

## Features

- **Real-time Heart Rate Monitoring**: Live heart rate and RR interval data from Polar H10
- **Lab Streaming Layer (LSL)**: Real-time data streaming for external applications
- **Remote HTTP API**: REST API for remote control from VR Experiment Manager
- **Data Recording**: Automatic data logging with participant session management
- **Interval Management**: Start/stop data collection intervals for experimental conditions
- **Modern GUI**: Dark-themed interface with real-time data visualization

## Installation

### Prerequisites

- Python 3.8 or higher
- Polar H10 heart rate monitor
- Bluetooth Low Energy (BLE) support on your computer

### Setup

1. **Clone or download** this LSL-Lab application to your computer

2. **Install dependencies**:
   ```bash
   cd src/lsl-lab
   pip install -r requirements.txt
   ```

3. **Verify installation** by running the test script:
   ```bash
   python test_remote_api.py
   ```

## Usage

### Basic Operation

1. **Start the application**:
   ```bash
   python LSL-Lab_Remote.py
   ```

2. **Connect to Polar H10**:
   - Power on your Polar H10 device
   - Moisten the chest strap electrodes
   - Click "SCAN" to find your device
   - Select your device and click "CONNECT"

3. **Set Participant ID**:
   - Enter a unique participant identifier
   - Click "SET ID" to create a new session

4. **Start Recording**:
   - Click "START RECORDING" to begin data collection
   - Use "MARK TIMESTAMP" and interval controls as needed
   - Click "STOP RECORDING" when finished

### Remote Control Integration

The application automatically starts a remote control API server on **port 8080** when launched.

#### Testing Remote Control

Use the provided test script to verify remote control functionality:

```bash
# Test local instance
python test_remote_api.py

# Test remote instance
python test_remote_api.py 192.168.1.100
``` 