import { Box, Paper } from '@mui/material';
import ChatHeader from './ChatHeader';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';

export default function ChatContainer() {
  return (
    <Paper
      elevation={3}
      sx={{
        height: '100vh',
        maxHeight: 'calc(100vh - 64px)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      <ChatHeader />
      <ChatMessageList />
      <ChatInput />
    </Paper>
  );
} 