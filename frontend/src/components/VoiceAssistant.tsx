import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Mic, Volume2, VolumeX, Send, RefreshCw, Sparkles, AlertCircle, Wrench, Play } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { VoiceAdapter } from '../services/voiceAdapter';
import { AudioWaveform } from './AudioWaveform';
import { WS_BASE_URL } from '../config/api';

export const VoiceAssistant: React.FC = () => {
  const {
    agentState,
    setAgentState,
    messages,
    addMessage,
    isMuted,
    toggleMute,
    activeTool,
    setActiveTool,
    errorMessage,
    setErrorMessage,
    conversationId,
    interimTranscript,
    setInterimTranscript,
    resetConversation
  } = useAppStore();

  const [textInput, setTextInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);

  const wsRef = useRef<WebSocket | null>(null);
  const voiceAdapterRef = useRef<VoiceAdapter | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, interimTranscript]);

  const handleServerEvent = useCallback((data: any) => {
    if (data.type === 'thinking') {
      setAgentState('thinking');
    } else if (data.type === 'tool_started') {
      setAgentState('executing_tool');
      setActiveTool({ name: data.tool_name, args: data.arguments });
    } else if (data.type === 'tool_completed') {
      setActiveTool({ name: data.tool_name, result: data.result });
      if (data.result?.requires_confirmation) {
        setAgentState('waiting_confirmation');
      }
    } else if (data.type === 'agent_chunk') {
      setAgentState('speaking');

      if (!isMuted && voiceAdapterRef.current) {
        voiceAdapterRef.current.speak(data.content, () => {
          setAgentState('speaking');
        }, () => {
          setAgentState('idle');
        });
      } else {
        setAgentState('idle');
      }

      addMessage({
        id: Math.random().toString(),
        role: 'assistant',
        content: data.content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
    } else if (data.type === 'error') {
      setErrorMessage(data.message);
      setAgentState('error');
    }
  }, [isMuted, setAgentState, setActiveTool, setErrorMessage, addMessage]);

  const connectWebSocket = useCallback(() => {
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ws/conversation/${conversationId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setErrorMessage(null);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleServerEvent(data);
      } catch (e) {
        console.error('WS Parse Error', e);
      }
    };

    ws.onerror = () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 2500);
    };

    ws.onclose = () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 2500);
    };

    wsRef.current = ws;
  }, [conversationId, handleServerEvent, setErrorMessage]);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  // Initialize Voice Adapter
  useEffect(() => {
    const adapter = new VoiceAdapter(
      (text, isFinal) => {
        setInterimTranscript(text);
        if (isFinal && text.trim()) {
          sendUserMessage(text.trim(), true);
          setIsListening(false);
          setInterimTranscript('');
        }
      },
      (err) => {
        setErrorMessage(err);
        setIsListening(false);
        setAgentState('error');
      },
      () => {
        setIsListening(false);
        if (agentState === 'listening') {
          setAgentState('idle');
        }
      }
    );

    setSpeechSupported(adapter.isSpeechSupported);
    voiceAdapterRef.current = adapter;
  }, []);

  const sendUserMessage = (text: string, isAudio: boolean = false) => {
    if (!text.trim()) return;

    addMessage({
      id: Math.random().toString(),
      role: 'user',
      content: text,
      isAudio,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    setAgentState('thinking');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: isAudio ? 'user_transcript' : 'user_message',
        content: text,
        is_audio: isAudio
      }));
    } else {
      connectWebSocket();
      setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            type: isAudio ? 'user_transcript' : 'user_message',
            content: text,
            is_audio: isAudio
          }));
        } else {
          setErrorMessage('Connecting to reservation server... please try again.');
        }
      }, 500);
    }
  };

  const toggleMic = () => {
    if (!speechSupported) {
      setErrorMessage('Speech recognition is not supported in this browser. Please use the typed message box below.');
      return;
    }

    if (isListening) {
      voiceAdapterRef.current?.stopListening();
      setIsListening(false);
      setAgentState('idle');
    } else {
      setErrorMessage(null);
      setIsListening(true);
      setAgentState('listening');
      voiceAdapterRef.current?.startListening();
    }
  };

  const replaySpeech = (text: string) => {
    if (voiceAdapterRef.current) {
      setAgentState('speaking');
      voiceAdapterRef.current.speak(text, () => {
        setAgentState('speaking');
      }, () => {
        setAgentState('idle');
      });
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    sendUserMessage(textInput.trim(), false);
    setTextInput('');
  };

  const getStatusBadge = () => {
    switch (agentState) {
      case 'listening':
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-rose-500/10 text-rose-400 border border-rose-500/30 rounded-full text-xs font-medium animate-pulse"><Mic className="w-3.5 h-3.5" /> Listening to your microphone...</span>;
      case 'thinking':
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 rounded-full text-xs font-medium animate-pulse"><Sparkles className="w-3.5 h-3.5" /> Processing request...</span>;
      case 'executing_tool':
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-amber-500/10 text-amber-400 border border-amber-500/30 rounded-full text-xs font-medium"><Wrench className="w-3.5 h-3.5" /> Checking database ({activeTool?.name})...</span>;
      case 'speaking':
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-medium"><Volume2 className="w-3.5 h-3.5" /> Speaking response...</span>;
      case 'waiting_confirmation':
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/30 rounded-full text-xs font-medium"><AlertCircle className="w-3.5 h-3.5" /> Confirmation needed</span>;
      case 'error':
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-red-500/10 text-red-400 border border-red-500/30 rounded-full text-xs font-medium"><AlertCircle className="w-3.5 h-3.5" /> Notice</span>;
      default:
        return <span className="flex items-center gap-1.5 px-3 py-1 bg-stone-800 text-stone-300 border border-stone-700 rounded-full text-xs font-medium">Ready</span>;
    }
  };

  return (
    <div className="flex flex-col h-[750px] bg-stone-900 border border-stone-800 rounded-2xl shadow-2xl overflow-hidden">
      {/* Top Bar Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-stone-800 bg-stone-950/40">
        <div className="flex items-center gap-3">
          <div className="w-3 h-3 rounded-full bg-emerald-500 animate-ping" />
          <div>
            <h2 className="text-base font-semibold text-white tracking-wide">Aura & Embers AI Voice Host</h2>
            <p className="text-xs text-stone-400">Natural voice conversation & table reservations</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {getStatusBadge()}
          <button
            onClick={toggleMute}
            className={`p-2 rounded-lg border transition ${isMuted ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' : 'bg-stone-800 text-stone-300 border-stone-700 hover:bg-stone-700'}`}
            title={isMuted ? 'Unmute AI Voice' : 'Mute AI Voice'}
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <button
            onClick={resetConversation}
            className="p-2 rounded-lg bg-stone-800 text-stone-300 border border-stone-700 hover:bg-stone-700 transition"
            title="Reset conversation"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Center Voice Visualizer */}
      <div className="bg-gradient-to-b from-stone-950/80 to-stone-900/60 py-6 border-b border-stone-800/80">
        <AudioWaveform agentState={agentState} isListening={isListening} />
        
        {/* Active Tool Badge if tool invoked */}
        {activeTool && (
          <div className="flex justify-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-stone-800/90 border border-stone-700 rounded-md text-xs text-stone-300">
              <Wrench className="w-3.5 h-3.5 text-amber-400" />
              <span>Tool Call: <code className="text-amber-300">{activeTool.name}</code></span>
            </div>
          </div>
        )}
      </div>

      {/* Error Alert Display */}
      {errorMessage && (
        <div className="px-6 py-2 bg-rose-950/60 border-y border-rose-800/50 flex items-center justify-between text-xs text-rose-300">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="underline hover:text-white">Dismiss</button>
        </div>
      )}

      {/* Conversation Stream */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                m.role === 'user'
                  ? 'bg-rose-600 text-white shadow-md rounded-br-none'
                  : 'bg-stone-800/90 text-stone-100 border border-stone-700/60 rounded-bl-none'
              }`}
            >
              <div className="flex items-center justify-between gap-3 mb-1 text-[10px] opacity-70">
                <div className="flex items-center gap-1.5">
                  <span>{m.role === 'user' ? 'You' : 'VOX Concierge'}</span>
                  {m.isAudio && <span>• 🎙️ Spoken</span>}
                  <span>• {m.timestamp}</span>
                </div>
                {m.role === 'assistant' && (
                  <button
                    onClick={() => replaySpeech(m.content)}
                    className="p-1 hover:text-amber-300 text-stone-400 transition"
                    title="Read this message aloud"
                  >
                    <Play className="w-3 h-3" />
                  </button>
                )}
              </div>
              <p className="whitespace-pre-line">{m.content}</p>
            </div>
          </div>
        ))}

        {/* Live Interim Transcript */}
        {interimTranscript && (
          <div className="flex flex-col items-end">
            <div className="max-w-[80%] bg-rose-950/40 border border-rose-600/40 text-rose-200 rounded-2xl rounded-br-none px-4 py-3 text-sm italic animate-pulse">
              {interimTranscript}...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Controls Bar */}
      <div className="p-4 bg-stone-950/80 border-t border-stone-800 flex flex-col gap-3">
        {/* Quick Suggestion Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
          <span className="text-stone-400 text-[11px] whitespace-nowrap">Try saying:</span>
          <button
            onClick={() => sendUserMessage("Table for four people tomorrow at 7 PM")}
            className="px-2.5 py-1 bg-stone-800/80 hover:bg-stone-700 text-stone-300 rounded-full border border-stone-700 whitespace-nowrap transition"
          >
            "Table for four people tomorrow at 7 PM"
          </button>
          <button
            onClick={() => sendUserMessage("What are your opening hours?")}
            className="px-2.5 py-1 bg-stone-800/80 hover:bg-stone-700 text-stone-300 rounded-full border border-stone-700 whitespace-nowrap transition"
          >
            "What are your opening hours?"
          </button>
          <button
            onClick={() => sendUserMessage("Do you have gluten-free or dairy-free dishes?")}
            className="px-2.5 py-1 bg-stone-800/80 hover:bg-stone-700 text-stone-300 rounded-full border border-stone-700 whitespace-nowrap transition"
          >
            "Any gluten-free dishes?"
          </button>
          <button
            onClick={() => sendUserMessage("Yes, please confirm the reservation!")}
            className="px-2.5 py-1 bg-stone-800/80 hover:bg-stone-700 text-stone-300 rounded-full border border-stone-700 whitespace-nowrap transition"
          >
            "Yes, please confirm!"
          </button>
        </div>

        {/* Controls: Microphone + Typed Input */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleMic}
            className={`p-3.5 rounded-full shadow-lg transition-all transform active:scale-95 flex items-center justify-center ${
              isListening
                ? 'bg-rose-500 text-white ring-4 ring-rose-500/30 animate-pulse'
                : 'bg-stone-800 text-stone-200 hover:bg-stone-700 border border-stone-700'
            }`}
            title={isListening ? 'Click to stop listening' : 'Click to speak via microphone'}
          >
            <Mic className={`w-5 h-5 ${isListening ? 'text-white' : 'text-stone-300'}`} />
          </button>

          <form onSubmit={handleTextSubmit} className="flex-1 flex items-center gap-2">
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={isListening ? "Listening... speak now or click mic to finish" : "Speak via mic or type here..."}
              className="flex-1 px-4 py-2.5 bg-stone-900 border border-stone-700/80 rounded-xl text-sm text-stone-200 placeholder-stone-500 focus:outline-none focus:border-rose-500 transition"
            />
            <button
              type="submit"
              disabled={!textInput.trim()}
              className="p-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-40 text-white rounded-xl transition shadow-md"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
