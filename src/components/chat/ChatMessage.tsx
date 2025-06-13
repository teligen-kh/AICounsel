import { Box, Paper, Typography } from '@mui/material';
import { Message } from './ChatMessageList';

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isAI = message.sender === 'ai';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isAI ? 'flex-start' : 'flex-end',
        alignItems: 'flex-end',
        gap: 1,
      }}
    >
      <Paper
        sx={{
          maxWidth: '70%',
          padding: 1.5,
          bgcolor: isAI ? 'grey.100' : 'primary.main',
          color: isAI ? 'text.primary' : 'white',
          borderRadius: 2,
          ...(isAI
            ? { borderTopLeftRadius: 0 }
            : { borderTopRightRadius: 0 }),
        }}
      >
        <Typography variant="body1">{message.text}</Typography>
      </Paper>
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ minWidth: '4rem' }}
      >
        {new Date(message.timestamp).toLocaleTimeString('ko-KR', {
          hour: '2-digit',
          minute: '2-digit',
        })}
      </Typography>
    </Box>
  );
} 