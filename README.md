# WhatsApp Message Notification Router

## Project Overview
This project builds a scalable, modular Python pipeline that routes WhatsApp-style messages into one of three actions:
- notify
- digest
- mute

The current implementation uses a rule-based classifier and a retrieval layer over historical messages. The architecture is designed so that future integrations with OpenAI, vision models, speech-to-text, RAG, and vector databases can be added without rewriting the project.

## Folder Structure
- dataset/ - input CSV datasets
- media/ - media files such as images and voice notes
- output/ - generated routing outputs
- src/ - Python source code
- tests/ - future unit and integration tests

## Installation
1. Create and activate a Python 3.11+ environment.
2. Install dependencies:
   ```powershell
   py -m pip install -r requirements.txt
   ```
3. Copy .env.example to .env and update values if needed.

## How to Run
From the project root:
```powershell
py .\src\main.py
```

## Future Improvements
- Add GPT-4.1-based classification
- Add image OCR and captioning
- Add Whisper-based voice transcription
- Add retrieval augmented generation with a vector database
- Add evaluation and test coverage
