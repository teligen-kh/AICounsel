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
        const startTime = performance.now();
        console.log('=== 프론트엔드 API 요청 시작 ===');
        console.log(`요청 시간: ${new Date().toISOString()}`);
        console.log(`메시지 내용: "${message.content}"`);
        console.log(`세션 ID: ${message.session_id}`);
        console.log(`메시지 길이: ${message.content.length}`);
        
        try {
            const requestData = {
                message: message.content,
                conversation_id: message.session_id
            };
            console.log('요청 데이터:', requestData);
            
            const requestStart = performance.now();
            const response = await api.post<ChatResponse>('/chat/send', requestData);
            const requestTime = performance.now() - requestStart;
            
            console.log('=== 프론트엔드 API 응답 수신 ===');
            console.log(`요청 처리 시간: ${requestTime.toFixed(2)}ms`);
            console.log(`응답 상태: ${response.status}`);
            console.log(`응답 데이터:`, response.data);
            console.log(`응답 길이: ${response.data.response?.length || 0}`);
            
            const totalTime = performance.now() - startTime;
            console.log(`전체 처리 시간: ${totalTime.toFixed(2)}ms`);
            console.log('=== 프론트엔드 API 요청 완료 ===');
            
            return response.data;
        } catch (error: any) {
            const errorTime = performance.now() - startTime;
            console.error('=== 프론트엔드 API 오류 발생 ===');
            console.error(`오류 발생 시간: ${errorTime.toFixed(2)}ms`);
            console.error('오류 내용:', error);
            console.error('응답 데이터:', error.response?.data);
            console.error('상태 코드:', error.response?.status);
            throw error;
        }
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