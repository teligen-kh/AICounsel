import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ChatResponse {
  content: string;
}

export const chatService = {
  async sendMessage(message: string): Promise<ChatResponse> {
    try {
      const response = await axios.post<ChatResponse>(`${API_BASE_URL}/chat`, {
        message,
      });
      return response.data;
    } catch (error) {
      console.error('Error in chatService.sendMessage:', error);
      throw error;
    }
  },
}; 