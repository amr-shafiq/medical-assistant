using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.UI;
using System;

public class ChatUIManager : MonoBehaviour
{
    [Header("UI Elements")]
    public Transform contentPanel; 
    public GameObject messagePrefab; 
    public ScrollRect scrollRect; 

    void Start()
    {
        if (contentPanel == null)
        {
            Debug.LogError("Content Panel is not assigned in the Inspector!");
        }
        else
        {
            Debug.Log("Content Panel is assigned: " + contentPanel.name);
        }

        if (messagePrefab == null)
        {
            Debug.LogError("Message Prefab is not assigned in the Inspector!");
        }
        else
        {
            Debug.Log("Message Prefab is assigned: " + messagePrefab.name);
        }

        if (scrollRect == null)
        {
            Debug.LogError("ScrollRect is not assigned in the Inspector!");
        }
        else
        {
            Debug.Log("ScrollRect is assigned: " + scrollRect.name);
        }
    }

    public void AddMessage(string message, bool isUser)
    {
        Debug.Log("Instantiating message prefab...");
        GameObject newMessage = Instantiate(messagePrefab, contentPanel);

        Debug.Log("Prefab instantiated successfully: " + newMessage.name);

        // Check for TMP Component
        var messageText = newMessage.GetComponentInChildren<TextMeshProUGUI>();
        if (messageText == null)
        {
            Debug.LogError("No TextMeshProUGUI component found in the messagePrefab!");
            return;
        }
        else
        {
            Debug.Log("Found TextMeshProUGUI component: " + messageText.name);
        }

        // Assign Text
        messageText.text = message;
        Debug.Log("Message text assigned: " + messageText.text);

        // Set message color
        messageText.color = isUser ? Color.blue : Color.green;
        Debug.Log("Message color assigned.");

        // Adjust the layout to fit the content
        LayoutRebuilder.ForceRebuildLayoutImmediate(newMessage.GetComponent<RectTransform>());

        // Scroll to bottom
        StartCoroutine(ScrollToBottom());
    }


    public IEnumerator ScrollToBottom()
    {
        // Wait until the next frame to update the UI layout
        yield return null;

        if (scrollRect != null)
        {
            // Scroll to bottom
            scrollRect.verticalNormalizedPosition = 0f;
            Debug.Log("Scrolled to bottom.");
        }
        else
        {
            Debug.LogError("ScrollRect reference is null! Cannot scroll to bottom.");
        }
    }
}



