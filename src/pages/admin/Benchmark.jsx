import React from 'react';
import { Typography, Table, TableHead, TableRow, TableCell, TableBody } from '@mui/material';

// 假資料示範
const mockReport = [
  { test: 'F09 攻擊分類', result: '通過', time: '120ms' },
  { test: 'F10 風險評分', result: '通過', time: '95ms' },
  { test: '輸出守衛', result: '失敗', time: '30ms' },
];

export default function Benchmark() {
  return (
    <>
      <Typography variant="h5" gutterBottom>基準測試報告</Typography>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>測試項目</TableCell>
            <TableCell>結果</TableCell>
            <TableCell>耗時</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {mockReport.map((r, i) => (
            <TableRow key={i}>
              <TableCell>{r.test}</TableCell>
              <TableCell>{r.result}</TableCell>
              <TableCell>{r.time}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
}
