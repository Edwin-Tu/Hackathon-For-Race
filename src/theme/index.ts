import { createTheme, alpha, ThemeOptions } from '@mui/material/styles';

// 品牌配色
const brandColors = {
  // 主色：專業藍綠色 - 傳達信任、照護、科技感
  primary: {
    light: '#5DADE2',
    main: '#2E86AB',
    dark: '#1A5276',
    contrastText: '#FFFFFF',
  },
  // 次要色：溫暖橙色 - 傳達溫馨、親和
  secondary: {
    light: '#FAD7A0',
    main: '#E67E22',
    dark: '#CA6F1E',
    contrastText: '#FFFFFF',
  },
  // 功能色
  success: {
    light: '#82E0AA',
    main: '#27AE60',
    dark: '#1E8449',
    contrastText: '#FFFFFF',
  },
  warning: {
    light: '#F9E79F',
    main: '#F39C12',
    dark: '#D68910',
    contrastText: '#000000',
  },
  error: {
    light: '#F5B7B1',
    main: '#E74C3C',
    dark: '#C0392B',
    contrastText: '#FFFFFF',
  },
  info: {
    light: '#AED6F1',
    main: '#3498DB',
    dark: '#2471A3',
    contrastText: '#FFFFFF',
  },
};

// 共用主題設定
const baseThemeOptions: ThemeOptions = {
  typography: {
    fontFamily: [
      '"Noto Sans TC"',
      '"Roboto"',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontSize: '2.5rem',
      fontWeight: 700,
      letterSpacing: '-0.02em',
      lineHeight: 1.2,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 700,
      letterSpacing: '-0.01em',
      lineHeight: 1.3,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
      lineHeight: 1.3,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
      lineHeight: 1.4,
    },
    h6: {
      fontSize: '1.125rem',
      fontWeight: 600,
      lineHeight: 1.5,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
      lineHeight: 1.5,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.5,
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        '*': {
          boxSizing: 'border-box',
        },
        html: {
          scrollBehavior: 'smooth',
        },
        body: {
          scrollbarWidth: 'thin',
        },
        '::-webkit-scrollbar': {
          width: '8px',
          height: '8px',
        },
        '::-webkit-scrollbar-thumb': {
          borderRadius: '4px',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '10px 20px',
          fontSize: '0.9375rem',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        contained: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
          '&:hover': {
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
          },
        },
        outlined: {
          borderWidth: 2,
          '&:hover': {
            borderWidth: 2,
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'scale(1.05)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          transition: 'box-shadow 0.3s ease-in-out',
        },
        elevation1: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        },
        elevation2: {
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        },
        elevation3: {
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.12)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
          transition: 'all 0.2s ease',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            transition: 'box-shadow 0.2s ease',
            '&:hover': {
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
            },
            '&.Mui-focused': {
              boxShadow: '0 0 0 3px rgba(46, 134, 171, 0.2)',
            },
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 20,
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.2)',
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          transition: 'transform 0.2s ease',
          '&:hover': {
            transform: 'scale(1.08)',
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          margin: '4px 8px',
          transition: 'all 0.2s ease',
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 8,
          fontSize: '0.8125rem',
          padding: '8px 12px',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
        standardSuccess: {
          backgroundColor: alpha(brandColors.success.main, 0.1),
          '& .MuiAlert-icon': {
            color: brandColors.success.main,
          },
        },
        standardError: {
          backgroundColor: alpha(brandColors.error.main, 0.1),
          '& .MuiAlert-icon': {
            color: brandColors.error.main,
          },
        },
        standardWarning: {
          backgroundColor: alpha(brandColors.warning.main, 0.1),
          '& .MuiAlert-icon': {
            color: brandColors.warning.main,
          },
        },
        standardInfo: {
          backgroundColor: alpha(brandColors.info.main, 0.1),
          '& .MuiAlert-icon': {
            color: brandColors.info.main,
          },
        },
      },
    },
    MuiSnackbar: {
      styleOverrides: {
        root: {
          '& .MuiAlert-root': {
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
          },
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            fontWeight: 600,
            fontSize: '0.875rem',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          transition: 'background-color 0.2s ease',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          borderRight: 'none',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
        },
      },
    },
  },
};

// 淺色主題
export const lightTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: 'light',
    ...brandColors,
    background: {
      default: '#F8FAFC',
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A202C',
      secondary: '#64748B',
    },
    divider: 'rgba(0, 0, 0, 0.08)',
  },
  components: {
    ...baseThemeOptions.components,
    MuiCssBaseline: {
      styleOverrides: {
        ...baseThemeOptions.components?.MuiCssBaseline?.styleOverrides,
        '::-webkit-scrollbar-track': {
          background: '#F1F5F9',
        },
        '::-webkit-scrollbar-thumb': {
          background: '#CBD5E1',
          '&:hover': {
            background: '#94A3B8',
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%)',
          borderRight: 'none',
          boxShadow: '2px 0 12px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: `linear-gradient(135deg, ${brandColors.primary.main} 0%, ${brandColors.primary.dark} 100%)`,
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.1)',
        },
      },
    },
  },
});

// 深色主題
export const darkTheme = createTheme({
  ...baseThemeOptions,
  palette: {
    mode: 'dark',
    primary: {
      light: '#7DD3FC',
      main: '#38BDF8',
      dark: '#0EA5E9',
      contrastText: '#0F172A',
    },
    secondary: {
      light: '#FED7AA',
      main: '#FB923C',
      dark: '#EA580C',
      contrastText: '#0F172A',
    },
    success: {
      light: '#86EFAC',
      main: '#4ADE80',
      dark: '#22C55E',
      contrastText: '#0F172A',
    },
    warning: {
      light: '#FDE68A',
      main: '#FBBF24',
      dark: '#F59E0B',
      contrastText: '#0F172A',
    },
    error: {
      light: '#FCA5A5',
      main: '#F87171',
      dark: '#EF4444',
      contrastText: '#FFFFFF',
    },
    info: {
      light: '#93C5FD',
      main: '#60A5FA',
      dark: '#3B82F6',
      contrastText: '#0F172A',
    },
    background: {
      default: '#0F172A',
      paper: '#1E293B',
    },
    text: {
      primary: '#F1F5F9',
      secondary: '#94A3B8',
    },
    divider: 'rgba(255, 255, 255, 0.08)',
  },
  components: {
    ...baseThemeOptions.components,
    MuiCssBaseline: {
      styleOverrides: {
        ...baseThemeOptions.components?.MuiCssBaseline?.styleOverrides,
        '::-webkit-scrollbar-track': {
          background: '#1E293B',
        },
        '::-webkit-scrollbar-thumb': {
          background: '#475569',
          '&:hover': {
            background: '#64748B',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
        },
        elevation2: {
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.35)',
        },
        elevation3: {
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.4)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.25)',
          backgroundImage: 'none',
          border: '1px solid rgba(255, 255, 255, 0.05)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.35)',
          },
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          background: 'linear-gradient(180deg, #1E293B 0%, #0F172A 100%)',
          borderRight: '1px solid rgba(255, 255, 255, 0.05)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #1E293B 0%, #0F172A 100%)',
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.3)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&.Mui-focused': {
              boxShadow: '0 0 0 3px rgba(56, 189, 248, 0.25)',
            },
          },
        },
      },
    },
  },
});
