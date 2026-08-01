import type { NextApiRequest, NextApiResponse } from 'next';
import { GetCommand } from '@aws-sdk/lib-dynamodb';
import { docClient, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, TaskStatusResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<TaskStatusResponse | { error: string }>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { taskId } = req.query;

    if (!taskId || typeof taskId !== 'string') {
      return res.status(400).json({ error: '缺少 taskId' });
    }

    const result = await docClient.send(new GetCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Key: { taskId },
    }));

    if (!result.Item) {
      return res.status(404).json({ error: '找不到任務' });
    }

    const task = result.Item as VideoTask;

    return res.status(200).json({
      taskId: task.taskId,
      status: task.status,
      videoUrl: task.videoUrl,
      errorMessage: task.errorMessage,
    });
  } catch (error) {
    console.error('Get task status error:', error);
    return res.status(500).json({ error: '查詢任務狀態失敗' });
  }
}
