import { S3Client, GetObjectCommand, PutObjectCommand } from '@aws-sdk/client-s3';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, UpdateCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';
import { BedrockRuntimeClient, GetAsyncInvokeCommand, StartAsyncInvokeCommand } from '@aws-sdk/client-bedrock-runtime';

const s3Client = new S3Client();
const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient());
const bedrockClient = new BedrockRuntimeClient({ region: process.env.AWS_REGION });

const IMAGES_BUCKET = process.env.AWS_S3_IMAGES_BUCKET;
const VIDEOS_BUCKET = process.env.AWS_S3_VIDEOS_BUCKET;
const TABLE_NAME = process.env.AWS_DYNAMODB_TABLE_VIDEO_TASKS;
const MODEL_ID = process.env.AWS_BEDROCK_MODEL_ID;

export const handler = async (event) => {
  console.log('Received event:', JSON.stringify(event, null, 2));

  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));

    console.log(`Processing: ${bucket}/${key}`);

    // 解析 key 取得 residentId 和 familyMemberId
    // 格式: images/{residentId}/{familyMemberId}/{timestamp}_{filename}
    const keyParts = key.split('/');
    if (keyParts.length < 4 || keyParts[0] !== 'images') {
      console.log('Invalid key format, skipping');
      continue;
    }

    const residentId = keyParts[1];
    const familyMemberId = keyParts[2];

    // 查找對應的 PENDING 任務
    const queryResult = await dynamoClient.send(new QueryCommand({
      TableName: TABLE_NAME,
      IndexName: 'residentId-createdAt-index',
      KeyConditionExpression: 'residentId = :rid',
      FilterExpression: 'imageKey = :imageKey AND #status = :status',
      ExpressionAttributeNames: { '#status': 'status' },
      ExpressionAttributeValues: {
        ':rid': residentId,
        ':imageKey': key,
        ':status': 'PENDING',
      },
      Limit: 1,
    }));

    if (!queryResult.Items || queryResult.Items.length === 0) {
      console.log('No pending task found for this image');
      continue;
    }

    const task = queryResult.Items[0];
    const taskId = task.taskId;

    try {
      // 更新狀態為 PROCESSING
      await updateTaskStatus(taskId, 'PROCESSING');

      // 呼叫 Bedrock 生成影片
      const videoKey = `videos/${residentId}/${familyMemberId}/${taskId}.mp4`;
      
      // Bedrock Luma Ray 非同步呼叫
      const invokeResult = await bedrockClient.send(new StartAsyncInvokeCommand({
        modelId: MODEL_ID,
        modelInput: {
          taskType: 'IMAGE_TO_VIDEO',
          imageToVideoParams: {
            images: [{
              format: 'jpeg',
              source: {
                s3Location: {
                  uri: `s3://${IMAGES_BUCKET}/${key}`,
                },
              },
            }],
            text: 'gentle natural movement, soft breathing motion, warm family atmosphere, subtle eye blinks, slight head movement',
          },
          videoGenerationConfig: {
            durationSeconds: 5,
            fps: 24,
            dimension: '1280x720',
          },
        },
        outputDataConfig: {
          s3OutputDataConfig: {
            s3Uri: `s3://${VIDEOS_BUCKET}/${videoKey}`,
          },
        },
      }));

      const invocationArn = invokeResult.invocationArn;
      console.log('Started async invoke:', invocationArn);

      // 輪詢等待完成（Lambda 有 5 分鐘 timeout）
      let completed = false;
      let attempts = 0;
      const maxAttempts = 60; // 最多等待 5 分鐘

      while (!completed && attempts < maxAttempts) {
        await sleep(5000); // 等待 5 秒
        attempts++;

        const statusResult = await bedrockClient.send(new GetAsyncInvokeCommand({
          invocationArn,
        }));

        console.log(`Attempt ${attempts}: Status = ${statusResult.status}`);

        if (statusResult.status === 'Completed') {
          completed = true;
          
          // 建立影片 URL
          const videoUrl = `https://${VIDEOS_BUCKET}.s3.${process.env.AWS_REGION}.amazonaws.com/${videoKey}`;
          
          // 更新任務為完成
          await updateTaskStatus(taskId, 'COMPLETED', {
            videoKey,
            videoUrl,
          });
          
          console.log('Video generation completed:', videoUrl);
        } else if (statusResult.status === 'Failed') {
          throw new Error(statusResult.failureMessage || 'Bedrock generation failed');
        }
      }

      if (!completed) {
        throw new Error('Timeout waiting for video generation');
      }

    } catch (error) {
      console.error('Error processing:', error);
      
      await updateTaskStatus(taskId, 'FAILED', {
        errorMessage: error.message || '影片生成失敗',
      });
    }
  }

  return { statusCode: 200, body: 'OK' };
};

async function updateTaskStatus(taskId, status, extraFields = {}) {
  const updateExpression = ['#status = :status', 'updatedAt = :updatedAt'];
  const expressionAttributeValues = {
    ':status': status,
    ':updatedAt': Date.now(),
  };

  for (const [key, value] of Object.entries(extraFields)) {
    updateExpression.push(`${key} = :${key}`);
    expressionAttributeValues[`:${key}`] = value;
  }

  await dynamoClient.send(new UpdateCommand({
    TableName: TABLE_NAME,
    Key: { taskId },
    UpdateExpression: `SET ${updateExpression.join(', ')}`,
    ExpressionAttributeNames: { '#status': 'status' },
    ExpressionAttributeValues: expressionAttributeValues,
  }));
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
