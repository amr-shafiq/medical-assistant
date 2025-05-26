import os
from azure.identity import DefaultAzureCredential
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, AudioConfig

speech_subscription_key = "CutiVqvVHzl2W6MCqWB2f2pMshaE89MP6oLITKrCr4d2RQLjEoaoJQQJ99ALACqBBLyXJ3w3AAAYACOGgk8y"
resource_region = "southeastasia"  
# Authenticate with Managed Identity
credential = DefaultAzureCredential()
# Create the Speech Config with endpoint
speech_config = SpeechConfig(subscription="CutiVqvVHzl2W6MCqWB2f2pMshaE89MP6oLITKrCr4d2RQLjEoaoJQQJ99ALACqBBLyXJ3w3AAAYACOGgk8y", region="southeastasia")
# Specify the input audio file (replace with your file path)
audio_file_path = "H:/recorded1.wav"
audio_input = AudioConfig(filename=audio_file_path)
# Create the Speech Recognizer
speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

print("Recognizing speech from the audio file...")
result = speech_recognizer.recognize_once()
# Check recognition result
if result.reason == result.reason.RecognizedSpeech:
    print("Transcription recognized successfully!")
    transcription_text = result.text
    print(f"Transcription: {transcription_text}")
    # Save the transcription to a file
    transcription_file_path = "H:/transcription.txt"
    with open(transcription_file_path, "w", encoding="utf-8") as transcription_file:
        transcription_file.write(transcription_text)
    print(f"Transcription saved to: {transcription_file_path}")
elif result.reason == result.reason.NoMatch:
    print("No speech could be recognized.")
elif result.reason == result.reason.Canceled:
    cancellation_details = result.cancellation_details
    print(f"Speech recognition canceled: {cancellation_details.reason}")
    if cancellation_details.error_details:
        print(f"Error details: {cancellation_details.error_details}")



