import type { NextApiRequest, NextApiResponse } from 'next';
import { QueryCommand } from '@aws-sdk/lib-dynamodb';
import { docClient, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, LatestVideoResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<LatestVideoResponse | null | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { residentId } = req.query;

    if (!residentId || typeof residentId !== 'string') {
      return res.status(400).json({ error: '缺少 residentId' });
    }

    // 使用 GSI 查詢該住民最新的已完成任務
    const result = await docClient.send(new QueryCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      IndexName: 'residentId-createdAt-index',
      KeyConditionExpression: 'residentId = :rid',
      FilterExpression: '#status = :status',
      ExpressionAttributeNames: {
        '#status': 'status',
      },
      ExpressionAttributeValues: {
        ':rid': residentId,
        ':status': 'COMPLETED',
      },
      ScanIndexForward: false, // 降序排列，最新的在前
      Limit: 1,
    }));

    if (!result.Items || result.Items.length === 0) {
      return res.status(200).json(null);
    }

    const task = result.Items[0] as VideoTask;

    return res.status(200).json({
      videoUrl: task.videoUrl!,
      createdAt: task.createdAt,
    });
  } catch (error) {
    console.error('Get latest video error:', error);
    return res.status(500).json({ error: '查詢最新影片失敗' });
  }
}
