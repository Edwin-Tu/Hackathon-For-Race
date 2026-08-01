import { useState, useEffect } from 'react';

// 這是一個簡易的 mock hook，實務上應該呼叫 RTK Query / fetch
export function useFamilyStats() {
  const [stats, setStats] = useState({ glucose: 0, heartRate: 0, unreadAlerts: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 模擬 API 延遲
    setTimeout(() => {
      setStats({ glucose: 110, heartRate: 72, unreadAlerts: 1 });
      setLoading(false);
    }, 500);
  }, []);

  return { stats, loading, error };
}
