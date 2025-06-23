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
        justifyContent: isAI ? 'flex-end' : 'flex-start',
        alignItems: 'flex-end',
        gap: 1,
      }}
    >
      <Paper
        sx={{
          maxWidth: '70%',
          padding: 1.5,
          bgcolor: isAI ? 'primary.main' : 'grey.100',
          color: isAI ? 'white' : 'text.primary',
          borderRadius: 2,
          ...(isAI
            ? { borderTopRightRadius: 0 }
            : { borderTopLeftRadius: 0 }),
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