# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['azureSpeechTTS.py'],
    pathex=[],
    binaries=[('C:\\Python312\\Lib\\site-packages\\azure\\cognitiveservices\\speech\\Microsoft.CognitiveServices.Speech.core.dll', '.')],
    datas=[('H:/Unity Workspace/ASR Final Project/Assets/AsianFemale/config/medical-database-977c4-firebase-adminsdk-s3aru-276c163bc4.json', 'config'), ('H:/Unity Workspace/ASR Final Project/Assets/AsianFemale/state.txt', '.'), ('H:/Unity Workspace/ASR Final Project/Assets/AsianFemale/transcription.txt', '.'), ('H:/Unity Workspace/ASR Final Project/Assets/AsianFemale/tts_output.wav', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='azureSpeechTTS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
