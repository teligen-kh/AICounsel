import { useState } from 'react';
import {
  Box,
  IconButton,
  InputBase,
  Paper,
} from '@mui/material';
import {
  Send as SendIcon,
  Mic as MicIcon,
  Image as ImageIcon,
} from '@mui/icons-material';
import { useChatStore } from '@/store/useChatStore';
import { chatService } from '@/services/chatService';

export default function ChatInput() {
  const [message, setMessage] = useState('');
  const { addMessage, setLoading, sessionId } = useChatStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      // 사용자 메시지 추가
      addMessage({
        text: message.trim(),
        sender: 'user',
      });
      
      setMessage('');
      setLoading(true);

      try {
        // API 호출
        const response = await chatService.sendMessage(message.trim(), sessionId);
        
        // AI 응답 추가
        addMessage({
          text: response.response,
          sender: 'ai',
        });
      } catch (error) {
        console.error('Error getting AI response:', error);
        // 에러 메시지 표시
        addMessage({
          text: '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
          sender: 'ai',
        });
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{
        p: 2,
        backgroundColor: 'background.default',
      }}
    >
      <Paper
        sx={{
          p: '2px 4px',
          display: 'flex',
          alignItems: 'center',
          borderRadius: 3,
        }}
      >
        <IconButton sx={{ p: '10px' }} aria-label="image">
          <ImageIcon />
        </IconButton>
        <InputBase
          sx={{ ml: 1, flex: 1 }}
          placeholder="메시지를 입력하세요"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          multiline
          maxRows={4}
        />
        <IconButton sx={{ p: '10px' }} aria-label="voice">
          <MicIcon />
        </IconButton>
        <IconButton
          type="submit"
          sx={{ p: '10px' }}
          aria-label="send"
          disabled={!message.trim()}
        >
          <SendIcon />
        </IconButton>
      </Paper>
    </Box>
  );
} 