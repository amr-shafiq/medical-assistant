using System.IO;
using UnityEngine;


public class StateManager : MonoBehaviour
{
    public static StateManager Instance;

    public string currentState = "waiting_for_name";  // Start state
    public string patientName = "";                  // Store patient's name
    public string symptoms = "";                     // Store symptoms as a comma-separated string
    public string disease = "";                      // Store detected disease

    private void Start()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else
        {
            Destroy(gameObject);
        }

        // Ensure state.txt is created/reset when the scene starts
        ResetStateFile();
    }

    // Method to reset the state file when Play is pressed
    private void ResetStateFile()
    {
        string stateFilePath = "H:/state.txt";

        // Default content for state.txt
        string content = $"currentState={currentState}\npatientName={patientName}\nsymptoms={symptoms}\ndisease={disease}";

        try
        {
            File.WriteAllText(stateFilePath, content);
            Debug.Log($"State file created/reset at {stateFilePath} with content:\n{content}");
        }
        catch (IOException ex)
        {
            Debug.LogError($"Failed to create/reset state file: {ex.Message}");
        }
    }

    // Method to set the state, patient name, symptoms, and disease
    public void SetState(string newState, string newPatientName = "", string newSymptoms = "", string newDisease = "")
    {
        currentState = newState;

        if (!string.IsNullOrEmpty(newPatientName))
        {
            patientName = newPatientName;
        }

        if (!string.IsNullOrEmpty(newSymptoms))
        {
            symptoms = newSymptoms;
        }

        if (!string.IsNullOrEmpty(newDisease))
        {
            disease = newDisease;
        }

        SaveStateToFile(); // Save updated state to file for Python to access
    }

    // Method to save the current state, patient name, symptoms, and disease to a file
    private void SaveStateToFile()
    {
        string stateFilePath = "H:/state.txt";

        // Write data in a key-value format
        string content = $"currentState={currentState}\npatientName={patientName}\nsymptoms={symptoms}\ndisease={disease}";

        try
        {
            File.WriteAllText(stateFilePath, content);
            Debug.Log($"State saved to {stateFilePath} with content:\n{content}");
        }
        catch (IOException ex)
        {
            Debug.LogError($"Failed to save state: {ex.Message}");
        }
    }

    // Method to retrieve the current state (for Python to read)
    public string GetState()
    {
        return currentState;
    }

    // Method to retrieve the current patient name
    public string GetPatientName()
    {
        return patientName;
    }

    // Method to retrieve the current symptoms
    public string GetSymptoms()
    {
        return symptoms;
    }

    // Method to retrieve the current disease
    public string GetDisease()
    {
        return disease;
    }
}






