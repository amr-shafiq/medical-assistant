using UnityEngine;
using UnityEditor;
using System.IO;

public class SessionClearer : MonoBehaviour
{
    // private static string sessionFilePath = "H:/Unity Workspace/ASR Final Project/Assets/AsianFemale/scripts/session_data.json";

    // [InitializeOnLoadMethod]
    // private static void OnPlayModeStateChanged()
    // {
        // Listen for when Unity's play mode state changes (play/stop)
        // EditorApplication.playModeStateChanged += OnPlayModeStateChangedHandler;
    // }

    // private static void OnPlayModeStateChangedHandler(PlayModeStateChange state)
    // {
        // When play mode is stopped, clear the session data
        // if (state == PlayModeStateChange.ExitingPlayMode)
        // {
            // ClearSessionData();
        // }
    // }

    // private static void ClearSessionData()
    // {
        // try
        // {
            // Check if the session file exists
            // if (File.Exists(sessionFilePath))
            // {
                // Clear the contents of the session data file
                // File.WriteAllText(sessionFilePath, "{}"); // Write an empty JSON object
                // Debug.Log("Session data cleared.");
            // }
            // else
            // {
                // Debug.LogWarning("Session data file not found.");
            // }
        // }
        // catch (System.Exception ex)
        // {
            // Debug.LogError($"Failed to clear session data: {ex.Message}");
        // }
    // }
}

