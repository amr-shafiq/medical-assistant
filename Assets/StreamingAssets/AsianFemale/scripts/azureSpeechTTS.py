import sys
import random
import re
import os
import gc
from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig, SpeechRecognizer, ResultReason
import firebase_admin
import asyncio
import time
from firebase_admin import credentials, firestore, initialize_app
from google.cloud.firestore_v1 import AsyncClient
import json
import warnings
from datetime import datetime
SESSION_FILE = "H:/Unity Workspace/ASR Final Project/Assets/AsianFemale/scripts/session_data.json"

warnings.filterwarnings("ignore", message=".*Detected filter using positional arguments.*")

# Get the directory of the current script (inside "scripts" folder)
base_path = os.path.dirname(os.path.abspath(__file__))

# Move one level up to "AsianFemale"
parent_path = os.path.dirname(base_path)

# Use relative paths
state_file_path = os.path.join(parent_path, "state.txt")
transcription_file_path = os.path.join(parent_path, "transcription.txt")
tts_output_file_path = os.path.join(parent_path, "tts_output.wav")

# Define the Firebase credentials file path (inside "config" folder)
firebase_cred_path = os.path.join(base_path, "config", "medical-database-977c4-firebase-adminsdk-s3aru-276c163bc4.json")

# Initialize Firebase
try:
    cred = credentials.Certificate("H:/medical-database-977c4-firebase-adminsdk-s3aru-276c163bc4.json")
    initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    sys.exit(1)

def read_state_from_file(state_file_path):
    """Reads state.txt for patient details."""
    try:
        with open(state_file_path, "r") as file:
            lines = file.readlines()
            state_data = {}
            for line in lines:
                key, value = line.strip().split("=", 1)
                state_data[key] = value
            return (state_data.get("currentState"), 
                    state_data.get("patientName"), 
                    state_data.get("symptoms"), 
                    state_data.get("disease"))
    except Exception as e:
        print(f"Error reading state file: {e}")
        return None, None, None, None


current_state, patient_name, symptoms, disease = read_state_from_file(state_file_path)



def write_state_to_file(new_state, patient_name, symptoms=None, disease=""):
    """
    Writes the current state, patient name, symptoms (as a comma-separated list), 
    and disease to the state file.
    
    Args:
        new_state (str): The new state to write.
        patient_name (str): The patient's name.
        symptoms (list or str): List of symptoms (converted to a string if it's a list).
        disease (str): Detected disease.
    """
    try:
        # Get the base directory (one level up from "scripts")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_path = os.path.dirname(script_dir)

        # Construct the state file path
        state_file_path = os.path.join(base_path, "state.txt")

        # Fetch disease from Firebase if patient_name is provided
        if patient_name:
            patients_ref = db.collection('Patients')
            query = patients_ref.where('name', '==', patient_name).get()

            if query:
                patient_data = query[0].to_dict()
                # print(f"DEBUG: Retrieved data for {patient_name}: {patient_data}")
                fetched_disease = patient_data.get('disease')
                if fetched_disease:
                    disease = fetched_disease
            else:
                print(f"")

        # Convert symptoms list to a comma-separated string if it's a list
        if isinstance(symptoms, list):
            symptoms = ",".join(symptoms)
        elif not symptoms:
            symptoms = ""  # Default to an empty string if no symptoms are provided

        # Write state to file
        with open(state_file_path, "w", encoding="utf-8") as file:
            file.write(f"currentState={new_state}\n")
            file.write(f"patientName={patient_name}\n")
            file.write(f"symptoms={symptoms}\n")
            file.write(f"disease={disease}\n")

    except Exception as e:
        print(f"Error writing to state file: {e}")






async def initialize_assistant_state():
    
    global state  # Use the global state dictionary

    # Reset local state
    state["waiting_for_name"] = True
    state["patient_name"] = None
    state["patient_id"] = None

    # If a patient document exists in Firestore, update waiting_for_name to True
    patients_ref = db.collection('Patients')
    documents = await patients_ref.get()

    for doc in documents:
        patient_ref = patients_ref.document(doc.id)
        await patient_ref.update({
            'waiting_for_name': True
        })

    # print("DEBUG: Assistant state initialized. Waiting for patient name.")

# Load session data from the file
def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as file:
            return json.load(file)
    else:
        return {
            "name": "",
            "state": "waiting_for_name",  # Initial state: waiting for name
            "symptoms": [],
            "last_interaction_time": ""
        }

# Save session data to the file
def save_session(session_data):
    with open(SESSION_FILE, "w") as file:
        json.dump(session_data, file)

async def get_or_store_patient_name(patient_name):
    """
    Checks if a patient exists in Firestore. If not, stores the name and returns the patient ID.
    """
    try:
        # Run Firestore query in a separate thread
        patient_id = await asyncio.to_thread(fetch_or_store_patient_sync, patient_name)
        # print(f"DEBUG: Patient ID returned: {patient_id}")
        return patient_id

    except Exception as e:
        print(f"Error getting or storing patient name: {e}")
        print(f"ERROR: asyncio.to_thread failed: {e}")
        return None

def fetch_or_store_patient_sync(patient_name):
    """
    Synchronous Firestore query to fetch or store patient info.
    """
    try:
        # Search for the patient in Firestore
        patient_ref = db.collection('Patients').where('name', '==', patient_name).limit(1).get()

        if patient_ref:
            # Return the patient ID if the patient is found
            patient_doc = patient_ref[0]
            return patient_doc.id  # Patient ID

        # If the patient is not found, store the new patient
        new_patient_ref = db.collection('Patients').add({
            'name': patient_name,
            'disease': None,
            'symptoms': [],
            'lastInteraction': firestore.SERVER_TIMESTAMP,
            'waiting_for_name': True  # Initial state
        })
        return new_patient_ref[1].id  # Corrected to retrieve document ID from the tuple

    except Exception as e:
        print(f"Error in fetch_or_store_patient_sync: {e}")
        raise
 

# Optimized async file reading
async def read_text_file(file_path):
    """
    Reads the transcription from the file asynchronously.
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            # print(f"DEBUG: Content of transcription.txt: '{content}'")  # Debug print
            return content
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

async def text_to_speech_async(text):
    subscription_key = "5MgcelMm0eRTAAcLGGuJGvxRHGsgA1TZcRvxk9tJEK7nQPSCLdSUJQQJ99ALACqBBLyXJ3w3AAAYACOGgwh9"
    region = "southeastasia"

    # Ensure the output path is resolved correctly
    # output_path = os.path.abspath(output_path)

    speech_config = SpeechConfig(subscription=subscription_key, region=region)
    audio_config = AudioConfig(filename=tts_output_file_path)

    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    # Use asyncio.to_thread to avoid blocking the event loop
    def synthesize_speech():
        result = synthesizer.speak_text_async(text).get()
        if result.reason == result.reason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.error_details:
                print(f"Error details: {cancellation_details.error_details}")
        else:
            return result
    await asyncio.to_thread(synthesize_speech)
    
async def register_new_patient(name):
    try:
        doc_ref = db.collection('Patients').add({
            "name": name,
            "symptoms": [],
            "disease": None,
            "lastInteraction": firestore.SERVER_TIMESTAMP,
            "state": "WAITING_FOR_SYMPTOMS"
        })
        return doc_ref.id  # Return patient ID
    except Exception as e:
        print(f"Error registering new patient: {e}")
        return None

def get_patient_data(patient_name, update_data=None):
    try:
        patients_ref = db.collection('Patients')

        # Query for an existing patient
        query = patients_ref.where('name', '==', patient_name).get()

        if query:
            # Patient exists, retrieve their document
            patient_doc = query[0]
            patient_ref = patients_ref.document(patient_doc.id)

            if update_data:
                update_data["lastInteraction"] = firestore.SERVER_TIMESTAMP  # Update interaction timestamp
                patient_ref.update(update_data)

            # Log the interaction in the subcollection
            log_data = {
                "status": "updated" if update_data else "retrieved",
                "date": firestore.SERVER_TIMESTAMP,
                "activity": update_data or "Checked patient record"
            }
            patient_ref.collection('logs').add(log_data)

            return {'id': patient_doc.id, 'data': patient_doc.to_dict()}

        else:
            # Create a new patient entry
            new_patient_data = {
                'name': patient_name,
                'disease': None,
                'symptoms': [],
                'lastInteraction': firestore.SERVER_TIMESTAMP,
                'state': 'waiting_for_name'
            }
            new_patient_ref = patients_ref.document()
            new_patient_ref.set(new_patient_data)

            # Log the creation in the subcollection
            log_data = {
                "status": "created",
                "date": firestore.SERVER_TIMESTAMP,
                "activity": "New patient record created"
            }
            new_patient_ref.collection('logs').add(log_data)

            return {'id': new_patient_ref.id, 'data': new_patient_data}

    except Exception as e:
        print(f"Error in Firebase operation: {e}")
        return None



def log_patient_action(patient_name, state, action_details):    
    try:
        # Ensure action_details is a string (for logging)
        if isinstance(action_details, list):
            # If it's a list (such as symptoms), join the items into a string
            action_details = ', '.join([str(item) for item in action_details])
        elif isinstance(action_details, dict):
            # If it's a dictionary (for example, symptoms in a dictionary form), handle it accordingly
            action_details = ', '.join([str(key) for key in action_details.keys()])


        # Get the patient data
        patient_data = get_patient_data(patient_name)

        if patient_data:
            patient_id = patient_data['id']
            logs_ref = db.collection('Patients').document(patient_id).collection('logs')

            # Ensure the logs subcollection exists (Firestore handles it automatically, but we can check if it's empty)
            log_entry = {
                "state": state,
                "action": action_details,
                "timestamp": firestore.SERVER_TIMESTAMP
            }

            # Add the log entry to the logs subcollection
            logs_ref.add(log_entry)
            # print(f"DEBUG: Logged action for {patient_name}: {log_entry}")

    except Exception as e:
        print(f"Error logging patient action: {e}")



    
# Main assistant conversation function
# Function to simulate the assistant's conversation
async def assistant_conversation():

    # Get the base directory (one level up from "scripts")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(script_dir)

    # Construct paths
    state_file_path = os.path.join(base_path, "state.txt")
    transcription_file_path = os.path.join(base_path, "transcription.txt")

    # Read the state and patient name from state.txt
    current_state, patient_name, symptoms, disease = read_state_from_file(state_file_path)

    # Read transcription from transcription.txt
    transcription = await read_text_file(transcription_file_path)
    updated_symptoms = []

    # Handle 'waiting_for_name' state
    if current_state == "waiting_for_name": 
        extracted_name = extract_name(transcription)
        
        if extracted_name:
            patient_name = extracted_name

            # Check if patient exists in Firestore
            patients_ref = db.collection('Patients')
            query = patients_ref.where('name', '==', patient_name).get()

            if query:
                # Returning patient
                patient_data = query[0].to_dict()
                previous_disease = patient_data.get('disease', None)
                last_interaction = patient_data.get('lastInteraction', None)
                previous_symptoms = patient_data.get('symptoms', [])

                # Format the last interaction date to show only day, month, and year
                if last_interaction:
                    last_interaction_date = last_interaction.strftime("%B %d, %Y")  # e.g., "January 20, 2025"
                else:
                    last_interaction_date = "unknown date"

                response = (
                    f"Hello, {patient_name}! Welcome back. How's your {previous_disease} been going? "
                    f"Have you experienced {', '.join(previous_symptoms)} recently?"
                    f"I think our last interaction was at {last_interaction_date}, was that correct?"
                    if previous_disease
                    else f"Hi there, {patient_name}! It is wonderful to see you again. How have you been feeling lately?"
                )
                write_state_to_file("waiting_for_name", patient_name, "", "")
                print(f"{response}")
            else:
                # New patient
                response = f"Thank you, {patient_name}. Could you please tell me about your symptoms?"
                print(f"{response}") 
                write_state_to_file("waiting_for_symptoms", patient_name, updated_symptoms, disease)  # Update state
                # Log state transition
                log_patient_action(patient_name, "waiting_for_symptoms", response)


            
        else:
            if any(keyword in transcription.lower() for keyword in ['thank you', 'thanks', 'appreciate']):
                response = f"You're very welcome, {patient_name}! I am happy to be of help. Feel free to reach out anytime!"
                print(f"{response}")
                
            # Handle goodbye or closing remarks
            elif any(keyword in transcription.lower() for keyword in ['goodbye', 'bye', 'see you', 'take care']):
                response = f"Goodbye and take care, {patient_name}! Wishing you all the best, and I am here whenever you need me."
                print(f"{response}")
                write_state_to_file("waiting_for_name", "", "", "")
            else:
                response = "I couldn't catch your name. Could you please say it again?"
        with open(transcription_file_path, "r", encoding="utf-8") as file:
            transcription = file.read().strip()
        await text_to_speech_async(response)
        

    # Handle 'waiting_for_symptoms' state
    elif current_state == "waiting_for_symptoms":
        if any(keyword in transcription.lower() for keyword in ['goodbye', 'bye', 'see you']):
            response = f"Thank you for your time, {patient_name}. Hope to see you again, Goodbye!"
            write_state_to_file("waiting_for_name", "", "", "")  # Reset state
            print(f"{response}")

            # Log end of session
            log_patient_action(patient_name, "end_session", response)
        else:
            symptoms = process_symptoms(transcription, patient_name)
            if symptoms:
                patient_data = get_patient_data(patient_name)

                # Ensure symptoms is a list
                if isinstance(symptoms, dict):  # If symptoms is a dict, convert it to a list
                    symptoms = list(symptoms.values())  # Make sure it's a list of strings

                # Get current symptoms (ensure it's an array)
                current_symptoms = patient_data['data'].get('symptoms', [])

                # Update the symptoms array with new symptoms
                updated_symptoms = current_symptoms + symptoms

                # Update disease if detected
                update_data = {
                    'symptoms': firestore.ArrayUnion(updated_symptoms),  # Append new symptoms to the existing array
                    'lastInteraction': firestore.SERVER_TIMESTAMP,
                }

                if disease:
                    update_data['disease'] = disease  # Add disease if it's detected

                # Update Firestore with new symptoms
                get_patient_data(patient_name, update_data)

                # Prepare response
                response = (
                    f"Thanks for sharing, {patient_name}. I have noted your symptoms: {', '.join(symptoms)}. "
                    f"How are you feeling overall? Do any of these symptoms worry you, or is there anything else you'd like to add?"
                )
                print(f"{response}")
                log_patient_action(patient_name, "waiting_for_symptoms", symptoms)  # Log symptoms properly
            else:
                response = f"I was not able to catch any symptoms from what you said, {patient_name}. Could you please try again? Do not worry, I am here to help!"
                print(f"{response}")
            write_state_to_file("waiting_for_symptoms", patient_name, updated_symptoms, disease)

        
        with open(transcription_file_path, "r", encoding="utf-8") as file:
            transcription = file.read().strip()
        await text_to_speech_async(response)
        return response


async def get_patient_name_from_firestore(patient_id):
    """
    Retrieves the patient's name from Firestore by their patient ID.
    """
    try:
        patient_doc = await db.collection('Patients').document(patient_id).get()
        if patient_doc.exists:
            patient_data = patient_doc.to_dict()
            return patient_data.get('name', '')
        else:
            return ''
    except Exception as e:
        print(f"Error getting patient name from Firestore: {e}")
        return ''




async def update_patient_symptoms(patient_name, detected_symptoms):
    """
    Updates the symptoms for a specific patient in Firestore.
    """
    try:
        # Assuming you are using Firestore
        patient_ref = db.collection('Patients').where('name', '==', patient_name).limit(1).get()

        if patient_ref:
            patient_doc = patient_ref[0]  # Assuming one result is found, you can refine this logic
            patient_data = patient_doc.to_dict()

            # Add or update the symptoms field in the document
            existing_symptoms = patient_data.get('symptoms', [])
            existing_symptoms.extend(detected_symptoms)  # Add new symptoms

            # Update the patient document with the new symptoms
            patient_doc.reference.update({
                'symptoms': existing_symptoms,
                'lastInteraction': firestore.SERVER_TIMESTAMP  # Update last interaction time
            })
            print(f"Symptoms for {patient_name} updated.")
        else:
            print(f"Patient {patient_name} not found in Firestore.")

    except Exception as e:
        print(f"Error updating symptoms for {patient_name}: {e}")





def extract_name(transcription):
    transcription = transcription.strip().lower()  # Clean up the string

    # Improved regex to handle apostrophes, hyphens, and more variations
    match = re.search(r"\b(my name is|i'm|i am|this is|name is|i am called|people call me)\s+([a-zA-Z\s\-']+)[\.\!?]?", 
                      transcription, re.IGNORECASE)
    
    if match:
        # Extract name and clean up any punctuation
        name = match.group(2).strip()
        # Clean up name by removing any stray non-alphanumeric characters except apostrophes and hyphens
        name = re.sub(r'[^\w\s\'\-]', '', name)
        
        # print(f"DEBUG: Name detected: {name}")
        return name
    else:
        print(f"")
    
    return None

gc.collect()

def process_symptoms(input_text, patient_name):
    """
    Analyzes the input text and provides a response based on detected symptoms.
    """
    input_text_lower = input_text.lower()
    
    # Expanded symptom set with more detailed keywords
    symptoms = {
        "fever": ["fever", "chills", "temperature", "high fever", "cold sweats", "feeling hot", "febrile", "feverish"],
        "headache": ["headache", "migraine", "pain in head", "tension headache", "throbbing pain", "dizziness", "pressure in head"],
        "nausea": ["nausea", "vomit", "sick to my stomach", "queasy", "upset stomach", "feeling like throwing up", "retching", "gagging"],
        "diarrhea": ["diarrhea", "loose stool", "stomach upset", "runny stool", "watery stool", "intestinal distress", "frequent bowel movement", "shitting", "shit"],
        "fatigue": ["tired", "fatigue", "low energy", "lack of energy", "exhaustion", "feeling drained", "lack of motivation", "tiredness"],
        "chest pain": ["chest pain", "tight chest", "pain in chest", "pressure in chest", "chest discomfort", "angina", "sharp chest pain"],
        "shortness of breath": ["shortness of breath", "difficulty breathing", "breathing problem", "dyspnea", "labored breathing", "can't catch breath", "tightness in chest"],
        "cough": ["cough", "dry cough", "wet cough", "persistent cough", "coughing up mucus", "coughing fits", "chronic cough"],
        "sore throat": ["sore throat", "scratchy throat", "painful swallowing", "throat irritation", "swollen throat", "itchy throat"],
        "congestion": ["nasal congestion", "stuffy nose", "blocked nose", "runny nose", "sinus congestion", "nasal blockage", "mucus buildup"],
        "sweating": ["excessive sweating", "night sweats", "profuse sweating", "drenching sweat", "sweating a lot", "perspiration"],
        "weight loss": ["unexplained weight loss", "sudden weight loss", "losing weight without trying", "unintentional weight loss"],
        "swelling": ["swelling", "edema", "fluid retention", "swollen ankles", "puffy face", "swollen joints", "swollen legs", "inflammation"],
        "joint pain": ["joint pain", "arthritis", "joint stiffness", "pain in knees", "shoulder pain", "back pain", "swollen joints", "muscle pain"],
        "dizziness": ["dizziness", "lightheaded", "vertigo", "feeling faint", "feeling unsteady", "balance issues", "spinning sensation"],
        "skin rash": ["skin rash", "red spots", "itchy rash", "blisters", "hives", "eczema", "allergic reaction", "skin irritation"],
        "vomiting": ["vomiting", "throwing up", "retching", "nausea followed by vomiting", "projectile vomiting", "chronic vomiting"],
        "abdominal pain": ["abdominal pain", "stomach ache", "cramps", "belly pain", "stomach bloating", "sharp stomach pain", "gastritis", "intestinal pain"],
        "back pain": ["back pain", "lower back pain", "upper back pain", "spinal pain", "chronic back pain", "muscle strain in back", "back discomfort"],
        "sleep disturbance": ["insomnia", "difficulty sleeping", "sleeping too much", "restlessness", "sleep deprivation", "nightmares", "lack of sleep"],
        "blurry vision": ["blurry vision", "vision problems", "double vision", "eyesight issues", "difficulty focusing", "eye strain", "diplopia"],
        "COVID-19": ["fever", "dry cough", "fatigue", "shortness of breath", "loss of taste", "loss of smell", "sore throat", "headache"],
        "urinary issues": ["painful urination", "frequent urination", "dark urine", "cloudy urine", "blood in urine", "urinary tract infection", "burning sensation while urinating"],
        "stomach bloating": ["stomach bloating", "abdominal distension", "feeling of fullness", "belly swelling", "gas buildup", "gastritis", "indigestion"],
        "leg cramps": ["leg cramps", "muscle spasms", "calf cramps", "muscle tightness", "muscle pain in legs", "pain in thighs"],
        "numbness": ["numbness", "loss of sensation", "tingling", "pins and needles", "numb fingers", "numbness in limbs"],
        "ringing in ears": ["ringing in ears", "tinnitus", "ear ringing", "buzzing in ears", "ear discomfort", "fullness in ears"],
        "heart palpitations": ["heart palpitations", "racing heart", "skipping heartbeat", "fluttering in chest", "rapid heartbeat", "irregular heartbeat"],
        "memory problems": ["memory problems", "forgetfulness", "difficulty remembering", "short-term memory loss", "confusion", "difficulty concentrating"],
        "cold hands and feet": ["cold hands", "cold feet", "poor circulation", "numb hands and feet", "hands and feet turning pale"],
        "hives": ["hives", "welts", "itchy bumps", "allergic rash", "urticaria", "raised red bumps", "skin rash"],
        "hair loss": ["hair loss", "balding", "thinning hair", "hair shedding", "patchy hair loss", "alopecia", "scalp hair loss"],
        "muscle weakness": ["muscle weakness", "muscle fatigue", "lack of strength", "muscle atrophy", "tired muscles", "muscle aches"],
        "dehydration": ["dehydration", "dry mouth", "thirst", "dark urine", "feeling thirsty", "dry skin", "fatigue from dehydration"],
        "chills": ["chills", "shivers", "cold sweats", "cold feeling", "shivering", "goosebumps", "chilled feeling"],
        "excessive thirst": ["excessive thirst", "unquenchable thirst", "dry mouth", "constant thirst", "polydipsia"],
        "night blindness": ["night blindness", "difficulty seeing in low light", "poor vision at night", "visual impairment in dark"],
        "chronic fatigue": ["chronic fatigue", "persistent tiredness", "constant fatigue", "ongoing exhaustion", "debilitating fatigue", "chronic tiredness"],
        "feeling faint": ["feeling faint", "lightheaded", "passing out", "feeling weak", "near fainting", "fainting spell"],
        "tingling": ["tingling", "pins and needles", "numbness in hands", "numbness in feet", "tingling sensation", "prickling sensation"]
    }

    # Disease mapping to symptoms
    disease_map = {
    "COVID-19": [
        "fever", "dry cough", "fatigue", "shortness of breath", 
        "loss of taste", "loss of smell", "sore throat", "headache", 
        "muscle pain", "chills", "diarrhea", "nausea"
    ],
    "Flu": [
        "fever", "chills", "fatigue", "sore throat", "cough", 
        "body aches", "headache", "congestion", "runny nose", 
        "muscle pain", "vomiting"
    ],
    "Migraine": [
        "headache", "dizziness", "nausea", "sensitivity to light", 
        "visual disturbances", "throbbing pain", "neck pain", 
        "sensitive to sound"
    ],
    "Gastroenteritis": [
        "diarrhea", "nausea", "abdominal pain", "vomiting", "stomach cramps", 
        "bloating", "loss of appetite", "fever", "dehydration", "gastritis"
    ],
    "Pneumonia": [
        "fever", "cough", "shortness of breath", "chest pain", 
        "fatigue", "difficulty breathing", "chills", "sweating", 
        "productive cough", "blue lips or face", "wheezing"
    ],
    "Asthma": [
        "shortness of breath", "wheezing", "chest tightness", "coughing", 
        "difficulty breathing", "labored breathing", "tightness in chest"
    ],
    "Anemia": [
        "fatigue", "weakness", "pale skin", "shortness of breath", 
        "dizziness", "cold hands and feet", "headache", "irregular heartbeat"
    ],
    "Heart Attack": [
        "chest pain", "shortness of breath", "pain in arm", "dizziness", 
        "nausea", "sweating", "fatigue", "pressure in chest", "lightheaded"
    ],
    "Diabetes": [
        "frequent urination", "excessive thirst", "fatigue", "blurred vision", 
        "unexplained weight loss", "slow healing wounds", "numbness in hands or feet"
    ],
    "Chronic Obstructive Pulmonary Disease (COPD)": [
        "shortness of breath", "chronic cough", "wheezing", "chest tightness", 
        "fatigue", "coughing up mucus", "difficulty breathing"
    ],
    "Urinary Tract Infection (UTI)": [
        "painful urination", "frequent urination", "blood in urine", 
        "cloudy urine", "strong-smelling urine", "pelvic pain", 
        "lower abdominal pain", "fever"
    ],
    "Peptic Ulcer Disease": [
        "abdominal pain", "stomach ache", "bloating", "nausea", "vomiting", 
        "heartburn", "indigestion", "gastritis", "loss of appetite"
    ],
    "Depression": [
        "fatigue", "low energy", "loss of interest in activities", 
        "insomnia", "poor concentration", "feeling worthless", 
        "irritability", "sadness", "weight changes", "hopelessness"
    ],
    "Osteoarthritis": [
        "joint pain", "joint stiffness", "pain in knees", "shoulder pain", 
        "swelling in joints", "back pain", "limited range of motion"
    ],
    "Chronic Fatigue Syndrome": [
        "chronic fatigue", "muscle pain", "sleep disturbances", "memory problems", 
        "concentration issues", "headaches", "sore throat", "swollen lymph nodes"
    ],
    "Stroke": [
        "sudden numbness", "weakness in limbs", "difficulty speaking", 
        "vision problems", "confusion", "headache", "dizziness", 
        "loss of balance", "drooping face"
    ],
    "Liver Disease": [
        "fatigue", "yellowing of the skin or eyes", "abdominal pain", 
        "swelling in the abdomen", "dark urine", "pale stool", "nausea", 
        "loss of appetite", "confusion"
    ],
    "Thyroid Disorders": [
        "fatigue", "weight gain or loss", "sensitivity to cold or heat", 
        "dry skin", "hair loss", "depression", "irregular heartbeat", 
        "muscle weakness", "difficulty concentrating"
    ],
    "Allergies": [
        "sneezing", "runny nose", "itchy eyes", "skin rash", "hives", 
        "nasal congestion", "itchy throat", "coughing", "swelling"
    ],
    "Hypertension (High Blood Pressure)": [
        "headache", "shortness of breath", "dizziness", "chest pain", 
        "fatigue", "blurred vision", "nosebleeds", "heart palpitations"
    ],
    "Lung Cancer": [
        "chronic cough", "shortness of breath", "chest pain", "weight loss", 
        "fatigue", "coughing up blood", "wheezing", "hoarseness"
    ],
    "Gout": [
        "joint pain", "swelling in joints", "redness", "warmth in joints", 
        "intense pain in big toe", "painful inflammation in joints"
    ],
    "Epilepsy": [
        "seizures", "confusion", "dizziness", "loss of consciousness", 
        "muscle stiffness", "involuntary movements", "memory loss"
    ],
    "Psoriasis": [
        "red patches of skin", "itchy skin", "scaly skin", "dry skin", 
        "swollen joints", "nail changes", "painful lesions"
    ]
}


    detected_symptoms = []

    # Check for each symptom category
    for symptom, keywords in symptoms.items():
        if any(keyword in input_text_lower for keyword in keywords):
            detected_symptoms.append(symptom)

    # Determine likely disease based on detected symptoms
    likely_disease = None
    max_matching_symptoms = 0

    for disease, associated_symptoms in disease_map.items():
        matching_symptoms = set(detected_symptoms) & set(associated_symptoms)
        if len(matching_symptoms) > max_matching_symptoms:
            likely_disease = disease
            max_matching_symptoms = len(matching_symptoms)

    if detected_symptoms:
        patients_ref = db.collection('Patients')
        query = patients_ref.where('name', '==', patient_name).get()

        if query:
            patient_doc = query[0]
            patient_ref = patients_ref.document(patient_doc.id)

            try:
                # Update Firestore with symptoms and disease
                update_data = {
                    'symptoms': firestore.ArrayUnion(detected_symptoms),
                    'lastInteraction': firestore.SERVER_TIMESTAMP,
                }
                if likely_disease:
                    update_data['disease'] = likely_disease

                patient_ref.update(update_data)
                
            except Exception as e:
                print(f"Error updating patient {patient_name}: {e}")
        else:
            print(f"No patient found with the name {patient_name}")

    return detected_symptoms


def transcribe_audio(file_path):
    """
    Transcribes audio from a given file using Azure Speech-to-Text.
    """
    speech_config = SpeechConfig(subscription="5MgcelMm0eRTAAcLGGuJGvxRHGsgA1TZcRvxk9tJEK7nQPSCLdSUJQQJ99ALACqBBLyXJ3w3AAAYACOGgwh9", region="southeastasia")
    audio_config = AudioConfig(filename=file_path)
    speech_recognizer = SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    result = speech_recognizer.recognize_once()
    if result.reason == result.reason.RecognizedSpeech:
        return result.text.strip()
    elif result.reason == result.reason.NoMatch:
        print("DEBUG: No speech could be recognized.")
        return None
    elif result.reason == result.reason.Canceled:
        print(f"DEBUG: Speech recognition canceled. Details: {result.cancellation_details}")
        return None


# Main function
async def main():
    
    await assistant_conversation()


# Run the main function in the asyncio loop
if __name__ == "__main__":
    asyncio.run(main())