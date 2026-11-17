export interface RestaurantInfo {
  id: number;
  name: string;
  description: string;
  address: string;
  phone: string;
  email: string;
  timezone: string;
  reservation_policy: string;
  hours: { day: string; open: string; close: string; is_closed: boolean }[];
}

export interface MenuItem {
  id: number;
  name: string;
  description: string;
  price: number;
  is_available: boolean;
  is_vegan: boolean;
  is_vegetarian: boolean;
  is_gluten_free: boolean;
  spicy_level: number;
  category_id: number;
  category_name?: string;
  allergens: string[];
  ingredients: string[];
}

export interface MenuCategory {
  id: number;
  name: string;
  display_order: number;
  items: MenuItem[];
}

export interface ReservationResponse {
  success: boolean;
  booking_code?: string;
  table_number?: string;
  seating_area?: string;
  date?: string;
  time?: string;
  party_size?: number;
  customer_name?: string;
  customer_phone?: string;
  message?: string;
  error?: string;
  requires_confirmation?: boolean;
}

export interface AgentChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  isAudio?: boolean;
  timestamp: string;
  toolCall?: {
    name: string;
    arguments?: any;
    result?: any;
  };
}

export type AgentState = 
  | 'idle'
  | 'listening'
  | 'transcribing'
  | 'thinking'
  | 'executing_tool'
  | 'speaking'
  | 'waiting_confirmation'
  | 'error';
