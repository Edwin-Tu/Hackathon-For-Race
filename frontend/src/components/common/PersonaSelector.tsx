'use client';
import React, { useState } from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Avatar,
  Typography,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  ListItemAvatar,
  ListItemText,
  Paper,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

// Persona 類型
export interface Persona {
  id: string;
  displayName: string;
  avatar?: string;
  status: 'active' | 'inactive';
  lastInteractionAt?: Date;
}

interface PersonaSelectorProps {
  personas: Persona[];
  selectedPersonaId: string;
  onSelect: (personaId: string) => void;
  showConfirmDialog?: boolean;
  variant?: 'select' | 'inline' | 'compact';
}

/**
 * Persona 選擇器
 * 用於在語音互動前選擇住民，或在照護者介面切換住民
 */
export default function PersonaSelector({
  personas,
  selectedPersonaId,
  onSelect,
  showConfirmDialog = true,
  variant = 'select',
}: PersonaSelectorProps) {
  const [dialogOpen, setDialogOpen] = useState(false);
  const [pendingPersonaId, setPendingPersonaId] = useState<string | null>(null);

  const currentPersona = personas.find((p) => p.id === selectedPersonaId);

  // 處理選擇
  const handleSelect = (personaId: string) => {
    if (personaId === selectedPersonaId) return;

    if (showConfirmDialog) {
      setPendingPersonaId(personaId);
      setDialogOpen(true);
    } else {
      onSelect(personaId);
    }
  };

  // 確認切換
  const handleConfirm = () => {
    if (pendingPersonaId) {
      onSelect(pendingPersonaId);
    }
    setDialogOpen(false);
    setPendingPersonaId(null);
  };

  // 取消切換
  const handleCancel = () => {
    setDialogOpen(false);
    setPendingPersonaId(null);
  };

  // 下拉選單樣式
  if (variant === 'select') {
    return (
      <>
        <FormControl fullWidth>
          <InputLabel>選擇住民</InputLabel>
          <Select
            value={selectedPersonaId}
            label="選擇住民"
            onChange={(e) => handleSelect(e.target.value)}
            renderValue={(value) => {
              const persona = personas.find((p) => p.id === value);
              return (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Avatar sx={{ width: 24, height: 24, fontSize: 12 }}>
                    {persona?.displayName[0] || <PersonIcon />}
                  </Avatar>
                  <Typography>{persona?.displayName}</Typography>
                </Box>
              );
            }}
          >
            {personas.map((persona) => (
              <MenuItem key={persona.id} value={persona.id}>
                <ListItemAvatar>
                  <Avatar sx={{ width: 32, height: 32, mr: 1 }}>
                    {persona.displayName[0]}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={persona.displayName}
                  secondary={
                    persona.lastInteractionAt
                      ? `最後互動：${persona.lastInteractionAt.toLocaleDateString('zh-TW')}`
                      : '尚無互動紀錄'
                  }
                />
                <Chip
                  size="small"
                  label={persona.status === 'active' ? '活躍' : '非活躍'}
                  color={persona.status === 'active' ? 'success' : 'default'}
                  sx={{ ml: 1 }}
                />
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* 切換確認對話框 */}
        <PersonaSwitchDialog
          open={dialogOpen}
          currentPersona={currentPersona ?? undefined}
          targetPersona={personas.find((p) => p.id === pendingPersonaId) ?? undefined}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      </>
    );
  }

  // 內嵌卡片樣式
  if (variant === 'inline') {
    return (
      <>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ width: 48, height: 48 }}>
                {currentPersona?.displayName[0] || <PersonIcon />}
              </Avatar>
              <Box>
                <Typography variant="h6">{currentPersona?.displayName || '請選擇住民'}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {currentPersona?.lastInteractionAt
                    ? `最後互動：${currentPersona.lastInteractionAt.toLocaleString('zh-TW')}`
                    : '尚無互動紀錄'}
                </Typography>
              </Box>
            </Box>
            <Button
              variant="outlined"
              startIcon={<SwapHorizIcon />}
              onClick={() => setDialogOpen(true)}
            >
              切換住民
            </Button>
          </Box>
        </Paper>

        {/* 切換對話框 */}
        <Dialog open={dialogOpen} onClose={handleCancel} maxWidth="xs" fullWidth>
          <DialogTitle>選擇住民 (Persona)</DialogTitle>
          <DialogContent>
            <Alert severity="info" sx={{ mb: 2 }}>
              切換住民將載入該住民的記憶與偏好設定
            </Alert>
            <FormControl fullWidth>
              <InputLabel>住民</InputLabel>
              <Select
                value={pendingPersonaId || selectedPersonaId}
                label="住民"
                onChange={(e) => setPendingPersonaId(e.target.value)}
              >
                {personas.map((persona) => (
                  <MenuItem key={persona.id} value={persona.id}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                      <Avatar sx={{ width: 28, height: 28, fontSize: 14 }}>
                        {persona.displayName[0]}
                      </Avatar>
                      <Typography sx={{ flex: 1 }}>{persona.displayName}</Typography>
                      <Chip
                        size="small"
                        label={persona.status === 'active' ? '活躍' : '非活躍'}
                        color={persona.status === 'active' ? 'success' : 'default'}
                      />
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCancel}>取消</Button>
            <Button
              variant="contained"
              onClick={handleConfirm}
              disabled={!pendingPersonaId || pendingPersonaId === selectedPersonaId}
            >
              確認切換
            </Button>
          </DialogActions>
        </Dialog>
      </>
    );
  }

  // 緊湊樣式（用於 AppBar）
  return (
    <>
      <Chip
        avatar={
          <Avatar sx={{ width: 24, height: 24 }}>
            {currentPersona?.displayName[0] || <PersonIcon />}
          </Avatar>
        }
        label={currentPersona?.displayName || '選擇住民'}
        onClick={() => setDialogOpen(true)}
        sx={{ cursor: 'pointer' }}
      />

      <PersonaSwitchDialog
        open={dialogOpen}
        personas={personas}
        currentPersona={currentPersona ?? undefined}
        targetPersona={undefined}
        selectedPersonaId={selectedPersonaId}
        onSelect={handleSelect}
        onClose={handleCancel}
      />
    </>
  );
}

// 切換確認對話框元件
interface PersonaSwitchDialogProps {
  open: boolean;
  currentPersona: Persona | undefined;
  targetPersona: Persona | undefined;
  personas?: Persona[];
  selectedPersonaId?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  onSelect?: (personaId: string) => void;
  onClose?: () => void;
}

function PersonaSwitchDialog({
  open,
  currentPersona,
  targetPersona,
  personas,
  selectedPersonaId,
  onConfirm,
  onCancel,
  onSelect,
  onClose,
}: PersonaSwitchDialogProps) {
  const [selected, setSelected] = useState(selectedPersonaId || '');

  // 簡單確認模式（已選定目標）
  if (targetPersona && onConfirm && onCancel) {
    return (
      <Dialog open={open} onClose={onCancel}>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <WarningAmberIcon color="warning" />
          確認切換住民
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            切換住民將結束目前的對話 Session，並清除前一位住民的上下文，避免資訊殘留。
          </Alert>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 2, py: 2 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ width: 48, height: 48, mx: 'auto', mb: 1 }}>
                {currentPersona?.displayName[0]}
              </Avatar>
              <Typography variant="body2">{currentPersona?.displayName}</Typography>
            </Box>
            <SwapHorizIcon color="action" sx={{ fontSize: 32 }} />
            <Box sx={{ textAlign: 'center' }}>
              <Avatar sx={{ width: 48, height: 48, mx: 'auto', mb: 1, bgcolor: 'primary.main' }}>
                {targetPersona?.displayName[0]}
              </Avatar>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                {targetPersona?.displayName}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCancel}>取消</Button>
          <Button variant="contained" onClick={onConfirm}>
            確認切換
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  // 選擇模式
  if (personas && onSelect && onClose) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
        <DialogTitle>選擇住民</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 1 }}>
            <InputLabel>住民</InputLabel>
            <Select value={selected} label="住民" onChange={(e) => setSelected(e.target.value)}>
              {personas.map((persona) => (
                <MenuItem key={persona.id} value={persona.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Avatar sx={{ width: 28, height: 28 }}>{persona.displayName[0]}</Avatar>
                    <Typography>{persona.displayName}</Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>取消</Button>
          <Button
            variant="contained"
            onClick={() => {
              onSelect(selected);
              onClose();
            }}
            disabled={!selected}
          >
            確認
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  return null;
}
