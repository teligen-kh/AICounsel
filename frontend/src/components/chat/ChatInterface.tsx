import React, { useState, useRef, useEffect } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  Container, 
  IconButton,
  FormControlLabel,
  Switch,
  Tooltip
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import DatabaseIcon from '@mui/icons-material/Storage';
import ChatMessage from './ChatMessage';
import LoadingMessage from './LoadingMessage';
import { chatApi, ChatMessage as ChatMessageType } from '@/services/api';
import { v4 as uuidv4 } from 'uuid';

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const [useDbPriority, setUseDbPriority] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // 이전 대화 내용 불러오기
    const loadChatHistory = async () => {
      try {
        const history = await chatApi.getChatHistory(sessionId);
        setMessages(history);
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    };

    loadChatHistory();
  }, [sessionId]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: ChatMessageType = {
      content: input,
      role: 'user',
      timestamp: new Date(),
      session_id: sessionId,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatApi.sendMessage(userMessage, useDbPriority);
      const assistantMessage: ChatMessageType = {
        content: response.response,
        role: 'assistant',
        timestamp: new Date(),
        session_id: sessionId,
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // TODO: 파일 업로드 처리
      console.log('Selected file:', file);
    }
  };

  const handleDbPriorityToggle = (event: React.ChangeEvent<HTMLInputElement>) => {
    setUseDbPriority(event.target.checked);
  };

  return (
    <Container maxWidth="md" sx={{ height: '100vh', py: 4 }}>
      <Paper elevation={3} sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* 채팅 헤더 */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">AI 상담사</Typography>
          <Tooltip title="DB 우선 검색 모드: 활성화 시 MongoDB의 기존 답변을 우선적으로 참고합니다">
            <FormControlLabel
              control={
                <Switch
                  checked={useDbPriority}
                  onChange={handleDbPriorityToggle}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <DatabaseIcon fontSize="small" />
                  DB 우선
                </Box>
              }
              labelPlacement="start"
            />
          </Tooltip>
        </Box>

        {/* 메시지 영역 */}
        <Box sx={{ 
          flex: 1, 
          overflow: 'auto', 
          p: 2,
          display: 'flex',
          flexDirection: 'column',
          gap: 2
        }}>
          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              content={message.content}
              role={message.role}
              timestamp={message.timestamp}
            />
          ))}
          {isLoading && <LoadingMessage />}
          <div ref={messagesEndRef} />
        </Box>

        {/* 입력 영역 */}
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <input
              type="file"
              id="file-upload"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
            />
            <label htmlFor="file-upload">
              <IconButton component="span" color="primary">
                <AttachFileIcon />
              </IconButton>
            </label>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="메시지를 입력하세요..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              multiline
              maxRows={4}
            />
            <Button
              variant="contained"
              endIcon={<SendIcon />}
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
            >
              전송
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
} 