# Unity VR Experiment Receiver Setup Guide

## Quick Setup

### 1. Install Newtonsoft JSON Package
1. Open Unity Package Manager (`Window > Package Manager`)
2. Click the `+` button and select "Add package by name"
3. Enter: `com.unity.nuget.newtonsoft-json`
4. Click "Add"

### 2. Add the Script
1. Copy `VRExperimentReceiver.cs` to your Unity project's `Assets/Scripts/` folder
2. Create an empty GameObject in your scene
3. Rename it to "ExperimentManager"
4. Add the `VRExperimentReceiver` script to it

### 3. Configure in Inspector

#### Network Settings
- **UDP Port**: `1221` (must match experiment manager)

#### Experiment Configuration
Set up your conditions and objects to match your experiment manager:

**Example Conditions:**
- Condition 1: `condition_a`
- Condition 2: `condition_b` 
- Condition 3: `condition_c`

**Example Objects:**
- Object 1: `object_1`
- Object 2: `object_2`
- Object 3: `object_3`

#### Global Controls
- **Global Enable Objects**: Objects to enable when experiment starts (e.g., UI, player controller)
- **Global Disable Objects**: Objects to disable when experiment ends (e.g., all interactive objects)

## Inspector Configuration Example

```
VR Experiment Receiver
├── Network Settings
│   └── UDP Port: 1221
├── Experiment Configuration
│   ├── Conditions [3]
│   │   ├── [0] Condition Name: "condition_a"
│   │   │   ├── Objects To Enable: [LightingA, UIElementsA]
│   │   │   └── Objects To Disable: [LightingB, LightingC]
│   │   ├── [1] Condition Name: "condition_b"
│   │   │   ├── Objects To Enable: [LightingB, UIElementsB]
│   │   │   └── Objects To Disable: [LightingA, LightingC]
│   │   └── [2] Condition Name: "condition_c"
│   │       ├── Objects To Enable: [LightingC, UIElementsC]
│   │       └── Objects To Disable: [LightingA, LightingB]
│   └── Objects [3]
│       ├── [0] Object Name: "object_1"
│       │   └── Object To Activate: Object1Prefab
│       ├── [1] Object Name: "object_2"
│       │   └── Object To Activate: Object2Prefab
│       └── [2] Object Name: "object_3"
│           └── Object To Activate: Object3Prefab
└── Global Controls
    ├── Global Disable Objects: [AllInteractables, ExperimentUI]
    └── Global Enable Objects: [PlayerController, MainCamera]
```

## Testing

### Test Without Experiment Manager
1. Right-click on the VRExperimentReceiver script in Inspector
2. Select "Test Start Condition" to test condition activation
3. Select "Test Disable All" to test cleanup

### Test With Experiment Manager
1. Start your Unity scene
2. Run the VR Experiment Manager (`python run.py`)
3. Configure and start an experiment
4. Watch Unity console for received messages

## Common Patterns

### Pattern 1: Simple Object Spawning
```
Condition: "condition_a"
├── Objects To Enable: [EnvironmentA, UISetA]
├── Objects To Disable: [EnvironmentB, EnvironmentC]

Object: "object_1"
├── Object To Activate: Object1Prefab (positioned at spawn point)
```

### Pattern 2: Environment Changes
```
Condition: "condition_b"
├── Objects To Enable: [LightingSetB, EffectsB, BackgroundB]
├── Objects To Disable: [LightingSetA, EffectsA, BackgroundA]

Object: "object_2"
├── Object To Activate: Object2Prefab (with physics enabled)
```

### Pattern 3: UI and Interface Changes
```
Condition: "condition_c"
├── Objects To Enable: [InterfaceC, InstructionsC]
├── Objects To Disable: [InterfaceA, InterfaceB]

Object: "object_3"
├── Object To Activate: Object3Prefab
```

## Extending the Script

### Add Custom Logic
Override the virtual methods in a derived class:

```csharp
public class MyExperimentReceiver : VRExperimentReceiver
{
    public override void OnConditionStart(string conditionType, string objectType, int conditionIndex)
    {
        // Your custom logic here
        if (conditionType == "condition_a")
        {
            // Modify environment for condition A
            RenderSettings.skybox = skyboxA;
            playerController.moveSpeed = 1.0f;
        }
        else if (conditionType == "condition_b")
        {
            // Modify environment for condition B
            RenderSettings.skybox = skyboxB;
            playerController.moveSpeed = 1.5f;
        }
        
        // Call base implementation
        base.OnConditionStart(conditionType, objectType, conditionIndex);
    }
    
    public override void OnExperimentEnd(string reason)
    {
        // Save data, show completion screen, etc.
        SaveExperimentData();
        ShowCompletionScreen();
        
        base.OnExperimentEnd(reason);
    }
}
```

### Access Current State
```csharp
public class MyGameLogic : MonoBehaviour
{
    public VRExperimentReceiver experimentReceiver;
    
    void Update()
    {
        string currentCondition = experimentReceiver.GetCurrentCondition();
        string currentObject = experimentReceiver.GetCurrentObject();
        int conditionIndex = experimentReceiver.GetCurrentConditionIndex();
        
        // Use this information in your game logic
        if (currentCondition == "condition_a")
        {
            // Handle condition A specific logic
        }
    }
}
```

## Troubleshooting

### UDP Messages Not Received
1. Check firewall settings (allow port 1221)
2. Verify UDP port matches experiment manager
3. Ensure both applications are on same network
4. Check Unity console for error messages

### Objects Not Activating
1. Verify object names match exactly (case-insensitive)
2. Check that GameObjects are assigned in Inspector
3. Ensure objects exist in scene hierarchy
4. Check for null reference errors in console

## Simple Example Setup

For a basic experiment with 3 conditions and 3 objects:

1. **Create 3 condition GameObjects** in your scene:
   - `ConditionA_Environment` (lighting, background for condition A)
   - `ConditionB_Environment` (lighting, background for condition B)
   - `ConditionC_Environment` (lighting, background for condition C)

2. **Create 3 object prefabs**:
   - `Object1Prefab` (first experimental object)
   - `Object2Prefab` (second experimental object)
   - `Object3Prefab` (third experimental object)

3. **Configure in Inspector**:
   - Set condition names: `condition_a`, `condition_b`, `condition_c`
   - Set object names: `object_1`, `object_2`, `object_3`
   - Assign enable/disable objects for each condition
   - Assign object prefabs to activate

4. **Test**: Use the context menu options to test your setup before running the full experiment. 