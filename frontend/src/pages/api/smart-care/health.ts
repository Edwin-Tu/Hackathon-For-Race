import type { NextApiRequest, NextApiResponse } from 'next';
import { fetchSmartCare, pipeSmartCareResponse } from '../../../server/smartCareProxy';

export default async function handler(request: NextApiRequest, response: NextApiResponse) {
  if (request.method !== 'GET') {
    response.setHeader('Allow', 'GET');
    response.status(405).json({ detail: 'Method not allowed' });
    return;
  }

  try {
    const upstream = await fetchSmartCare('/health', { method: 'GET' }, 10_000);
    await pipeSmartCareResponse(upstream, response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Health proxy failed';
    response.status(502).json({ detail: message });
  }
}
