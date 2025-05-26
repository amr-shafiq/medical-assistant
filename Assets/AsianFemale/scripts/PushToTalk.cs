using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using Unity.VisualScripting;
using System.Threading.Tasks;
using UnityEngine;
using UnityEngine.UI;
using System;
using UnityEngine.Networking;

public class PushToTalk : MonoBehaviour
{

    public GameObject character;
    public Text userTextUI;
    public Text characterTextUI;
    public Animator characterAnimator;
    private CharacterAnimationController animationController;
    // private string transcriptionFilePath = "H:/transcription.txt";
    // private string pythonSTTPath = @"C:/azureSpeechSTT.py";
    // private string pythonTTSPath = @"C:/azureSpeechTTS.py";
    // private string recordedFilePath = "H:/recorded1.wav";
    // private string ttsAudioFilePath = "H:/tts_output.wav";
    private AudioClip recording;
    private bool isListening = false;
    private bool isNameCaptured = false;
    private int recordingFrequency = 44100;
    private FileStream fileStream;
    private int lastSamplePosition = 0;
    private AudioSource audioSource;
    private string lastTranscription = "";
    public Text responseText;
    public ChatUIManager chatUIManager;
    private string output;
    private DateTime lastTranscriptionModifiedTime = DateTime.MinValue;
    private bool isUpdatingChatUI = false;
    private bool isProcessingSTT = false;
    private bool isProcessingTTS = false;
    private string lastProcessedTranscription = null;
    private string basePath;
    private string persistentPath;

    private string transcriptionFilePath;
    private string pythonSTTPath;
    private string pythonTTSPath;
    private string recordedFilePath;
    private string ttsAudioFilePath;



    void Start()
    {
        #if UNITY_EDITOR
            basePath = Application.dataPath + "/AsianFemale";
        #else
            basePath = Application.persistentDataPath + "/AsianFemale";  // Use persistent path in build
        #endif

        persistentPath = Application.persistentDataPath + "/AsianFemale";

        UnityEngine.Debug.Log($"Persistent path: {Application.persistentDataPath}");
        // Copy necessary files to persistentDataPath
        CopyFilesToPersistentPath();

        // Now that basePath is initialized, assign the rest
        transcriptionFilePath = Path.Combine(persistentPath, "transcription.txt");
        pythonSTTPath = Path.Combine(Application.persistentDataPath, "AsianFemale/scripts/azureSpeechSTT.py");
        pythonTTSPath = Path.Combine(persistentPath, "scripts/azureSpeechTTS.py");
        recordedFilePath = Path.Combine(persistentPath, "recorded1.wav");
        ttsAudioFilePath = Path.Combine(persistentPath, "tts_output.wav");

        audioSource = gameObject.AddComponent<AudioSource>();
        if (characterAnimator == null)
        {
            characterAnimator = GetComponent<Animator>();
        }

        animationController = GetComponent<CharacterAnimationController>();

        if (!characterAnimator.enabled)
        {
            UnityEngine.Debug.LogWarning("Animator is disabled. Enabling it.");
            characterAnimator.enabled = true;
        }
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.E))
        {
            if (!isListening)
            {
                UnityEngine.Debug.Log("E key pressed - recording should start");
                StartMicrophoneRecording();

            }
        }
        else if (Input.GetKeyUp(KeyCode.E))
        {
            if (isListening)
            {
                UnityEngine.Debug.Log("E key released - recording should stop");
                StopMicrophoneRecording();
                StartSpeechRecognition();
            }
        }

        if (isListening)
        {
            AppendAudioData();
        }

        string newTranscription = ReadLatestTranscription();
        if (!string.IsNullOrEmpty(newTranscription) && newTranscription != lastTranscription)
        {
            lastTranscription = newTranscription;
            UnityEngine.Debug.Log($"Transcription updated: {newTranscription}");

            if (!isNameCaptured)
            {
                // Assume the first transcription is the name
                isNameCaptured = true;
                UpdateUserUI($"Name captured: {newTranscription}");
                UpdateCharacterUI("Thank you! How can I assist you today?");
                UnityEngine.Debug.Log($"Name captured: {newTranscription}");
            }
            else
            {
                // Process further inputs
                UpdateUserUI(newTranscription);
                StartTTS(newTranscription);
            }
        }
    }

    void CopyFilesToPersistentPath()
    {
        string sourcePath = Application.streamingAssetsPath + "/AsianFemale";
        string destinationPath = Application.persistentDataPath + "/AsianFemale";

        if (!Directory.Exists(destinationPath))
        {
            Directory.CreateDirectory(destinationPath);
        }

        foreach (string filePath in Directory.GetFiles(sourcePath, "*", SearchOption.AllDirectories))
        {
            string relativePath = filePath.Substring(sourcePath.Length + 1);
            string destFilePath = Path.Combine(destinationPath, relativePath);

            string destDirectory = Path.GetDirectoryName(destFilePath);
            if (!Directory.Exists(destDirectory))
            {
                Directory.CreateDirectory(destDirectory);
            }

            File.Copy(filePath, destFilePath, true);
            UnityEngine.Debug.Log($"Copied: {filePath} → {destFilePath}");
        }
    }






    void StartMicrophoneRecording()
    {
        if (Microphone.devices.Length == 0)
        {
            UnityEngine.Debug.LogError("No microphone devices found!");
            return;
        }

        UnityEngine.Debug.Log($"Using Microphone: {Microphone.devices[0]}");

        recording = Microphone.Start(null, true, 10, recordingFrequency);
        isListening = true;
        lastSamplePosition = 0;

        fileStream = new FileStream(recordedFilePath, FileMode.Create);
        WriteWavHeader(fileStream, 0, recording.channels, recordingFrequency);
        UnityEngine.Debug.Log("Microphone recording started...");
    }

    void StopMicrophoneRecording()
    {
        if (Microphone.IsRecording(null))
        {
            int currentPosition = Microphone.GetPosition(null);
            AppendAudioData(currentPosition);
            Microphone.End(null);
        }

        if (fileStream != null)
        {
            UpdateWavHeader(fileStream);
            fileStream.Close();  
            fileStream.Dispose(); 
        }

        isListening = false;
        UnityEngine.Debug.Log("Microphone recording stopped...");
    }


    void AppendAudioData(int? currentSamplePosition = null)
    {
        if (recording == null || fileStream == null)
            return;

        if (!currentSamplePosition.HasValue)
            currentSamplePosition = Microphone.GetPosition(null);

        int samplesToRead = currentSamplePosition.Value - lastSamplePosition;
        if (samplesToRead <= 0)
            return;

        float[] audioData = new float[samplesToRead];
        recording.GetData(audioData, lastSamplePosition);

        byte[] wavData = ConvertToWav(audioData, samplesToRead, recording.channels);
        fileStream.Write(wavData, 0, wavData.Length);

        lastSamplePosition = currentSamplePosition.Value;
    }

    void WriteWavHeader(FileStream stream, int sampleCount, int channels, int frequency)
    {
        byte[] header = new byte[44];
        using (var memoryStream = new MemoryStream(header))
        using (var writer = new BinaryWriter(memoryStream))
        {
            writer.Write("RIFF".ToCharArray());
            writer.Write(36 + sampleCount * 2);
            writer.Write("WAVE".ToCharArray());
            writer.Write("fmt ".ToCharArray());
            writer.Write(16);
            writer.Write((short)1);
            writer.Write((short)channels);
            writer.Write(frequency);
            writer.Write(frequency * channels * 2);
            writer.Write((short)(channels * 2));
            writer.Write((short)16);
            writer.Write("data".ToCharArray());
            writer.Write(sampleCount * 2);
        }

        stream.Write(header, 0, header.Length);
    }

    void UpdateWavHeader(FileStream stream)
    {
        long fileSize = stream.Length;
        int sampleCount = (int)((fileSize - 44) / 2);

        stream.Seek(4, SeekOrigin.Begin);
        stream.Write(System.BitConverter.GetBytes((int)(fileSize - 8)), 0, 4);
        stream.Seek(40, SeekOrigin.Begin);
        stream.Write(System.BitConverter.GetBytes(sampleCount * 2), 0, 4);
    }

    byte[] ConvertToWav(float[] audioData, int sampleCount, int channels)
    {
        MemoryStream stream = new MemoryStream();
        BinaryWriter writer = new BinaryWriter(stream);

        foreach (float sample in audioData)
        {
            short intSample = (short)(Mathf.Clamp(sample, -1f, 1f) * short.MaxValue);
            writer.Write(intSample);
        }

        return stream.ToArray();
    }

    void StartSpeechRecognition()
    {
        if (isProcessingSTT)
        {
            UnityEngine.Debug.Log("Speech recognition already in progress. Skipping...");
            return;
        }

        isProcessingSTT = true;

        // Debug paths
        UnityEngine.Debug.Log($"[DEBUG] Python STT Script Path: {pythonSTTPath}");
        UnityEngine.Debug.Log($"[DEBUG] Recorded File Path: {recordedFilePath}");

        // Ensure the file exists before running
        if (!File.Exists(pythonSTTPath))
        {
            UnityEngine.Debug.LogError($"[ERROR] Python script not found: {pythonSTTPath}");
            isProcessingSTT = false;
            return;
        }
        if (!File.Exists(recordedFilePath))
        {
            UnityEngine.Debug.LogError($"[ERROR] Recorded audio file not found: {recordedFilePath}");
            isProcessingSTT = false;
            return;
        }

        // Full path to python.exe (modify if needed)
        string pythonExecutable = @"C:\Python312\python.exe";  // Ensure this is correct

        Process speechRecognitionProcess = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = pythonExecutable,  // Use the full path
                Arguments = $"\"{pythonSTTPath}\" \"{recordedFilePath}\"",
                WorkingDirectory = Path.GetDirectoryName(pythonSTTPath),  // Set working directory
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            }
        };

        speechRecognitionProcess.Start();

        Task.Run(() =>
        {
            string output = speechRecognitionProcess.StandardOutput.ReadToEnd();
            string error = speechRecognitionProcess.StandardError.ReadToEnd();

            speechRecognitionProcess.WaitForExit();
            speechRecognitionProcess.Dispose();
            isProcessingSTT = false; // Mark STT as completed

            if (!string.IsNullOrEmpty(error))
            {
                UnityEngine.Debug.LogError($"[ERROR] Speech recognition failed:\n{error}");
            }
            else
            {
                UnityEngine.Debug.Log($"[SUCCESS] Speech recognition output:\n{output}");
                string transcription = ReadLatestTranscription();
                if (!string.IsNullOrEmpty(transcription) && transcription != lastProcessedTranscription)
                {
                    lastProcessedTranscription = transcription;
                    UnityEngine.Debug.Log($"New transcription detected: {transcription}");
                    StartTTS(transcription);
                }
            }
        });
    }


    string ReadLatestTranscription()
    {
        if (File.Exists(transcriptionFilePath))
        {
            DateTime currentModifiedTime = File.GetLastWriteTime(transcriptionFilePath);
            if (currentModifiedTime > lastTranscriptionModifiedTime)
            {
                lastTranscriptionModifiedTime = currentModifiedTime;
                return File.ReadAllText(transcriptionFilePath).Trim();
            }
        }
        return null;
    }

    void UpdateUserUI(string transcription)
    {
        if (userTextUI != null)
        {
            userTextUI.text = "User: " + transcription;
        }
    }

    void UpdateCharacterUI(string response)
    {
        // if (characterTextUI != null)
        // {
            // characterTextUI.text = "Character: " + response;
        // }
    }

    // async void StartTTS(string text)
    void StartTTS(string text)
    {
        // Continuously check for new text in transcription.txt
        if (isProcessingTTS)
        {
            UnityEngine.Debug.Log("TTS already in progress. Skipping...");
            return;
        }
        isProcessingTTS = true;

        // Start TTS process
        if (characterAnimator == null)
        {
            characterAnimator = GameObject.Find("asianfemale").GetComponent<Animator>();
        }
        if (characterAnimator != null)
        {
            characterAnimator.SetBool("IsTalking", true);
        }

        if (chatUIManager != null)
        {
            chatUIManager.AddMessage($"Me: {text}", true);
        }

        Process ttsProcess = new Process
        {
            StartInfo = new ProcessStartInfo
            {
                FileName = "python",
                Arguments = $"\"{pythonTTSPath}\" \"{text}\" \"{ttsAudioFilePath}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true
            }
        };

        ttsProcess.Start();
        StartCoroutine(WaitForTTSProcess(ttsProcess));
    }

     void PlayTTSAudio()
     {
        if (!File.Exists(ttsAudioFilePath))
        {
        UnityEngine.Debug.LogError("TTS audio file does not exist.");
        return;
        }

        if (audioSource.isPlaying)
        {
            audioSource.Stop();
            UnityEngine.Debug.Log("Stopped previous audio playback.");
            }

     try
        {
            byte[] audioData = File.ReadAllBytes(ttsAudioFilePath);
            WAV wav = new WAV(audioData);
            if (wav.SampleCount > 0 && wav.Frequency > 0)
            {
                AudioClip audioClip = AudioClip.Create("TTS", wav.SampleCount, wav.ChannelCount, wav.Frequency, false);
                audioClip.SetData(wav.LeftChannel, 0);
                audioSource.clip = audioClip;

                audioSource.Play();
                StartCoroutine(RunCombinedTasks());
            }
            else
            {
                UnityEngine.Debug.LogError("Invalid WAV data in TTS audio file.");
            }
        }
        catch (Exception ex)
        {
            UnityEngine.Debug.LogError($"Error while processing TTS audio: {ex.Message}");
        }
     }

    IEnumerator RunCombinedTasks()
    {
        // Monitor audio playback and wait for it to finish
        float audioEndTime = Time.time + audioSource.clip.length;
        while (audioSource.isPlaying || Time.time < audioEndTime)
        {
            yield return null;
        }

        UnityEngine.Debug.Log("Audio playback completed.");

        
        if (characterAnimator != null)
        {
            characterAnimator.SetBool("IsTalking", false);
            characterAnimator.CrossFade("Idle", 0.5f);
            UnityEngine.Debug.Log("Animation transitioned to Idle after audio finished.");
        }
        else
        {
            UnityEngine.Debug.LogError("Character animator is null!");
        }

        UnityEngine.Debug.Log($"Updating UI with output: {output}, response: {responseText.text}");
        yield return StartCoroutine(UpdateUIWithTalkingState(output, responseText.text));
    }


    private IEnumerator UpdateUIWithTalkingState(string output, string response)
    {
        if (isUpdatingChatUI)
        {
            UnityEngine.Debug.LogWarning("UI update already in progress. Skipping this update.");
            yield break;
        }

        isUpdatingChatUI = true;

        if (string.IsNullOrEmpty(response))
        {
            response = "Sorry, I didn't understand that.";
        }

        if (characterTextUI != null)
        {
            characterTextUI.text = $"Assistant: {response}";
        }

        if (chatUIManager != null)
        {
            chatUIManager.AddMessage($"Assistant: {response}", false);
        }

        yield return null;
        isUpdatingChatUI = false;
    }



    private IEnumerator WaitForTTSProcess(Process ttsProcess)
    {
        
        string output = ttsProcess.StandardOutput.ReadToEnd();
        string error = ttsProcess.StandardError.ReadToEnd();

        ttsProcess.WaitForExit();
        ttsProcess.Dispose();
        isProcessingTTS = false; // Mark TTS as completed

        string responseToUse = string.Empty;

        if (!string.IsNullOrEmpty(error))
        {
            UnityEngine.Debug.LogError($"TTS error: {error}");
            responseToUse = error;
        }
        else
        {
            UnityEngine.Debug.Log($"TTS Output: {output}");
            if (!string.IsNullOrEmpty(output.Trim()))
            {
                responseToUse = output;
            }
            else
            {
                UnityEngine.Debug.LogError("TTS output is empty or null after trimming!");
                responseToUse = "I encountered an issue with generating speech.";  // Fallback message
            }
        }

        // Ensure this UI update happens on the main thread
        if (!string.IsNullOrEmpty(responseToUse))
        {
            StartCoroutine(UpdateUIWithTTS(responseToUse));
        }

        // Check if TTS audio file exists and play
        if (File.Exists(ttsAudioFilePath))
        {
            PlayTTSAudio();
        }
        else
        {
            UnityEngine.Debug.LogError("TTS failed. No audio playback available.");
            if (characterAnimator != null)
            {
                characterAnimator.SetBool("IsTalking", false);
                characterAnimator.CrossFade("Idle", 0.5f);
            }
        }

        // Update animation and UI after TTS process finishes
        if (!string.IsNullOrEmpty(responseToUse))
        {
            StartCoroutine(HandleAnimationAndUIUpdate(ttsProcess, output, responseToUse));
        }

        yield return null;
    }

    private IEnumerator UpdateUIWithTTS(string response)
    {
        if (characterTextUI != null)
        {
            // characterTextUI.text = $"Character: {response}";
            UnityEngine.Debug.Log("Character Text UI updated: " + response);
        }
        else
        {
            UnityEngine.Debug.LogError("CharacterTextUI is null. Cannot update text.");
        }

        if (chatUIManager != null)
        {
            // chatUIManager.AddMessage($"Character: {response}", false);
        }
        else
        {
            UnityEngine.Debug.LogError("chatUIManager is null. Cannot update chat UI.");
        }

        yield return null;
    }

    private IEnumerator UpdateUIWithCombinedText(string output, string response)
    {

        if (chatUIManager != null)
        {
            chatUIManager.AddMessage($"Assistant: {response}", false);
        }

        yield return null;
    }

    private IEnumerator HandleAnimationAndUIUpdate(Process ttsProcess, string output, string response)
    {
        yield return StartCoroutine(WaitForTTSProcess(ttsProcess));

        if (characterAnimator != null)
        {
            characterAnimator.SetBool("IsTalking", false);
            characterAnimator.CrossFade("Idle", 0.5f);
        }

        yield return StartCoroutine(UpdateUIWithCombinedText(output, response));
    }




}