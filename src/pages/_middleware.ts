import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import jwt from 'jsonwebtoken';

export async function middleware(req: NextRequest) {
  const token = req.cookies.get('auth')?.value;
  if (!token) return NextResponse.redirect(new URL('/login', req.url));

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as {
      role: 'caregiver' | 'family' | 'admin';
      residentId?: string;
    };
    const res = NextResponse.next();
    res.headers.set('x-user-role', payload.role);
    if (payload.residentId) res.headers.set('x-resident-id', payload.residentId);
    return res;
  } catch {
    return NextResponse.redirect(new URL('/login', req.url));
  }
}
