// src/utils/auth.ts
/**
 * 認證工具函數
 */

/**
 * 從 JWT Token 中提取使用者角色
 * @param token JWT Token
 * @returns 角色字串或 null
 */
export function getUserRole(token: string | null): string | null {
  if (!token) return null;
  
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    const payload = JSON.parse(atob(parts[1]));
    return payload.role || null;
  } catch (error) {
    console.error('Failed to parse JWT token:', error);
    return null;
  }
}

/**
 * 從 JWT Token 中提取使用者資訊
 * @param token JWT Token
 * @returns 使用者資訊物件或 null
 */
export function getUserInfo(token: string | null): {
  sub: string;
  role: string;
  displayName: string;
  personaId?: string;
  organizationId?: string;
  exp: number;
  iat: number;
} | null {
  if (!token) return null;
  
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    
    const payload = JSON.parse(atob(parts[1]));
    return payload;
  } catch (error) {
    console.error('Failed to parse JWT token:', error);
    return null;
  }
}

/**
 * 檢查 Token 是否過期
 * @param token JWT Token
 * @returns true 如果過期，false 如果有效
 */
export function isTokenExpired(token: string | null): boolean {
  if (!token) return true;
  
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return true;
    
    const payload = JSON.parse(atob(parts[1]));
    const exp = payload.exp || 0;
    
    // 檢查是否過期（加上 5 秒緩衝）
    return exp < Math.floor(Date.now() / 1000) + 5;
  } catch (error) {
    console.error('Failed to parse JWT token:', error);
    return true;
  }
}

/**
 * 從 localStorage 取得 Token
 * @returns JWT Token 或 null
 */
export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth');
}

/**
 * 儲存 Token 到 localStorage 和 Cookie
 * @param token JWT Token
 */
export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  
  // 儲存到 localStorage
  localStorage.setItem('auth', token);
  
  // 儲存到 HttpOnly Cookie (實際上應該由伺服器設定)
  document.cookie = `auth=${token}; path=/; max-age=604800; SameSite=Strict`;
}

/**
 * 清除 Token
 */
export function clearToken(): void {
  if (typeof window === 'undefined') return;
  
  // 清除 localStorage
  localStorage.removeItem('auth');
  
  // 清除 Cookie
  document.cookie = 'auth=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
}

/**
 * 檢查使用者是否已登入
 * @returns true 如果已登入且 Token 有效
 */
export function isAuthenticated(): boolean {
  const token = getToken();
  return token !== null && !isTokenExpired(token);
}

/**
 * 檢查使用者是否有指定角色
 * @param requiredRole 需要的角色
 * @returns true 如果使用者有該角色
 */
export function hasRole(requiredRole: string): boolean {
  const token = getToken();
  const role = getUserRole(token);
  return role === requiredRole;
}

/**
 * 檢查使用者是否有任一指定角色
 * @param requiredRoles 需要的角色陣列
 * @returns true 如果使用者有任一角色
 */
export function hasAnyRole(requiredRoles: string[]): boolean {
  const token = getToken();
  const role = getUserRole(token);
  return role !== null && requiredRoles.includes(role);
}
