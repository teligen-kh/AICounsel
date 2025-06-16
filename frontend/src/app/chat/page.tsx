'use client';

import { useState, useEffect, useRef } from 'react';
import { Box, Container, Paper, TextField, Button, Typography } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface Message {
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [sessionId] = useState(`session-${Date.now()}`);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      content: input,
      role: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: input,
          role: 'user',
          session_id: sessionId,
          message_type: 'text'
        }),
      });

      const data = await response.json();
      
      const assistantMessage: Message = {
        content: data.response,
        role: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      flexDirection: 'column',
      height: 'calc(100vh - 64px)', // 네비게이션 바 높이(64px)를 제외한 높이
      overflow: 'hidden'
    }}>
      <Container maxWidth="md" sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        py: 2,
        height: '100%'
      }}>
        <Paper elevation={3} sx={{ 
          flex: 1,
          display: 'flex', 
          flexDirection: 'column',
          height: '100%'
        }}>
          <Box sx={{ 
            p: 2, 
            backgroundColor: 'primary.main', 
            color: 'white',
            flexShrink: 0 // 헤더는 크기 고정
          }}>
            <Typography variant="h6">AI 상담사</Typography>
          </Box>
          
          <Box sx={{ 
            flex: 1, 
            p: 2, 
            overflow: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 1
          }}>
            {messages.map((message, index) => (
              <Box
                key={index}
                sx={{
                  alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                  backgroundColor: message.role === 'user' ? 'primary.light' : 'grey.100',
                  color: message.role === 'user' ? 'white' : 'text.primary',
                  p: 1,
                  px: 2,
                  borderRadius: 2,
                  maxWidth: '70%'
                }}
              >
                <Typography>{message.content}</Typography>
              </Box>
            ))}
            <div ref={messagesEndRef} />
          </Box>

          <Box sx={{ 
            p: 2, 
            display: 'flex', 
            gap: 1,
            flexShrink: 0, // 입력 영역은 크기 고정
            borderTop: 1,
            borderColor: 'divider'
          }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="메시지를 입력하세요..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              multiline
              maxRows={4}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <Button
              variant="contained"
              onClick={handleSend}
              endIcon={<SendIcon />}
            >
              전송
            </Button>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
} 