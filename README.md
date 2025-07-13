# VR Experiment Manager

A web-based control system for managing VR experiments with customizable variables and balanced experimental design.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```
The browser will open automatically at `http://localhost:5000`

### 3. First-Time Setup
1. Define your experimental variables (e.g., "Condition Type" and "Object Type")
2. Add values for each variable (e.g., "Condition A, Condition B, Condition C" and "Object 1, Object 2, Object 3")
3. Generate experimental orders
4. Start your experiment

## Project Structure

```
VR-Experiment-Manager/
├── run.py                          # Main launcher (auto-opens browser)
├── vr_experiment_supervisor.py     # Legacy GUI application (Tkinter)
├── VRExperimentReceiver.cs         # Unity C# script for receiving UDP messages
├── Unity_Setup_Guide.md            # Guide for setting up Unity integration
├── requirements.txt                # Python dependencies
├── src/                            # Main application source code
│   ├── __init__.py                 # Package initialization
│   ├── app.py                      # Flask application and WebSocket setup
│   ├── experiment_manager.py       # Core experiment management logic
│   ├── api_routes.py               # Main API endpoints (session management)
│   ├── config_routes.py            # Configuration management endpoints
│   └── order_routes.py             # Order generation and management endpoints
├── static/                         # Web interface files
│   ├── index.html                  # Main web interface
│   ├── styles.css                  # CSS styling
│   └── js/                         # JavaScript modules
│       ├── app.js                  # Main application logic
│       ├── config-manager.js       # Variable configuration management
│       ├── order-manager.js        # Order generation and selection
│       ├── ui-manager.js           # UI state management
│       ├── websocket-manager.js    # WebSocket communication
│       └── event-manager.js        # Event handling
├── config/                         # Auto-created configuration files
│   ├── metadata.json               # Variable names and settings
│   ├── <variable1_name>.json       # Variable 1 values (e.g., condition_types.json)
│   ├── <variable2_name>.json       # Variable 2 values (e.g., object_types.json)
│   └── orders.json                 # Generated experimental orders
├── data/                           # Auto-created session exports
├── logs/                           # Auto-created log files
└── .venv/                          # Virtual environment (if using)
```

## Script Descriptions

### Core Application Scripts

#### `run.py`
Main launcher script that:
- Starts the Flask application with WebSocket support
- Automatically opens the browser to `http://localhost:5000`
- Handles graceful shutdown on Ctrl+C
- Sets up logging and error handling

#### `src/app.py`
Flask application setup and WebSocket management:
- Initializes Flask app with correct template/static directories
- Sets up WebSocket (SocketIO) for real-time communication
- Configures logging with rotating file handler
- Implements enhanced timer management with WebSocket integration
- Handles session management and real-time updates to the web interface

#### `src/experiment_manager.py`
Core experiment management logic:
- Session creation and management
- Configuration loading/saving (variables, orders, metadata)
- UDP message broadcasting to VR applications
- Order generation using Latin Square design
- Experiment sequence management
- Session data export functionality

#### `src/api_routes.py`
Main API endpoints for session management:
- Session creation and status endpoints
- Experiment configuration and validation
- Condition start/next/force-next controls
- Session data saving and export
- Network settings management

#### `src/config_routes.py`
Configuration management endpoints:
- Variable definition and management
- Metadata configuration (variable names, display settings)
- Configuration validation and saving
- Variable value management (condition types, object types)

#### `src/order_routes.py`
Order generation and management:
- Latin Square order generation
- Order selection and marking as used
- Order validation and management
- Balanced experimental design creation

### Legacy Scripts

#### `vr_experiment_supervisor.py`
Legacy GUI application (Tkinter-based):
- Provides a desktop interface for experiment control
- Maintained for backward compatibility
- Offers similar functionality to the web interface
- Can be used as a standalone application

### Unity Integration

#### `VRExperimentReceiver.cs`
Unity C# script for receiving UDP messages:
- Handles UDP communication from the web application
- Manages GameObject activation based on experiment conditions
- Supports condition and object type combinations
- Provides debugging and status feedback

### Frontend JavaScript Modules

#### `static/js/app.js`
Main application logic:
- Coordinates between all JavaScript modules
- Handles application initialization
- Manages global state and configuration

#### `static/js/config-manager.js`
Variable configuration management:
- Handles variable definition and editing
- Manages metadata configuration
- Provides validation for variable settings

#### `static/js/order-manager.js`
Order generation and selection:
- Generates Latin Square experimental orders
- Handles order selection and marking
- Manages order validation

#### `static/js/ui-manager.js`
UI state management:
- Updates interface based on experiment state
- Handles button states and visibility
- Manages status displays and countdown timers

#### `static/js/websocket-manager.js`
WebSocket communication:
- Handles real-time communication with Flask backend
- Manages WebSocket connection and reconnection
- Processes real-time updates (timers, status changes)

#### `static/js/event-manager.js`
Event handling:
- Manages UI event listeners
- Handles form submissions and button clicks
- Coordinates between UI components

## UDP Communication

The system sends UDP broadcast messages to VR applications on port `1221` (configurable).

### Message Structure
```json
{
  "command": "start_condition",
  "condition_type": "condition_a",
  "object_type": "object_1",
  "condition_index": 0
}
```

### Available Commands
- `start_condition` - Begin new experimental condition
- `next_condition` - Progress to next condition  
- `disable_all` - Disable all VR objects (timer expired)

### Example UDP Messages
```json
// Starting first condition
{
  "command": "start_condition",
  "condition_type": "condition_a",
  "object_type": "object_1",
  "condition_index": 0
}

// Timer expired
{
  "command": "disable_all",
  "reason": "timer_expired"
}
```

## Balanced Experimental Design

The system generates balanced experimental orders using Latin Square design principles:

### Example Configuration
- **Variable 1**: Condition Type (3 values: A, B, C)
- **Variable 2**: Object Type (3 values: 1, 2, 3)
- **Result**: 18 balanced orders controlling for sequence effects

### Benefits
- Counterbalanced design controls for order effects
- Reduces from factorial complexity (3! × 3! = 36) to manageable count (18 orders)

## Usage Example

### 1. Setup Variables
```
Variable 1: "Condition Type" (singular), "Condition Types" (plural)
Values: ["Condition A", "Condition B", "Condition C"]

Variable 2: "Object Type" (singular), "Object Types" (plural)  
Values: ["Object 1", "Object 2", "Object 3"]
```

### 2. Generate Orders
Click "Generate All Orders" to create balanced experimental orders.

### 3. Select Order
Choose `ORD-0001` from the order list. This automatically:
- Applies the order to your experiment matrix
- Sets Group ID to "ORD-0001"
- Marks the order as used

### 4. Configure Network
Set UDP broadcast settings:
- IP: `192.168.1.255` (your network's broadcast address)
- Port: `1221` (default, shared with avatar sync)

### 5. Run Experiment
1. Click "Validate & Initialize Protocol"
2. Click "Initiate Condition" to start first condition
3. 5-minute timer begins automatically
4. Click "Progress to Next" when ready (or wait for timer)
5. Repeat until all conditions complete

### 6. Save Data
Enter notes and click "Archive Session Data" to export:
```
VR Experiment Session Data
==================================================

Group ID: ORD-0001
Date/Time: 2024-01-15 14:30:22
Current Condition Index: 3

Experiment Sequence:
--------------------
Condition 1: Condition A (Object 1) [COMPLETED]
Condition 2: Condition B (Object 2) [COMPLETED]  
Condition 3: Condition C (Object 3) [COMPLETED]

Supervisor Notes:
--------------------
Participant completed all conditions successfully.
Good engagement throughout the experiment.

System Event Log:
--------------------
[14:30:22] Application started. Ready to configure experiment.
[14:31:15] Sent UDP message: {"command":"start_condition","condition_type":"condition_a","object_type":"object_1","condition_index":0}
[14:36:15] 5-minute timer expired - sending disable_all command
...
```

## Network Configuration

### Default Settings
- **IP**: `10.195.83.255` (broadcast address)
- **Port**: `1221` (shared with avatar sync system)

### Custom Settings Example
For a local network `192.168.1.0/24`:
- **IP**: `192.168.1.255`
- **Port**: `1221`

## Troubleshooting

### Common Issues
1. **Browser doesn't open**: Run `python run.py` manually, then go to `http://localhost:5000`
2. **UDP not received**: Check IP/port settings match your VR application
3. **Order generation fails**: Ensure both variables have equal number of values
4. **Can't save session**: Enter a Group ID before saving

### Log Files
Check `logs/vr_experiment_manager.log` for detailed error information and system activity.

## Requirements

- Python 3.7+
- Flask, Flask-SocketIO, eventlet (see requirements.txt)
- Modern web browser
- Network connectivity to VR devices

## Unity Integration

### Unity VR Receiver Script
Use the included `VRExperimentReceiver.cs` script to receive UDP messages in Unity:

1. **Install**: Copy script to Unity project
2. **Configure**: Set up conditions and objects in Inspector
3. **Connect**: Ensure same network and port (1221)

See `Unity_Setup_Guide.md` for detailed setup instructions.

### Example Unity Setup
```csharp
// In Unity Inspector:
Conditions:
- condition_a: Enable [EnvironmentA, UISetA]
- condition_b: Enable [EnvironmentB, UISetB]  
- condition_c: Enable [EnvironmentC, UISetC]

Objects:
- object_1: Activate Object1Prefab
- object_2: Activate Object2Prefab
- object_3: Activate Object3Prefab
```

The script automatically handles UDP messages and manages GameObjects based on your experiment configuration.