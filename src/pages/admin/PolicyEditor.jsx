import React, { useState } from 'react';
import { TextField, Button, Box, Typography } from '@mui/material';

export default function PolicyEditor() {
  const [policy, setPolicy] = useState('{\n  \\"rules\\": []\n}');
  const handleSave = () => {
    // 這裡應該呼叫後端更新政策
    console.log('Saving policy', policy);
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Typography variant="h5" gutterBottom>政策編輯器</Typography>
      <TextField
        multiline
        rows={20}
        fullWidth
        value={policy}
        onChange={(e) => setPolicy(e.target.value)}
        variant="outlined"
      />
      <Button variant="contained" sx={{ mt: 2 }} onClick={handleSave}>儲存</Button>
    </Box>
  );
}
