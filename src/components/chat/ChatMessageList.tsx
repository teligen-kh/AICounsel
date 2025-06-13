import { Box } from '@mui/material';
import ChatMessage from './ChatMessage';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

export default function ChatMessageList() {
  // 임시 메시지 데이터
  const messages: Message[] = [
    {
      id: '1',
      text: '안녕하세요! 무엇을 도와드릴까요?',
      sender: 'ai',
      timestamp: new Date(),
    },
  ];

  return (
    <Box
      sx={{
        flex: 1,
        overflow: 'auto',
        padding: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
    </Box>
  );
} 