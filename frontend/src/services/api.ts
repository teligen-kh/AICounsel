import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface ChatMessage {
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    session_id: string;
}

export interface ChatResponse {
    response: string;
    context?: Record<string, any>;
}

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const chatApi = {
    sendMessage: async (message: ChatMessage): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/chat', message);
        return response.data;
    },

    getChatHistory: async (sessionId: string, limit = 50): Promise<ChatMessage[]> => {
        const response = await api.get<ChatMessage[]>(`/chat/history/${sessionId}`, {
            params: { limit },
        });
        return response.data.map(msg => ({
            ...msg,
            timestamp: new Date(msg.timestamp),
        }));
    },
}; 