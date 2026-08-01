'use client';
import React, { useState } from 'react';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Paper,
  Divider,
  Chip,
  Avatar,
  Alert,
  IconButton,
  InputAdornment,
  Fade,
  Grow,
  CircularProgress,
  Backdrop,
  Collapse,
} from '@mui/material';
import { useTheme, alpha, keyframes } from '@mui/material/styles';
import { useRouter } from 'next/router';
import ShieldIcon from '@mui/icons-material/Shield';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import FamilyRestroomIcon from '@mui/icons-material/FamilyRestroom';
import RecordVoiceOverIcon from '@mui/icons-material/RecordVoiceOver';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LoginIcon from '@mui/icons-material/Login';
import SecurityIcon from '@mui/icons-material/Security';

// 動畫定義
const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
`;

const shimmer = keyframes`
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
`;

// 預設 Demo 帳號
interface DemoAccount {
  username: string;
  role: string;
  displayName: string;
  icon: React.ReactNode;
  color: 'error' | 'info' | 'success' | 'warning';
  description: string;
}

const demoAccounts: DemoAccount[] = [
  { 
    username: 'admin', 
    role: 'ADMIN', 
    displayName: '系統管理者', 
    icon: <AdminPanelSettingsIcon />, 
    color: 'error',
    description: '管理使用者、角色與系統設定',
  },
  { 
    username: 'caregiver', 
    role: 'CAREGIVER', 
    displayName: '照護人員', 
    icon: <LocalHospitalIcon />, 
    color: 'info',
    description: '照護住民、查看摘要與警示',
  },
  { 
    username: 'family', 
    role: 'FAMILY', 
    displayName: '家屬', 
    icon: <FamilyRestroomIcon />, 
    color: 'success',
    description: '查看住民狀況與通知',
  },
  { 
    username: 'resident', 
    role: 'RESIDENT', 
    displayName: '住民（語音互動）', 
    icon: <RecordVoiceOverIcon />, 
    color: 'warning',
    description: '直接進入語音互動介面',
  },
];

// 模擬住民 Persona 列表
const mockPersonas = [
  { id: 'p1', displayName: '王奶奶', status: 'active' },
  { id: 'p2', displayName: '李爺爺', status: 'active' },
];

export default function Login() {
  const theme = useTheme();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [expandedResident, setExpandedResident] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // 處理一般登入
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (!username || !password) {
      setError('請輸入帳號與密碼');
      return;
    }
    await performLogin(username);
  };

  // Base64 編碼（支援 Unicode）
  const encodeBase64 = (str: string) => {
    return btoa(unescape(encodeURIComponent(str)));
  };

  // 執行員工登入
  const performLogin = async (user: string) => {
    setLoading(true);
    try {
      // 模擬 API 延遲
      await new Promise((resolve) => setTimeout(resolve, 800));

      // 根據帳號判斷角色
      let role = 'CAREGIVER';
      if (user.toLowerCase().includes('admin')) {
        role = 'ADMIN';
      } else if (user.toLowerCase().includes('family')) {
        role = 'FAMILY';
      }

      // 模擬產生 JWT
      const mockPayload = {
        sub: user,
        role,
        displayName: demoAccounts.find((a) => a.username === user)?.displayName || user,
        exp: Date.now() + 3600000, // 1 小時後過期
        iat: Date.now(),
      };
      const mockToken =
        encodeBase64(JSON.stringify({ alg: 'HS256', typ: 'JWT' })) +
        '.' +
        encodeBase64(JSON.stringify(mockPayload)) +
        '.mock_signature';

      // 儲存 Token
      localStorage.setItem('auth', mockToken);
      document.cookie = `auth=${mockToken}; path=/; max-age=3600`;

      // 依角色導向
      if (role === 'ADMIN') {
        router.push('/admin/Users');
      } else if (role === 'FAMILY') {
        router.push('/family/Dashboard');
      } else {
        router.push('/caregiver');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('登入失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 執行住民登入
  const performResidentLogin = async (personaId: string) => {
    setLoading(true);
    try {
      await new Promise((resolve) => setTimeout(resolve, 800));

      const persona = mockPersonas.find((p) => p.id === personaId);
      const mockPayload = {
        sub: personaId,
        role: 'RESIDENT',
        displayName: persona?.displayName || personaId,
        personaId,
        exp: Date.now() + 3600000,
        iat: Date.now(),
      };
      const mockToken =
        encodeBase64(JSON.stringify({ alg: 'HS256', typ: 'JWT' })) +
        '.' +
        encodeBase64(JSON.stringify(mockPayload)) +
        '.mock_signature';

      localStorage.setItem('auth', mockToken);
      document.cookie = `auth=${mockToken}; path=/; max-age=3600`;

      // 住民直接導向語音互動頁面
      router.push('/resident/voice');
    } catch (err) {
      console.error('Resident login error:', err);
      setError('登入失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 快速登入（Demo 用）
  const handleQuickLogin = (account: DemoAccount) => {
    if (account.role === 'RESIDENT') {
      setExpandedResident(!expandedResident);
      return;
    }
    setUsername(account.username);
    performLogin(account.username);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        py: 4,
        position: 'relative',
        overflow: 'hidden',
        // 漸層背景
        background: theme.palette.mode === 'dark' 
          ? `linear-gradient(135deg, ${alpha(theme.palette.primary.dark, 0.3)} 0%, ${theme.palette.background.default} 50%, ${alpha(theme.palette.secondary.dark, 0.2)} 100%)`
          : `linear-gradient(135deg, ${alpha(theme.palette.primary.light, 0.15)} 0%, ${theme.palette.background.default} 50%, ${alpha(theme.palette.secondary.light, 0.1)} 100%)`,
      }}
    >
      {/* 背景裝飾 */}
      <Box
        sx={{
          position: 'absolute',
          top: '10%',
          left: '5%',
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: alpha(theme.palette.primary.main, 0.08),
          filter: 'blur(60px)',
          animation: `${pulse} 4s ease-in-out infinite`,
        }}
      />
      <Box
        sx={{
          position: 'absolute',
          bottom: '10%',
          right: '5%',
          width: 250,
          height: 250,
          borderRadius: '50%',
          background: alpha(theme.palette.secondary.main, 0.08),
          filter: 'blur(60px)',
          animation: `${pulse} 5s ease-in-out infinite 1s`,
        }}
      />

      {/* Loading Backdrop */}
      <Backdrop
        open={loading}
        sx={{
          zIndex: theme.zIndex.drawer + 1,
          bgcolor: alpha(theme.palette.background.default, 0.8),
          backdropFilter: 'blur(4px)',
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CircularProgress size={48} thickness={4} />
          <Typography variant="body1" sx={{ mt: 2, fontWeight: 500 }}>
            登入中...
          </Typography>
        </Box>
      </Backdrop>

      <Container maxWidth="sm" sx={{ position: 'relative', zIndex: 1 }}>
        <Grow in timeout={600}>
          <Paper 
            elevation={0}
            sx={{ 
              p: { xs: 3, sm: 5 },
              borderRadius: 4,
              border: `1px solid ${theme.palette.divider}`,
              boxShadow: theme.palette.mode === 'dark'
                ? '0 8px 32px rgba(0,0,0,0.4)'
                : '0 8px 32px rgba(0,0,0,0.08)',
              backdropFilter: 'blur(20px)',
              bgcolor: alpha(theme.palette.background.paper, 0.9),
            }}
          >
            {/* Logo 與標題 */}
            <Box sx={{ textAlign: 'center', mb: 4 }}>
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  mx: 'auto',
                  mb: 2.5,
                  bgcolor: theme.palette.primary.main,
                  boxShadow: `0 8px 24px ${alpha(theme.palette.primary.main, 0.4)}`,
                  animation: `${float} 3s ease-in-out infinite`,
                }}
              >
                <ShieldIcon sx={{ fontSize: 44 }} />
              </Avatar>
              <Typography 
                variant="h4" 
                gutterBottom
                sx={{
                  fontWeight: 700,
                  background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                  backgroundClip: 'text',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}
              >
                智護聲盾
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Smart Care Voice Agent with SecretGuard
              </Typography>
            </Box>

            {/* 錯誤提示 */}
            <Fade in={!!error}>
              <Box>
                {error && (
                  <Alert 
                    severity="error" 
                    sx={{ mb: 3 }} 
                    onClose={() => setError('')}
                    variant="filled"
                  >
                    {error}
                  </Alert>
                )}
              </Box>
            </Fade>

            {/* 登入表單 */}
            <Fade in timeout={300}>
              <Box component="form" onSubmit={handleSubmit}>
                  <TextField
                    label="帳號"
                    fullWidth
                    margin="normal"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    disabled={loading}
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <PersonIcon color="action" />
                          </InputAdornment>
                        ),
                      },
                    }}
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    label="密碼"
                    type={showPassword ? 'text' : 'password'}
                    fullWidth
                    margin="normal"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    slotProps={{
                      input: {
                        startAdornment: (
                          <InputAdornment position="start">
                            <LockIcon color="action" />
                          </InputAdornment>
                        ),
                        endAdornment: (
                          <InputAdornment position="end">
                            <IconButton 
                              onClick={() => setShowPassword(!showPassword)} 
                              edge="end"
                              disabled={loading}
                            >
                              {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                            </IconButton>
                          </InputAdornment>
                        ),
                      },
                    }}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    size="large"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <LoginIcon />}
                    sx={{ 
                      mt: 4, 
                      mb: 2,
                      py: 1.5,
                      fontSize: '1rem',
                      fontWeight: 600,
                      boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.4)}`,
                      '&:hover': {
                        boxShadow: `0 6px 20px ${alpha(theme.palette.primary.main, 0.5)}`,
                      },
                    }}
                  >
                    {loading ? '登入中...' : '登入'}
                  </Button>

                  {/* 快速登入區 */}
                  <Divider sx={{ my: 4 }}>
                    <Chip 
                      label="Demo 快速登入" 
                      size="small"
                      icon={<SecurityIcon sx={{ fontSize: 16 }} />}
                      sx={{ 
                        px: 1,
                        fontWeight: 500,
                      }}
                    />
                  </Divider>

                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                    {demoAccounts.map((account, index) => (
                      <React.Fragment key={account.username}>
                        <Grow in timeout={400 + index * 100}>
                          <Paper
                            variant="outlined"
                            sx={{
                              p: 2,
                              cursor: loading ? 'not-allowed' : 'pointer',
                              transition: 'all 0.2s ease',
                              opacity: loading ? 0.6 : 1,
                              '&:hover': loading ? {} : {
                                borderColor: theme.palette[account.color].main,
                                bgcolor: alpha(theme.palette[account.color].main, 0.04),
                                transform: 'translateX(4px)',
                              },
                            }}
                            onClick={() => !loading && handleQuickLogin(account)}
                          >
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                              <Avatar 
                                sx={{ 
                                  bgcolor: alpha(theme.palette[account.color].main, 0.15),
                                  color: theme.palette[account.color].main,
                                }}
                              >
                                {account.icon}
                              </Avatar>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                                  {account.displayName}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {account.description}
                                </Typography>
                              </Box>
                              <Chip
                                size="small"
                                label={account.username}
                                color={account.color}
                                variant="outlined"
                              />
                            </Box>
                          </Paper>
                        </Grow>
                        
                        {/* 住民 Persona 選擇展開區 */}
                        {account.role === 'RESIDENT' && (
                          <Collapse in={expandedResident}>
                            <Box sx={{ pl: 4, pt: 1, pb: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                              {mockPersonas.map((persona) => (
                                <Chip
                                  key={persona.id}
                                  label={persona.displayName}
                                  onClick={() => !loading && performResidentLogin(persona.id)}
                                  color="warning"
                                  variant="outlined"
                                  sx={{ 
                                    cursor: loading ? 'not-allowed' : 'pointer',
                                    '&:hover': { bgcolor: alpha(theme.palette.warning.main, 0.1) },
                                  }}
                                />
                              ))}
                            </Box>
                          </Collapse>
                        )}
                      </React.Fragment>
                    ))}
                  </Box>
                </Box>
              </Fade>
          </Paper>
        </Grow>

        {/* 版權資訊 */}
        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ mt: 4, textAlign: 'center', display: 'block' }}
        >
          404 Not Sleep Team © 2026 | 黑客松提案展示系統
        </Typography>
      </Container>
    </Box>
  );
}
