# VR Experiment Manager

A web-based control system for managing VR experiments with customizable variables and balanced experimental design.

## Quick Start

### 1. Install Dependencies
```bash
pip install flask flask-socketio
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

// Moving to next condition
{
  "command": "next_condition", 
  "condition_type": "condition_b",
  "object_type": "object_2",
  "condition_index": 1
}

// Timer expired
{
  "command": "disable_all",
  "reason": "timer_expired"
}
```

**Note**: Condition and object names are automatically converted to lowercase in UDP messages.

## Order Creation

The system uses Latin Square design to create balanced experimental orders.

### Example Configuration
**Variables:**
- Condition Types: `["Condition A", "Condition B", "Condition C"]`
- Object Types: `["Object 1", "Object 2", "Object 3"]`

### Generated Orders
```
Order ORD-0001:
1. Condition A → Object 1
2. Condition B → Object 2  
3. Condition C → Object 3

Order ORD-0002:
1. Condition B → Object 3
2. Condition C → Object 1
3. Condition A → Object 2

Order ORD-0003:
1. Condition C → Object 2
2. Condition A → Object 3
3. Condition B → Object 1
```

### Order Benefits
- Each condition appears in each position exactly once
- Each condition pairs with each object exactly once
- Counterbalanced design controls for order effects
- Reduces from factorial complexity (3! × 3! = 36) to manageable count (18 orders)

## File Structure

```
VR-Experiment-Manager/
├── run.py                    # Main launcher (auto-opens browser)
├── app.py                    # Flask backend
├── static/script.js          # Frontend JavaScript
├── templates/index.html      # Web interface
├── config/                   # Auto-created configuration files
│   ├── metadata.json         # Variable names
│   ├── condition_types.json  # Variable 1 values
│   ├── object_types.json     # Variable 2 values
│   └── orders.json           # Generated orders
├── data/                     # Auto-created session exports
└── logs/                     # Auto-created log files
```

## Usage Example

### 1. Setup Variables
```
Variable 1: "Condition Type" (singular), "Condition Types" (plural)
Values: ["Condition A", "Condition B", "Condition C"]

Variable 2: "Object Type" (singular), "Object Types" (plural)  
Values: ["Object 1", "Object 2", "Object 3"]
```

### 2. Generate Orders
Click "Generate All Orders" to create 18 balanced experimental orders.

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
1. **Browser doesn't open**: Run `python app.py` manually, then go to `http://localhost:5000`
2. **UDP not received**: Check IP/port settings match your VR application
3. **Order generation fails**: Ensure both variables have equal number of values
4. **Can't save session**: Enter a Group ID before saving

### Log Files
Check `logs/vr_experiment_manager.log` for detailed error information and system activity.

## Requirements

- Python 3.7+
- Flask, Flask-SocketIO
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