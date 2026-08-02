import type { NextApiResponse } from 'next';

const DEFAULT_TIMEOUT_MS = 120_000;

export function smartCareApiUrl(path: string): string {
  const base = process.env.SMART_CARE_API_URL?.replace(/\/$/, '');
  if (!base) {
    throw new Error('SMART_CARE_API_URL is not configured');
  }
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

export function smartCareHeaders(extra: HeadersInit = {}): Headers {
  const headers = new Headers(extra);
  const token = process.env.SMART_CARE_API_TOKEN;
  if (token) headers.set('Authorization', `Bearer ${token}`);
  return headers;
}

export async function fetchSmartCare(
  path: string,
  init: RequestInit,
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(smartCareApiUrl(path), {
      ...init,
      headers: smartCareHeaders(init.headers),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

export async function pipeSmartCareResponse(
  upstream: Response,
  response: NextApiResponse,
): Promise<void> {
  const contentType = upstream.headers.get('content-type');
  if (contentType) response.setHeader('Content-Type', contentType);
  response.status(upstream.status).send(Buffer.from(await upstream.arrayBuffer()));
}

export async function readRawRequest(request: NodeJS.ReadableStream): Promise<Buffer> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks);
}
