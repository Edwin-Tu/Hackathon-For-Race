import type { NextApiRequest, NextApiResponse } from 'next';
import { PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { PutCommand } from '@aws-sdk/lib-dynamodb';
import { v4 as uuidv4 } from 'uuid';
import { s3Client, docClient, AWS_CONFIG } from '@/utils/aws';
import type { PresignedUrlResponse, VideoTask } from '@/types/video';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<PresignedUrlResponse | { error: string }>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { residentId, filename } = req.body;

    if (!residentId || !filename) {
      return res.status(400).json({ error: '缺少必要參數' });
    }

    // 從 token 取得 familyMemberId（暫時用固定值，待整合驗證）
    const familyMemberId = 'family-001'; // TODO: 從 auth token 取得

    const taskId = uuidv4();
    const timestamp = Date.now();
    const imageKey = `images/${residentId}/${familyMemberId}/${timestamp}_${filename}`;

    // 產生 presigned URL
    const command = new PutObjectCommand({
      Bucket: AWS_CONFIG.imagesBucket,
      Key: imageKey,
      ContentType: 'image/jpeg',
    });
    const uploadUrl = await getSignedUrl(s3Client, command, { expiresIn: 300 });

    // 建立 DynamoDB 任務記錄（PENDING 狀態）
    const task: VideoTask = {
      taskId,
      residentId,
      familyMemberId,
      imageKey,
      status: 'PENDING',
      createdAt: timestamp,
      updatedAt: timestamp,
    };

    await docClient.send(new PutCommand({
      TableName: AWS_CONFIG.videoTasksTable,
      Item: task,
    }));

    return res.status(200).json({
      uploadUrl,
      imageKey,
      taskId,
    });
  } catch (error) {
    console.error('Presigned URL error:', error);
    return res.status(500).json({ error: '產生上傳連結失敗' });
  }
}
