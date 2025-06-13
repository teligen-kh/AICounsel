import { create } from 'zustand';
import { Message } from '@/components/chat/ChatMessageList';

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isLoading: false,
  addMessage: (message) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: Math.random().toString(36).substring(7),
          timestamp: new Date(),
          ...message,
        },
      ],
    })),
  setLoading: (loading) => set({ isLoading: loading }),
})); 