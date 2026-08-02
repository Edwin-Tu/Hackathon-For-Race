'use client';
import React, { useState } from 'react';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Paper,
  Avatar,
  Alert,
  IconButton,
  InputAdornment,
  Fade,
  Grow,
  CircularProgress,
  Backdrop,
} from '@mui/material';
import { useTheme, alpha, keyframes } from '@mui/material/styles';
import { useRouter } from 'next/router';
import ShieldIcon from '@mui/icons-material/Shield';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import LoginIcon from '@mui/icons-material/Login';

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

// 帳號資料庫
interface AccountData {
  username: string;
  password: string;
  role: string;
  displayName: string;
}

const validAccounts: AccountData[] = [
  { 
    username: 'admin', 
    password: 'admin123',
    role: 'ADMIN', 
    displayName: '系統管理者',
  },
  { 
    username: 'family', 
    password: 'family123',
    role: 'FAMILY', 
    displayName: '家屬',
  },
  { 
    username: 'elder-care', 
    password: 'eldercare123',
    role: 'CAREGIVER', 
    displayName: '長照機構',
  },
  { 
    username: 'elder', 
    password: 'elder123',
    role: 'RESIDENT', 
    displayName: '長者',
  },
];

export default function Login() {
  const theme = useTheme();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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

    // 驗證帳號密碼
    const account = validAccounts.find(
      acc => acc.username === username && acc.password === password
    );

    if (!account) {
      setError('帳號或密碼錯誤');
      return;
    }

    await performLogin(account);
  };

  // Base64 編碼（支援 Unicode）
  const encodeBase64 = (str: string) => {
    return btoa(unescape(encodeURIComponent(str)));
  };

  // 執行登入
  const performLogin = async (account: AccountData) => {
    setLoading(true);
    try {
      // 模擬 API 延遲
      await new Promise((resolve) => setTimeout(resolve, 800));

      // 模擬產生 JWT
      const mockPayload = {
        sub: account.username,
        role: account.role,
        displayName: account.displayName,
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
      if (account.role === 'ADMIN') {
        router.push('/admin/Users');
      } else if (account.role === 'FAMILY') {
        router.push('/family/Dashboard');
      } else if (account.role === 'RESIDENT') {
        router.push('/resident/voice');
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

                  {/* 測試帳號提示 */}
                  <Box sx={{ mt: 3, p: 2, bgcolor: alpha(theme.palette.info.main, 0.05), borderRadius: 2, border: `1px solid ${alpha(theme.palette.info.main, 0.2)}` }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1, fontWeight: 600 }}>
                      測試帳號：
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', fontFamily: 'monospace', lineHeight: 1.8 }}>
                      admin / admin123 (系統管理者)<br />
                      family / family123 (家屬)<br />
                      elder-care / eldercare123 (長照機構)<br />
                      elder / elder123 (長者)
                    </Typography>
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
