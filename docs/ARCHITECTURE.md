# ARCHITECTURE — VOXRESERVE

VOXRESERVE is a real-time, AI-driven restaurant voice and text reservation platform designed to operate with zero paid API dependencies.

```mermaid
flowchart TD
    subgraph ClientBrowser [Browser Client Interface]
        MicCapture[Web Speech SpeechRecognition]
        SpeechSynth[Web Speech SpeechSynthesis]
        UI[React 18 + Tailwind + Lucide UI]
        WSClient[WebSocket Connection /ws/conversation]
    end

    subgraph BackendServer [FastAPI Backend Engine]
        WSEndpoint[WebSocket Endpoint /ws/conversation]
        Orchestrator[Agent Orchestrator & State Machine]
        ToolRegistry[Strict Typed Tool Registry]
        BookingEngine[Concurrency-Safe Booking Engine]
        AuthService[JWT & Security Service]
    end

    subgraph AIIntelligence [Open-Source AI Intelligence]
        OllamaServer[Local Ollama: llama3.2]
        DeterministicRules[Intelligent Fallback Rule Engine]
    end

    subgraph DatabaseLayer [PostgreSQL / SQLite Storage]
        TablesDB[(Tables & Capacity)]
        ReservationsDB[(Reservations & Concurrency Locks)]
        MenuDB[(Menu, Ingredients & Allergens)]
        AuditDB[(Audit Logs & Session Transcripts)]
    end

    MicCapture -->|User Transcript| WSClient
    WSClient <-->|Real-Time JSON Stream| WSEndpoint
    WSEndpoint <--> Orchestrator
    Orchestrator <-->|JSON Tool Calling| OllamaServer
    Orchestrator -.->|Offline Fallback| DeterministicRules
    Orchestrator --> ToolRegistry
    ToolRegistry --> BookingEngine
    BookingEngine --> DatabaseLayer
    WSEndpoint -->|Agent Response Chunks| WSClient
    WSClient --> SpeechSynth
```

## Core Components

1. **Client Browser**: Leverages browser-native Web Speech API for low-latency Speech-to-Text and Speech-to-Text without external billing or third-party tracking. Provides typed chat fallback if speech is denied or unsupported.
2. **WebSocket Conversation Protocol**: Transmits user transcripts, thinking indicators, database tool executions, and audio synthesis triggers in real time.
3. **Agent Tool Registry**: Strict validation preventing the LLM from executing raw queries or fabricating availability.
4. **Booking & Concurrency Engine**: Performs transactional re-validation inside nested transactions to ensure zero double-booking even under concurrent load.
