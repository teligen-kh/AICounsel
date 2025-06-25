import React from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';

export default function LoadingMessage() {
  return (
    <Box
      sx={{
        alignSelf: 'flex-end',
        maxWidth: '70%',
        display: 'flex',
        alignItems: 'center',
        gap: 1,
        p: 2,
        bgcolor: 'grey.100',
        borderRadius: '20px 20px 5px 20px',
      }}
    >
      <CircularProgress size={16} />
      <Typography variant="body2" color="text.secondary">
        답변을 생성하고 있습니다...
      </Typography>
    </Box>
  );
} 