# VOICE PIPELINE SPECIFICATION

VOXRESERVE provides zero-cost, privacy-first voice interaction using the browser Web Speech API with modular interfaces for local STT/TTS engines.

## 1. Browser-Native Architecture (Default)
- **STT (Speech-to-Text)**: Uses `window.webkitSpeechRecognition` or `window.SpeechRecognition`.
  - Captures streaming microphone audio on device.
  - Generates interim transcriptions for real-time visual feedback.
  - Emits final transcribed text via WebSocket to FastAPI.
- **TTS (Text-to-Speech)**: Uses `window.speechSynthesis`.
  - Plays back assistant responses with zero network transmission.
  - Automatically selects high-quality natural voices.
- **Mute / Fallback**: Users can mute audio synthesis at any time or interact via the typed text interface.

## 2. Optional Local Adapters
- **Whisper.cpp**: Configurable via `WHISPER_CPP_URL` in `.env`.
- **Piper TTS**: Configurable via `PIPER_TTS_URL` in `.env`.

## 3. Privacy & Audio Data
- Raw audio buffers are never stored on disk.
- Only text transcripts are saved for audit logs.
- Microphone permissions are explicitly requested on the user's first interaction.
