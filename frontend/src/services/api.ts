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
    sendMessage: async (message: ChatMessage, useDbPriority: boolean = true): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/chat', message, {
            params: { use_db_priority: useDbPriority },
        });
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

    setDbPriorityMode: async (enabled: boolean): Promise<{ message: string }> => {
        const response = await api.post<{ message: string }>('/chat/db-mode', null, {
            params: { enabled },
        });
        return response.data;
    },

    getDbPriorityMode: async (): Promise<{ db_priority_mode: boolean }> => {
        const response = await api.get<{ db_priority_mode: boolean }>('/chat/db-mode');
        return response.data;
    },
}; 