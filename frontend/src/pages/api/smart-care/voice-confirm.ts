import type { NextApiRequest, NextApiResponse } from 'next';
import { fetchSmartCare, pipeSmartCareResponse } from '../../../server/smartCareProxy';

export const config = {
  api: {
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
    const upstream = await fetchSmartCare('/api/voice/confirm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request.body),
    });
    await pipeSmartCareResponse(upstream, response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Confirmation proxy failed';
    response.status(502).json({ detail: message });
  }
}
