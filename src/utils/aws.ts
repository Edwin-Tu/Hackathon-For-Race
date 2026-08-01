import { S3Client } from '@aws-sdk/client-s3';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb';

// S3 Client
export const s3Client = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// DynamoDB Client
const dynamoClient = new DynamoDBClient({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export const docClient = DynamoDBDocumentClient.from(dynamoClient);

// 環境變數
export const AWS_CONFIG = {
  imagesBucket: process.env.AWS_S3_IMAGES_BUCKET!,
  videosBucket: process.env.AWS_S3_VIDEOS_BUCKET!,
  videoTasksTable: process.env.AWS_DYNAMODB_TABLE_VIDEO_TASKS!,
  bedrockModelId: process.env.AWS_BEDROCK_MODEL_ID!,
  region: process.env.AWS_REGION!,
};
