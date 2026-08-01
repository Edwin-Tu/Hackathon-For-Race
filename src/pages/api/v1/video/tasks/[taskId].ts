import type { NextApiRequest, NextApiResponse } from 'next';
import { GetCommand, DeleteCommand } from '@aws-sdk/lib-dynamodb';
import { DeleteObjectCommand } from '@aws-sdk/client-s3';
import { docClient, s3Client, AWS_CONFIG } from '@/utils/aws';
import type { VideoTask, TaskStatusResponse } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<TaskStatusResponse | { success: boolean } | { error: string }>
) {
  const { taskId } = req.query;

  if (!taskId || typeof taskId !== 'string') {
    return res.status(400).json({ error: '缺少 taskId' });
  }

  if (req.method === 'GET') {
    return handleGet(taskId, res);
  } else if (req.method === 'DELETE') {
    return handleDelete(taskId, res);
  } else {
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleGet(
  taskId: string,
  res: NextApiResponse<TaskStatusResponse | { error: string }>
) {
  try {
    const result = await docClient.send(new GetCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Key: { taskId },
    }));

    if (!result.Item) {
      return res.status(404).json({ error: '找不到任務' });
    }

    const task = result.Item as VideoTask;

    const response: TaskStatusResponse = {
      taskId: task.taskId,
      status: task.status,
    };
    if (task.videoUrl !== undefined) {
      response.videoUrl = task.videoUrl;
    }
    if (task.errorMessage !== undefined) {
      response.errorMessage = task.errorMessage;
    }
    return res.status(200).json(response);
  } catch (error) {
    console.error('Get task status error:', error);
    return res.status(500).json({ error: '查詢任務狀態失敗' });
  }
}

async function handleDelete(
  taskId: string,
  res: NextApiResponse<{ success: boolean } | { error: string }>
) {
  try {
    // 先取得任務資訊以獲取 S3 key
    const result = await docClient.send(new GetCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Key: { taskId },
    }));

    if (!result.Item) {
      return res.status(404).json({ error: '找不到任務' });
    }

    const task = result.Item as VideoTask;

    // 刪除 S3 上的影片（如果存在）
    if (task.videoKey) {
      try {
        await s3Client.send(new DeleteObjectCommand({
          Bucket: AWS_CONFIG.videosBucket,
          Key: task.videoKey,
        }));
      } catch (s3Error) {
        console.error('Delete S3 object error:', s3Error);
        // 繼續刪除 DynamoDB 記錄
      }
    }

    // 刪除 S3 上的原始圖片（如果存在）
    if (task.imageKey) {
      try {
        await s3Client.send(new DeleteObjectCommand({
          Bucket: AWS_CONFIG.imagesBucket,
          Key: task.imageKey,
        }));
      } catch (s3Error) {
        console.error('Delete S3 image error:', s3Error);
      }
    }

    // 刪除 DynamoDB 記錄
    await docClient.send(new DeleteCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Key: { taskId },
    }));

    return res.status(200).json({ success: true });
  } catch (error) {
    console.error('Delete task error:', error);
    return res.status(500).json({ error: '刪除任務失敗' });
  }
}
