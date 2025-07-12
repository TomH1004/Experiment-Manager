using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;
using Newtonsoft.Json;

[System.Serializable]
public class ExperimentCommand
{
    public string command;
    public string condition_type;
    public string object_type;
    public int condition_index;
    public string reason;
}

[System.Serializable]
public class ConditionSetup
{
    [Header("Condition Settings")]
    public string conditionName = "condition_a";
    
    [Header("GameObjects to Enable")]
    public GameObject[] objectsToEnable;
    
    [Header("GameObjects to Disable")]
    public GameObject[] objectsToDisable;
}

[System.Serializable]
public class ObjectSetup
{
    [Header("Object Settings")]
    public string objectName = "object_1";
    
    [Header("GameObject to Activate")]
    public GameObject objectToActivate;
}

public class VRExperimentReceiver : MonoBehaviour
{
    [Header("Network Settings")]
    [Tooltip("UDP port to listen on (must match experiment manager)")]
    public int udpPort = 1221;
    
    [Header("Experiment Configuration")]
    [Tooltip("Setup different conditions (e.g., condition_a, condition_b, condition_c)")]
    public ConditionSetup[] conditions;
    
    [Tooltip("Setup different objects (e.g., object_1, object_2, object_3)")]
    public ObjectSetup[] objects;
    
    [Header("Global Controls")]
    [Tooltip("GameObjects to disable when experiment ends or timer expires")]
    public GameObject[] globalDisableObjects;
    
    [Tooltip("GameObjects to enable when experiment starts")]
    public GameObject[] globalEnableObjects;
    
    [Header("Debug Settings")]
    public bool showDebugMessages = true;
    public bool logToFile = false;
    
    // Private variables
    private UdpClient udpClient;
    private Thread udpThread;
    private bool isListening = false;
    private ExperimentCommand lastCommand;
    
    // Current experiment state
    private string currentCondition = "";
    private string currentObject = "";
    private int currentConditionIndex = 0;
    
    void Start()
    {
        StartUDPListener();
        LogMessage("VR Experiment Receiver started. Listening on port " + udpPort);
    }
    
    void StartUDPListener()
    {
        try
        {
            udpClient = new UdpClient(udpPort);
            udpThread = new Thread(new ThreadStart(UDPListener));
            udpThread.IsBackground = true;
            udpThread.Start();
            isListening = true;
            LogMessage("UDP Listener started successfully");
        }
        catch (Exception e)
        {
            LogMessage("Error starting UDP listener: " + e.Message);
        }
    }
    
    void UDPListener()
    {
        IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);
        
        while (isListening)
        {
            try
            {
                byte[] data = udpClient.Receive(ref remoteEndPoint);
                string message = Encoding.UTF8.GetString(data);
                
                // Parse JSON message
                ExperimentCommand command = JsonConvert.DeserializeObject<ExperimentCommand>(message);
                
                if (command != null)
                {
                    lastCommand = command;
                    LogMessage("Received command: " + command.command + " - " + command.condition_type + " - " + command.object_type);
                }
            }
            catch (Exception e)
            {
                LogMessage("UDP Listener error: " + e.Message);
            }
        }
    }
    
    void Update()
    {
        // Process received commands on main thread
        if (lastCommand != null)
        {
            ProcessCommand(lastCommand);
            lastCommand = null;
        }
    }
    
    void ProcessCommand(ExperimentCommand command)
    {
        switch (command.command.ToLower())
        {
            case "start_condition":
                StartCondition(command.condition_type, command.object_type, command.condition_index);
                break;
                
            case "next_condition":
                NextCondition(command.condition_type, command.object_type, command.condition_index);
                break;
                
            case "disable_all":
                DisableAll(command.reason);
                break;
                
            default:
                LogMessage("Unknown command: " + command.command);
                break;
        }
    }
    
    void StartCondition(string conditionType, string objectType, int conditionIndex)
    {
        LogMessage($"Starting condition: {conditionType} with object: {objectType} (Index: {conditionIndex})");
        
        // Update current state
        currentCondition = conditionType;
        currentObject = objectType;
        currentConditionIndex = conditionIndex;
        
        // Enable global experiment objects
        EnableObjects(globalEnableObjects);
        
        // Apply condition settings
        ApplyCondition(conditionType);
        
        // Activate specific object
        ActivateObject(objectType);
        
        // Call custom start event (for students to extend)
        OnConditionStart(conditionType, objectType, conditionIndex);
    }
    
    void NextCondition(string conditionType, string objectType, int conditionIndex)
    {
        LogMessage($"Moving to next condition: {conditionType} with object: {objectType} (Index: {conditionIndex})");
        
        // Disable previous condition objects
        DisableCurrentObjects();
        
        // Start new condition
        StartCondition(conditionType, objectType, conditionIndex);
        
        // Call custom next event (for students to extend)
        OnNextCondition(conditionType, objectType, conditionIndex);
    }
    
    void DisableAll(string reason)
    {
        LogMessage($"Disabling all objects. Reason: {reason}");
        
        // Disable all condition objects
        DisableCurrentObjects();
        
        // Disable global objects
        DisableObjects(globalDisableObjects);
        
        // Call custom disable event (for students to extend)
        OnExperimentEnd(reason);
    }
    
    void ApplyCondition(string conditionType)
    {
        // Find matching condition setup
        foreach (ConditionSetup condition in conditions)
        {
            if (condition.conditionName.ToLower() == conditionType.ToLower())
            {
                // Enable condition objects
                EnableObjects(condition.objectsToEnable);
                
                // Disable condition objects
                DisableObjects(condition.objectsToDisable);
                
                LogMessage($"Applied condition: {conditionType}");
                return;
            }
        }
        
        LogMessage($"Warning: No condition setup found for: {conditionType}");
    }
    
    void ActivateObject(string objectType)
    {
        // Find matching object setup
        foreach (ObjectSetup obj in objects)
        {
            if (obj.objectName.ToLower() == objectType.ToLower())
            {
                // Activate object
                if (obj.objectToActivate != null)
                {
                    obj.objectToActivate.SetActive(true);
                    LogMessage($"Activated object: {objectType}");
                }
                return;
            }
        }
        
        LogMessage($"Warning: No object setup found for: {objectType}");
    }
    
    void DisableCurrentObjects()
    {
        // Disable all currently active objects
        foreach (ObjectSetup obj in objects)
        {
            if (obj.objectToActivate != null)
            {
                obj.objectToActivate.SetActive(false);
            }
        }
        
        // Disable current condition objects
        foreach (ConditionSetup condition in conditions)
        {
            if (condition.conditionName.ToLower() == currentCondition.ToLower())
            {
                DisableObjects(condition.objectsToEnable);
                EnableObjects(condition.objectsToDisable);
                break;
            }
        }
    }
    
    void EnableObjects(GameObject[] objects)
    {
        if (objects != null)
        {
            foreach (GameObject obj in objects)
            {
                if (obj != null)
                {
                    obj.SetActive(true);
                }
            }
        }
    }
    
    void DisableObjects(GameObject[] objects)
    {
        if (objects != null)
        {
            foreach (GameObject obj in objects)
            {
                if (obj != null)
                {
                    obj.SetActive(false);
                }
            }
        }
    }
    
    void LogMessage(string message)
    {
        if (showDebugMessages)
        {
            Debug.Log("[VR Experiment] " + message);
        }
        
        if (logToFile)
        {
            // Students can implement file logging here if needed
            System.IO.File.AppendAllText("experiment_log.txt", 
                DateTime.Now.ToString("HH:mm:ss") + " - " + message + "\n");
        }
    }
    
    // ============================================
    // CUSTOM EVENTS - Students can modify these
    // ============================================
    
    /// <summary>
    /// Called when a new condition starts. Students can add custom logic here.
    /// </summary>
    public virtual void OnConditionStart(string conditionType, string objectType, int conditionIndex)
    {
        // Example: Change environment based on condition
        // if (conditionType == "condition_a") { /* modify environment */ }
        // if (conditionType == "condition_b") { /* modify environment differently */ }
        
        // Example: Show UI message
        // ShowMessage($"Condition {conditionIndex + 1}: {conditionType} with {objectType}");
    }
    
    /// <summary>
    /// Called when moving to next condition. Students can add custom logic here.
    /// </summary>
    public virtual void OnNextCondition(string conditionType, string objectType, int conditionIndex)
    {
        // Example: Save data from previous condition
        // SaveConditionData(currentCondition, currentObject);
        
        // Example: Reset player position
        // ResetPlayerPosition();
    }
    
    /// <summary>
    /// Called when experiment ends. Students can add custom logic here.
    /// </summary>
    public virtual void OnExperimentEnd(string reason)
    {
        // Example: Show completion message
        // if (reason == "timer_expired") ShowMessage("Time's up!");
        // else ShowMessage("Experiment completed!");
        
        // Example: Save final data
        // SaveExperimentData();
    }
    
    // ============================================
    // UTILITY METHODS - Students can use these
    // ============================================
    
    /// <summary>
    /// Get current condition name
    /// </summary>
    public string GetCurrentCondition()
    {
        return currentCondition;
    }
    
    /// <summary>
    /// Get current object name
    /// </summary>
    public string GetCurrentObject()
    {
        return currentObject;
    }
    
    /// <summary>
    /// Get current condition index
    /// </summary>
    public int GetCurrentConditionIndex()
    {
        return currentConditionIndex;
    }
    
    /// <summary>
    /// Manually trigger condition (for testing)
    /// </summary>
    [ContextMenu("Test Start Condition")]
    public void TestStartCondition()
    {
        if (conditions.Length > 0 && objects.Length > 0)
        {
            StartCondition(conditions[0].conditionName, objects[0].objectName, 0);
        }
    }
    
    /// <summary>
    /// Manually trigger disable all (for testing)
    /// </summary>
    [ContextMenu("Test Disable All")]
    public void TestDisableAll()
    {
        DisableAll("manual_test");
    }
    
    void OnDestroy()
    {
        // Clean up UDP listener
        isListening = false;
        if (udpThread != null)
        {
            udpThread.Abort();
        }
        if (udpClient != null)
        {
            udpClient.Close();
        }
    }
    
    void OnApplicationPause(bool pauseStatus)
    {
        // Handle app pause (important for mobile VR)
        if (pauseStatus)
        {
            LogMessage("Application paused");
        }
        else
        {
            LogMessage("Application resumed");
        }
    }
} 