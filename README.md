# Medical Virtual Assistant (Unity + ASR + TTS)

This is a Unity-based Medical Virtual Assistant developed as part of an academic/final project. It integrates:

-  Unity for the 3D environment and interaction
-  Python-based ASR (Automatic Speech Recognition)
-  Text-to-Speech for voice responses
-  Firebase for data handling and storage
-  Git LFS (for large assets)

---

##  Features

- Voice-activated interaction with a medical assistant avatar
- ASR via Python to recognize patient queries
- Keyword matching symptoms for diagnosing diseases
- TTS for voice response playback
- Unity animation and UI handling
- Firebase authentication and database support

---

## 🛠️ Tech Stack

| Tool           | Purpose                            |
|----------------|------------------------------------|
| Unity          | Main development engine            |
| Python         | ASR & TTS scripts                  |
| Firebase       | Backend (Authentication, Database) |
| Git LFS        | For large files (.unitypackage etc)|
| C#             | Game logic and avatar scripting    |

---

## 🧰 Setup Instructions

### 🔁 Prerequisites

- Unity (version XYZ)
- Python 3.x with:
  - `speechrecognition`, `pyaudio`, or other ASR dependencies
- Firebase Unity SDK
- Git LFS installed from this link: [text](https://git-lfs.github.com)


### 🔧 Firebase Setup

1. Create a Firebase project in [Firebase Console](https://console.firebase.google.com)
2. Enable Authentication and Firestore (or Realtime Database)
3. Download and place your Firebase config files:

 - `google-services.json` → `Assets/StreamingAssets/`
 - `GoogleService-Info.plist` (if building for iOS)

4. Import Firebase Unity SDK packages:
 - `FirebaseAuth.unitypackage`
 - `FirebaseFirestore.unitypackage`
 - Or use Unity Package Manager if available

---

## 🎮 Running the Project

1. Clone the repo:
 ```bash
 git clone https://github.com/amr-shafiq/medical-assistant-unity.git
 cd medical-assistant-unity

