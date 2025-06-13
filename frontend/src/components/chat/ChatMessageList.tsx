import { Box } from '@mui/material';
import ChatMessage from './ChatMessage';
import { useChatStore } from '@/store/useChatStore';

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

export default function ChatMessageList() {
  const messages = useChatStore((state) => state.messages);

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