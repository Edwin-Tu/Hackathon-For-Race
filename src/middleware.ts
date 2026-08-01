import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  
  // 允許直接存取的路由（不需驗證）
  const publicPaths = ['/login', '/_next', '/favicon.ico', '/api'];
  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  const token = req.cookies.get('auth')?.value;
  if (!token) {
    return NextResponse.redirect(new URL('/login', req.url));
  }

  // 簡易解析 JWT payload（不驗證簽名，僅供 Demo）
  try {
    const payloadBase64 = token.split('.')[1];
    const payload = JSON.parse(atob(payloadBase64)) as {
      role: string;
      sub?: string;
    };
    const res = NextResponse.next();
    res.headers.set('x-user-role', payload.role);
    return res;
  } catch {
    return NextResponse.redirect(new URL('/login', req.url));
  }
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
