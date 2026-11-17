import { create } from 'zustand';
import { AgentChatMessage, AgentState, RestaurantInfo, MenuCategory } from '../types';

interface AppStore {
  // Voice & Chat State
  agentState: AgentState;
  messages: AgentChatMessage[];
  isMuted: boolean;
  activeTool: { name: string; args?: any; result?: any } | null;
  errorMessage: string | null;
  conversationId: string;
  interimTranscript: string;
  hasSpokenSupport: boolean;
  
  // Restaurant Info
  restaurant: RestaurantInfo | null;
  menuCategories: MenuCategory[];
  
  // Actions
  setAgentState: (state: AgentState) => void;
  addMessage: (message: AgentChatMessage) => void;
  updateLastAssistantMessage: (chunk: string) => void;
  toggleMute: () => void;
  setActiveTool: (tool: { name: string; args?: any; result?: any } | null) => void;
  setErrorMessage: (msg: string | null) => void;
  setInterimTranscript: (text: string) => void;
  setRestaurant: (info: RestaurantInfo) => void;
  setMenuCategories: (categories: MenuCategory[]) => void;
  resetConversation: () => void;
}

export const useAppStore = create<AppStore>((set) => ({
  agentState: 'idle',
  messages: [
    {
      id: 'init-msg',
      role: 'assistant',
      content: "Hello! Welcome to Aura & Embers Bistro. I am your real-time voice concierge. Would you like to reserve a table, view our hearth-roasted menu, or ask about allergens?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ],
  isMuted: false,
  activeTool: null,
  errorMessage: null,
  conversationId: 'conv-' + Math.random().toString(36).substring(2, 9),
  interimTranscript: '',
  hasSpokenSupport: true,
  restaurant: null,
  menuCategories: [],

  setAgentState: (state) => set({ agentState: state }),
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  updateLastAssistantMessage: (chunk) => set((s) => {
    const list = [...s.messages];
    const lastIdx = list.length - 1;
    if (lastIdx >= 0 && list[lastIdx].role === 'assistant') {
      list[lastIdx] = { ...list[lastIdx], content: chunk };
      return { messages: list };
    }
    return { messages: s.messages };
  }),
  toggleMute: () => set((s) => ({ isMuted: !s.isMuted })),
  setActiveTool: (tool) => set({ activeTool: tool }),
  setErrorMessage: (msg) => set({ errorMessage: msg }),
  setInterimTranscript: (text) => set({ interimTranscript: text }),
  setRestaurant: (info) => set({ restaurant: info }),
  setMenuCategories: (categories) => set({ menuCategories: categories }),
  resetConversation: () => set({
    conversationId: 'conv-' + Math.random().toString(36).substring(2, 9),
    messages: [
      {
        id: 'init-reset',
        role: 'assistant',
        content: "Hello! Welcome back to Aura & Embers. How can I assist you with your dining experience today?",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
    ],
    agentState: 'idle',
    activeTool: null,
    errorMessage: null
  })
}));
