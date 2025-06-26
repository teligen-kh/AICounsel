import { Paper, Typography, Box } from '@mui/material';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import React, { useEffect, useRef } from 'react';
import { Message } from './ChatMessageList';

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const { text, sender, timestamp } = message;
  const textRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    // MutationObserver를 사용하여 DOM 변경 감지
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          const paragraphs = document.querySelectorAll('p.MuiTypography-root');
          paragraphs.forEach((p) => {
            if (p.textContent && p.textContent.includes('알파넷')) {
              p.style.setProperty('white-space', 'pre-wrap', 'important');
            }
          });
        }
      });
    });

    // DOM 감시 시작
    if (textRef.current) {
      observer.observe(textRef.current, {
        childList: true,
        subtree: true
      });
    }

    // 초기 스타일 적용
    setTimeout(() => {
      const paragraphs = document.querySelectorAll('p.MuiTypography-root');
      paragraphs.forEach((p) => {
        if (p.textContent && p.textContent.includes('알파넷')) {
          p.style.setProperty('white-space', 'pre-wrap', 'important');
        }
      });
    }, 100);

    // 클린업
    return () => {
      observer.disconnect();
    };
  }, [text]);
  
  return (
    <Box
      sx={{
        alignSelf: sender === 'user' ? 'flex-start' : 'flex-end',
        maxWidth: '70%',
      }}
    >
      <Paper
        elevation={1}
        sx={{
          p: 2,
          bgcolor: sender === 'user' ? 'primary.main' : 'grey.100',
          color: sender === 'user' ? 'white' : 'text.primary',
          borderRadius: sender === 'user' ? '20px 20px 20px 5px' : '20px 20px 5px 20px',
        }}
      >
        <Typography
          ref={textRef}
          component="div"
          sx={{ 
            wordBreak: 'break-word',
            fontFamily: 'inherit',
            fontSize: 'inherit',
            lineHeight: 'inherit',
            color: 'inherit'
          }}
        >
          {text}
        </Typography>
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            mt: 1,
            textAlign: sender === 'user' ? 'left' : 'right',
            color: sender === 'user' ? 'rgba(255,255,255,0.7)' : 'text.secondary',
          }}
        >
          {format(timestamp, 'a h:mm', { locale: ko })}
        </Typography>
      </Paper>
    </Box>
  );
}