import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // 解析 JWT 取得角色並導向對應頁面
    const token = localStorage.getItem('auth');
    if (!token) {
      router.replace('/login');
      return;
    }

    try {
      const payloadBase64 = token.split('.')[1];
      if (!payloadBase64) {
        router.replace('/login');
        return;
      }
      const payload = JSON.parse(atob(payloadBase64)) as { role: string };
      
      // 依據角色導向對應頁面
      switch (payload.role) {
        case 'ADMIN':
          router.replace('/admin/Users');
          break;
        case 'FAMILY':
          router.replace('/family/Dashboard');
          break;
        case 'RESIDENT':
          router.replace('/resident/voice');
          break;
        case 'CAREGIVER':
        default:
          router.replace('/caregiver');
          break;
      }
    } catch {
      router.replace('/login');
    }
  }, [router]);

  return null;
}
