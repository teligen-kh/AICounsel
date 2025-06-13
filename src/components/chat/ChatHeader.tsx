import { AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import { Menu as MenuIcon, Phone as PhoneIcon } from '@mui/icons-material';

export default function ChatHeader() {
  return (
    <AppBar position="static" color="primary" elevation={0}>
      <Toolbar>
        <IconButton edge="start" color="inherit" aria-label="menu">
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          AI 상담
        </Typography>
        <IconButton color="inherit" aria-label="voice-call">
          <PhoneIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
} 