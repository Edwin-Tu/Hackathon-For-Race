// src/pages/api/v1/video/residents/[residentId]/history.ts
import type { NextApiRequest, NextApiResponse } from 'next';
import { QueryCommand } from '@aws-sdk/lib-dynamodb';
import { docClient, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, VideoHistoryResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<VideoHistoryResponse | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { residentId } = req.query;

    if (!residentId || typeof residentId !== 'string') {
      return res.status(400).json({ error: '缺少 residentId' });
    }

    // 使用 GSI 查詢該住民所有任務，按時間降序
    const result = await docClient.send(new QueryCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      IndexName: 'residentId-createdAt-index',
      KeyConditionExpression: 'residentId = :rid',
      ExpressionAttributeValues: {
        ':rid': residentId,
      },
      ScanIndexForward: false, // 降序（最新在前）
      Limit: 20,
    }));

    const tasks = (result.Items || []) as VideoTask[];

    return res.status(200).json({ tasks });
  } catch (error) {
    console.error('Get video history error:', error);
    return res.status(500).json({ error: '查詢歷史影片失敗' });
  }
}
