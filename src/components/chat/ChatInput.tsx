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

export default function ChatInput() {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      // TODO: 메시지 전송 로직 구현
      console.log('Sending message:', message);
      setMessage('');
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