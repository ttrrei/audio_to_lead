import os
import time
import json
import sys
from google import genai
from google.genai import types

# =====================================================================
# 1. Client Initialization & Security Configuration
# =====================================================================
API_KEY = os.environ.get("GEMINI_API_KEY", "AQ****")
if not API_KEY or API_KEY.startswith("AQ**"):
    print("WARNING: No valid GEMINI_API_KEY environment variable detected. Falling back to embedded key.")

client = genai.Client(api_key=API_KEY)
AUDIO_FILE = "conversation1.wav"

# =====================================================================
# 2. Audio Upload & Status Lifecycle Guard
# =====================================================================
print(f"INFO: Uploading audio file: {AUDIO_FILE}...")
uploaded_file = client.files.upload(file=AUDIO_FILE)
print(f"INFO: File uploaded successfully. Cloud Resource Name: {uploaded_file.name}")

print("INFO: Waiting for cloud audio processing to complete...")
while True:
    file_info = client.files.get(name=uploaded_file.name)
    if file_info.state.name == "ACTIVE":
        print("SUCCESS: Audio processing complete (State: ACTIVE).")
        break
    elif file_info.state.name == "FAILED":
        print("ERROR: Cloud audio processing failed on the server.")
        sys.exit(1)
    else:
        print(f"INFO: Current state: {file_info.state.name}. Retrying in 2 seconds...")
        time.sleep(2)

# =====================================================================
# 3. Audio Transcription Stage (ASR)
# =====================================================================
print("INFO: Requesting high-accuracy transcription and speaker diarization...")
transcribe_prompt = (
    "Transcribe the provided audio recording with absolute precision. You must enforce "
    "strict speaker separation. Adhere strictly to the following structural rules:\n"
    "1. Perform word-for-word (verbatim) transcription.\n"
    "2. Identify each unique speaker and assign a clear identifier (e.g., Speaker 1:, Speaker 2:).\n"
    "3. Force a new line break immediately when a different person begins speaking.\n"
    "4. Begin every single sentence or turn with the assigned speaker prefix.\n"
    "Do not group distinct speakers into the same paragraph or block of text under any circumstances."
)

response = client.models.generate_content(
    model='gemini-3.1-flash-lite',
    contents=[uploaded_file, transcribe_prompt]
)

if not response.text:
    print("ERROR: Transcription failed to generate any text output.")
    sys.exit(1)

print("\n--- [Transcript Preview] ---")
print(response.text)
print("----------------------------\n")

# =====================================================================
# 4. Sales Lead Metadata Extraction Stage
# =====================================================================
print("INFO: Requesting structured sales lead metadata extraction...")

# Note: Literal JSON curly braces are escaped here using double braces {{ }}
prompt_template = """You are an expert sales lead qualification agent. Your task is to analyze the following customer conversation transcript and extract key sales metadata.

You must output a single, valid JSON object containing exactly three fields. Do not include any introductory text, markdown formatting (such as ```json), or explanatory footnotes. Output ONLY the raw JSON string.

### FIELDS TO EXTRACT:
1. "intent": String. Must be either "Strong" or "Weak". 
   - "Strong": The customer explicitly asks to purchase, requests a signup link, asks for immediate payment methods, or shows high urgency.
   - "Weak": The customer is just browsing, asking routine questions, comparing options, or states they will "think about it later".
2. "primary_focus": String. The main variable the customer cares about most. Options: "Yield/Return", "Flexibility/Duration", "Safety/Risk", or "General/Unknown".
3. "target_product": String. The exact name of the financial/insurance product mentioned by the customer. If no specific product is mentioned, output "None".

### OUTPUT FORMAT EXAMPLE:
{{"intent": "Weak", "primary_focus": "Flexibility/Duration", "target_product": "Steady Returns No. 1"}}

### TRANSCRIPT TO ANALYZE:
{transcript}"""

final_prompt = prompt_template.format(transcript=response.text)

final_response = client.models.generate_content(
    model='gemma-4-31b-it',
    contents=final_prompt
)

raw_json_text = final_response.text.strip()

# =====================================================================
# 5. JSON Safety Validation & Finalization
# =====================================================================
try:
    if raw_json_text.startswith("```"):
        raw_json_text = raw_json_text.split("```json")[-1].split("```")[0].strip()

    structured_lead = json.loads(raw_json_text)

    print("SUCCESS: Final Structured Sales Lead JSON Object:")
    print(json.dumps(structured_lead, indent=4))

except json.JSONDecodeError as e:
    print("ERROR: Model response failed validation. Invalid JSON format.")
    print(f"Raw unparsed data returned from model:\n{final_response.text}")
