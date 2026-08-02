import type { NextApiRequest, NextApiResponse } from 'next';

// 模擬住民資料
const mockResidents = [
  { id: '1', name: '王奶奶', age: 78, room: '101' },
  { id: '2', name: '李爺爺', age: 82, room: '102' },
  { id: '3', name: '張阿姨', age: 75, room: '103' },
];

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    res.status(200).json(mockResidents);
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}
