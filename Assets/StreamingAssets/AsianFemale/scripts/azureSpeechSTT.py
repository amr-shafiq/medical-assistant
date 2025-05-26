import os
import sys
from azure.identity import DefaultAzureCredential
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig, ResultReason

speech_subscription_key = "CutiVqvVHzl2W6MCqWB2f2pMshaE89MP6oLITKrCr4d2RQLjEoaoJQQJ99ALACqBBLyXJ3w3AAAYACOGgk8y"
resource_region = "southeastasia"  
# Authenticate with Managed Identity
credential = DefaultAzureCredential()
# Create the Speech Config with endpoint
speech_config = SpeechConfig(subscription="CutiVqvVHzl2W6MCqWB2f2pMshaE89MP6oLITKrCr4d2RQLjEoaoJQQJ99ALACqBBLyXJ3w3AAAYACOGgk8y", region="southeastasia")

# Get the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
base_path = os.path.dirname(script_dir)

# Specify the input audio file
audio_file_path = os.path.join(base_path, "recorded1.wav")
transcription_file_path = os.path.join(base_path, "transcription.txt")

# Debugging statements
print(f"DEBUG: Current Working Directory - {os.getcwd()}")
print(f"DEBUG: Script Directory - {script_dir}")
print(f"DEBUG: Base Path - {base_path}")
print(f"DEBUG: Audio File Path - {audio_file_path} (Exists? {os.path.exists(audio_file_path)})")

# Check if audio file exists before proceeding
if not os.path.exists(audio_file_path):
    print("Error: Audio file not found!")
    exit(1)

# Configure audio input
audio_input = AudioConfig(filename=audio_file_path)

# Create the Speech Recognizer
speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

print("Recognizing speech from the audio file...")
result = speech_recognizer.recognize_once()

# Check recognition result
if result.reason == ResultReason.RecognizedSpeech:
    print("Transcription recognized successfully!")
    transcription_text = result.text
    print(f"Transcription: {transcription_text}")

    # Save the transcription to a file
    with open(transcription_file_path, "w", encoding="utf-8") as transcription_file:
        transcription_file.write(transcription_text)

    print(f"Transcription saved to: {transcription_file_path}")

elif result.reason == ResultReason.NoMatch:
    print("No speech could be recognized.")

elif result.reason == ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print(f"Speech recognition canceled: {cancellation_details.reason}")
    if cancellation_details.error_details:
        print(f"Error details: {cancellation_details.error_details}")



