import type { NextApiRequest, NextApiResponse } from 'next';
import { fetchSmartCare, pipeSmartCareResponse, readRawRequest } from '../../../server/smartCareProxy';

export const config = {
  api: {
    bodyParser: false,
    responseLimit: '12mb',
  },
};

export default async function handler(request: NextApiRequest, response: NextApiResponse) {
  if (request.method !== 'POST') {
    response.setHeader('Allow', 'POST');
    response.status(405).json({ detail: 'Method not allowed' });
    return;
  }

  try {
    const rawBody = await readRawRequest(request);
    const contentType = request.headers['content-type'];
    const upstream = await fetchSmartCare('/api/voice/turn', {
      method: 'POST',
      headers: contentType ? { 'Content-Type': contentType } : {},
      body: rawBody as unknown as BodyInit,
    });
    await pipeSmartCareResponse(upstream, response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Voice proxy failed';
    response.status(502).json({ detail: message });
  }
}
