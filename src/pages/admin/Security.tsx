'use client';
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  Chip,
  LinearProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import ShieldIcon from '@mui/icons-material/Shield';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';
import SecurityIcon from '@mui/icons-material/Security';
import BlockIcon from '@mui/icons-material/Block';
import BugReportIcon from '@mui/icons-material/BugReport';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';

// 攻擊類型統計
interface AttackStats {
  type: string;
  label: string;
  count: number;
  blocked: number;
  trend: 'up' | 'down' | 'stable';
}

// 風險趨勢數據
interface RiskTrendPoint {
  time: string;
  avgScore: number;
  highRiskCount: number;
}

// 洩漏偵測記錄
interface LeakageRecord {
  id: string;
  timestamp: Date;
  leakageType: string;
  assetType: string;
  action: 'BLOCKED' | 'REDACTED' | 'REWRITTEN';
  severity: 'critical' | 'high' | 'medium' | 'low';
}

// 模擬攻擊統計
const mockAttackStats: AttackStats[] = [
  { type: 'prompt_injection', label: '提示詞注入', count: 15, blocked: 15, trend: 'up' },
  { type: 'cross_resident_access', label: '跨住民存取', count: 8, blocked: 8, trend: 'down' },
  { type: 'secret_extraction', label: '機密提取', count: 12, blocked: 12, trend: 'stable' },
  { type: 'encoding_obfuscation', label: '編碼混淆', count: 5, blocked: 5, trend: 'up' },
  { type: 'role_impersonation', label: '角色偽裝', count: 3, blocked: 3, trend: 'down' },
  { type: 'tool_abuse', label: '工具濫用', count: 2, blocked: 2, trend: 'stable' },
];

// 模擬風險趨勢
const mockRiskTrend: RiskTrendPoint[] = [
  { time: '00:00', avgScore: 12, highRiskCount: 0 },
  { time: '04:00', avgScore: 8, highRiskCount: 0 },
  { time: '08:00', avgScore: 25, highRiskCount: 3 },
  { time: '12:00', avgScore: 45, highRiskCount: 8 },
  { time: '16:00', avgScore: 32, highRiskCount: 5 },
  { time: '20:00', avgScore: 18, highRiskCount: 2 },
];

// 模擬洩漏偵測記錄
const mockLeakageRecords: LeakageRecord[] = [
  {
    id: '1',
    timestamp: new Date('2026-08-01T14:30:00'),
    leakageType: '完全洩漏',
    assetType: 'System Prompt',
    action: 'BLOCKED',
    severity: 'critical',
  },
  {
    id: '2',
    timestamp: new Date('2026-08-01T12:15:00'),
    leakageType: '編碼洩漏',
    assetType: 'API Key',
    action: 'BLOCKED',
    severity: 'critical',
  },
  {
    id: '3',
    timestamp: new Date('2026-08-01T10:45:00'),
    leakageType: '部分洩漏',
    assetType: 'Database Info',
    action: 'REDACTED',
    severity: 'high',
  },
  {
    id: '4',
    timestamp: new Date('2026-08-01T09:20:00'),
    leakageType: '語意洩漏',
    assetType: 'Internal Rule',
    action: 'REWRITTEN',
    severity: 'medium',
  },
];

// 嚴重度配置
const severityConfig: Record<string, { label: string; color: 'error' | 'warning' | 'info' | 'success' }> = {
  critical: { label: '嚴重', color: 'error' },
  high: { label: '高', color: 'error' },
  medium: { label: '中', color: 'warning' },
  low: { label: '低', color: 'info' },
};

export default function Security() {
  const [timeRange, setTimeRange] = useState('24h');

  // 計算總體統計
  const totalAttacks = mockAttackStats.reduce((sum, s) => sum + s.count, 0);
  const totalBlocked = mockAttackStats.reduce((sum, s) => sum + s.blocked, 0);
  const blockRate = totalAttacks > 0 ? Math.round((totalBlocked / totalAttacks) * 100) : 0;
  const avgRiskScore = Math.round(mockRiskTrend.reduce((sum, p) => sum + p.avgScore, 0) / mockRiskTrend.length);

  return (
    <Container maxWidth="xl" sx={{ py: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ShieldIcon color="primary" />
          安全風險儀表板
        </Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>時間範圍</InputLabel>
          <Select value={timeRange} label="時間範圍" onChange={(e) => setTimeRange(e.target.value)}>
            <MenuItem value="1h">最近 1 小時</MenuItem>
            <MenuItem value="24h">最近 24 小時</MenuItem>
            <MenuItem value="7d">最近 7 天</MenuItem>
            <MenuItem value="30d">最近 30 天</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* 總體統計卡片 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    攻擊偵測
                  </Typography>
                  <Typography variant="h3">{totalAttacks}</Typography>
                </Box>
                <BugReportIcon color="error" sx={{ fontSize: 40 }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingUpIcon color="error" fontSize="small" />
                <Typography variant="caption" color="error">
                  較昨日 +12%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    成功阻擋
                  </Typography>
                  <Typography variant="h3">{totalBlocked}</Typography>
                </Box>
                <BlockIcon color="success" sx={{ fontSize: 40 }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <VerifiedUserIcon color="success" fontSize="small" />
                <Typography variant="caption" color="success.main">
                  阻擋率 {blockRate}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    平均風險分數
                  </Typography>
                  <Typography variant="h3">{avgRiskScore}</Typography>
                </Box>
                <SecurityIcon
                  sx={{
                    fontSize: 40,
                    color: avgRiskScore >= 50 ? 'error.main' : avgRiskScore >= 30 ? 'warning.main' : 'success.main',
                  }}
                />
              </Box>
              <LinearProgress
                variant="determinate"
                value={avgRiskScore}
                color={avgRiskScore >= 50 ? 'error' : avgRiskScore >= 30 ? 'warning' : 'success'}
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    洩漏偵測
                  </Typography>
                  <Typography variant="h3">{mockLeakageRecords.length}</Typography>
                </Box>
                <WarningAmberIcon color="warning" sx={{ fontSize: 40 }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <TrendingDownIcon color="success" fontSize="small" />
                <Typography variant="caption" color="success.main">
                  較昨日 -25%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* 攻擊類型統計 */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              攻擊類型分佈
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>攻擊類型</TableCell>
                  <TableCell align="right">偵測數</TableCell>
                  <TableCell align="right">阻擋數</TableCell>
                  <TableCell align="right">阻擋率</TableCell>
                  <TableCell>趨勢</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockAttackStats.map((stat) => (
                  <TableRow key={stat.type}>
                    <TableCell>{stat.label}</TableCell>
                    <TableCell align="right">{stat.count}</TableCell>
                    <TableCell align="right">{stat.blocked}</TableCell>
                    <TableCell align="right">
                      <Chip
                        size="small"
                        label={`${Math.round((stat.blocked / stat.count) * 100)}%`}
                        color={stat.blocked === stat.count ? 'success' : 'warning'}
                      />
                    </TableCell>
                    <TableCell>
                      {stat.trend === 'up' ? (
                        <TrendingUpIcon color="error" fontSize="small" />
                      ) : stat.trend === 'down' ? (
                        <TrendingDownIcon color="success" fontSize="small" />
                      ) : (
                        <Typography variant="caption" color="text.secondary">
                          —
                        </Typography>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* 風險分數趨勢 */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              風險分數趨勢
            </Typography>
            {/* 簡化的趨勢圖 */}
            <Box sx={{ display: 'flex', alignItems: 'flex-end', height: 200, gap: 1, mt: 2 }}>
              {mockRiskTrend.map((point, index) => (
                <Box
                  key={index}
                  sx={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                  }}
                >
                  <Box
                    sx={{
                      width: '100%',
                      height: `${point.avgScore * 2}px`,
                      bgcolor:
                        point.avgScore >= 50 ? 'error.main' : point.avgScore >= 30 ? 'warning.main' : 'success.main',
                      borderRadius: 1,
                      minHeight: 10,
                    }}
                  />
                  <Typography variant="caption" sx={{ mt: 1 }}>
                    {point.time}
                  </Typography>
                </Box>
              ))}
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, bgcolor: 'success.main', borderRadius: 0.5 }} />
                <Typography variant="caption">低風險 (&lt;30)</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, bgcolor: 'warning.main', borderRadius: 0.5 }} />
                <Typography variant="caption">中風險 (30-50)</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box sx={{ width: 12, height: 12, bgcolor: 'error.main', borderRadius: 0.5 }} />
                <Typography variant="caption">高風險 (&gt;50)</Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* 洩漏偵測記錄 */}
        <Grid size={{ xs: 12 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              洩漏偵測記錄
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>時間</TableCell>
                  <TableCell>洩漏類型</TableCell>
                  <TableCell>資產類型</TableCell>
                  <TableCell>嚴重度</TableCell>
                  <TableCell>處理動作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockLeakageRecords.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      {record.timestamp.toLocaleString('zh-TW', {
                        month: 'numeric',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </TableCell>
                    <TableCell>{record.leakageType}</TableCell>
                    <TableCell>{record.assetType}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={severityConfig[record.severity]?.label || record.severity}
                        color={severityConfig[record.severity]?.color || 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={record.action}
                        color={record.action === 'BLOCKED' ? 'error' : record.action === 'REDACTED' ? 'warning' : 'info'}
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}
