# Audio Transcription & Sales Lead Extraction Prototype

## Overview

This is a prototype implementation for extracting structured sales lead metadata from audio conversations between financial advisors and customers. The system performs automatic speech recognition (ASR), speaker diarization, and metadata extraction using Google Gemini APIs.

**Status**: Prototype – Not for production use. Designed for MVP validation and proof-of-concept workflows.

## Architecture & Workflow

The pipeline executes in five stages:

```
Audio Upload → Processing Queue → Transcription (ASR) → Speaker Diarization → Lead Metadata Extraction → JSON Output
```

### Stage-by-Stage Breakdown

1. **Audio Upload & Security Configuration**
   - Validates `GEMINI_API_KEY` environment variable
   - Uploads audio file to Google Cloud via Gemini API
   - Returns Cloud Resource Name for downstream processing

2. **Status Lifecycle Guard**
   - Polls file processing status until `ACTIVE` state
   - Handles `FAILED` state with immediate exit
   - Retry interval: 2 seconds (configurable)

3. **Transcription & Speaker Diarization**
   - Uses `gemini-3.1-flash-lite` model
   - Enforces word-for-word (verbatim) transcription
   - Automatically separates speakers with labels (Speaker 1:, Speaker 2:, etc.)
   - Each speaker turn starts on a new line

4. **Structured Sales Lead Extraction**
   - Uses `gemma-4-31b-it` model
   - Outputs JSON with three fields:
     - `intent`: "Strong" (purchase intent) or "Weak" (information gathering)
     - `primary_focus`: "Yield/Return", "Flexibility/Duration", "Safety/Risk", or "General/Unknown"
     - `target_product`: Specific product name or "None"

5. **JSON Validation & Output**
   - Strips markdown formatting (if present)
   - Validates JSON structure
   - Pretty-prints to console

## Files in This Repository

| File | Purpose |
|------|---------|
| `transcribe.py` | Main application code |
| `conversation1.wav` | Mock conversation scenario 1 (financial advisor ↔ customer) |
| `conversation2.wav` | Mock conversation scenario 2 (financial advisor ↔ customer) |
| `raw_conversation.txt` | Source transcript used to generate conversation WAV files |
| `output_conversation_1.log` | Terminal output from running `conversation1.wav` |
| `output_conversation_2.log` | Terminal output from running `conversation2.wav` |

## Setup & Installation

### Prerequisites

- Python 3.8+
- Google Gemini API key with audio processing access
- Audio files in `.wav` format

### Install Dependencies

```bash
pip install google-genai
```

### Configure API Key

Set your Gemini API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or pass it directly in the code (not recommended for production).

## Usage

### Run on a Specific Audio File

```bash
python transcribe.py
```

The script currently processes `conversation1.wav` (hardcoded). To process a different file, modify line 24:

```python
AUDIO_FILE = "your_audio_file.wav"
```

### Sample Output

**Terminal Output:**
```
INFO: Uploading audio file: conversation1.wav...
INFO: File uploaded successfully. Cloud Resource Name: files/abc123xyz...
INFO: Waiting for cloud audio processing to complete...
SUCCESS: Audio processing complete (State: ACTIVE).
INFO: Requesting high-accuracy transcription and speaker diarization...

--- [Transcript Preview] ---
Speaker 1: Good morning, I'm interested in your Steady Returns product.
Speaker 2: Excellent. Let me explain the key features...
----------------------------

INFO: Requesting structured sales lead metadata extraction...
SUCCESS: Final Structured Sales Lead JSON Object:
{
    "intent": "Strong",
    "primary_focus": "Yield/Return",
    "target_product": "Steady Returns No. 1"
}
```

## Extracted Sales Lead Schema (Prototype)

```json
{
  "intent": "Strong|Weak",
  "primary_focus": "Yield/Return|Flexibility/Duration|Safety/Risk|General/Unknown",
  "target_product": "Product Name|None"
}
```

**Important**: This schema is a sample baseline and has not been validated with Business Units. In production, this structure will likely be extended to capture:
- Customer risk profile
- Recommended products
- Conversation outcome flags
- Follow-up actions
- Compliance/regulatory notes

The current simplified structure is intentional—optimized for MVP feedback loops before adding complexity.

## Production Deployment & Streaming Audio

This prototype uses **polling-based file processing**, which is suitable for small-scale testing but not recommended for production workflows.

### For Production: Use Google Gemini 2.5 Flash Native Audio Dialog

For real-time, low-latency audio streaming in production, migrate to:

```
Google Gemini 2.5 Flash Native Audio Dialog API
  → Streams audio in real time
  → Lower latency than file upload/polling
  → Better for live advisor-customer scenarios
```

**Migration steps** (not included in this prototype):
1. Replace `client.files.upload()` with WebSocket/streaming endpoint
2. Switch to `gemini-2.5-flash-native-audio` model
3. Implement bidirectional streaming for real-time diarization
4. Add buffering/jitter handling for network resilience

## Models Used

| Component | Current Model | Alternative/Production |
|-----------|---------------|------------------------|
| Transcription & Diarization | `gemini-3.1-flash-lite` | `gemini-2.5-flash-native-audio` (production) |
| Lead Extraction | `gemma-4-31b-it` | Domain-specific fine-tuned model (future) |
| TTS (if needed) | Google Cloud TTS | Depends on use case |

Models can be swapped in the code for more specialized scenarios.

## Limitations & Known Issues

- **Prototype Only**: Not tested at scale or in regulated environments
- **Polling-based**: File upload/status polling not suitable for real-time scenarios
- **Limited Metadata**: Only 3 fields extracted; production will require richer schema
- **Hardcoded File Path**: Must modify `AUDIO_FILE` variable for each run
- **API Key in Code**: Production should use secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)
- **No Error Recovery**: Failed transcriptions exit immediately; production needs retry logic
- **Speaker Labels**: Generic "Speaker 1/2" labels; no speaker identification or confidence scores

## Next Steps for Production

1. **Validate with Business Unit** → Refine lead extraction schema
2. **Migrate to Native Audio Streaming** → Use Gemini 2.5 Flash for real-time processing
3. **Add Persistence Layer** → Store transcripts and metadata in database
4. **Implement Audit Logging** → Track conversations for compliance/regulatory review
5. **Build API Wrapper** → Expose as REST/gRPC service for advisor tools
6. **Add Speaker Identification** → Map speakers to advisor/customer IDs
7. **Error Handling & Retry Logic** → Production-grade resilience
8. **Performance Testing** → Latency, throughput, concurrent sessions
9. **Security Hardening** → Encryption, PII masking, access controls
10. **Fine-tuning** → Train custom models for financial domain specifics

## Testing with Mock Scenarios

Two test scenarios are included:

```bash
# Scenario 1
python transcribe.py  # Uses conversation1.wav

# Scenario 2 (modify AUDIO_FILE = "conversation2.wav" and re-run)
```

See `output_conversation_1.log` and `output_conversation_2.log` for expected outputs.

## Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `GEMINI_API_KEY` | Yes | Embedded key (fallback) | Google Gemini API key |

## License

This project is provided as-is without any license restrictions.

## Contributing

This is a prototype. For contributions, feedback, or issues:
1. Test against mock scenarios first
2. Document any schema changes needed for Business Unit review
3. Flag production-readiness blockers explicitly

## Contact & Support

- **Status**: Prototype / MVP Validation Phase
- **Last Updated**: 2026-07-14
- **Maintainer**: [Your name/team]
