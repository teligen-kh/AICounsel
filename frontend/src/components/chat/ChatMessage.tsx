import { Paper, Typography, Box } from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import React from 'react';

interface ChatMessageProps {
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

export default function ChatMessage({ content, role, timestamp }: ChatMessageProps) {
  return (
    <Box
      sx={{
        alignSelf: role === 'user' ? 'flex-start' : 'flex-end',
        maxWidth: '70%',
      }}
    >
      <Paper
        elevation={1}
        sx={{
          p: 2,
          bgcolor: role === 'user' ? 'primary.main' : 'grey.100',
          color: role === 'user' ? 'white' : 'text.primary',
          borderRadius: role === 'user' ? '20px 20px 20px 5px' : '20px 20px 5px 20px',
        }}
      >
        <Typography sx={{ 
          wordBreak: 'break-word',
          whiteSpace: 'pre-wrap'
        }}
        dangerouslySetInnerHTML={{
          __html: content.replace(/\n/g, '<br />')
        }}
        />
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 1,
            textAlign: role === 'user' ? 'left' : 'right',
            color: role === 'user' ? 'rgba(255,255,255,0.7)' : 'text.secondary',
          }}
        >
          {format(timestamp, 'a h:mm', { locale: ko })}
        </Typography>
      </Paper>
    </Box>
  );
} 