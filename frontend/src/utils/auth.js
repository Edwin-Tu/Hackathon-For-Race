// 取得 JWT 中的 role（要先在前端取得 token，這裡假設儲存在 localStorage）
export function getUserRole(token) {
  if (!token) return null;
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.role?.toUpperCase() || null;
  } catch (e) {
    return null;
  }
}
