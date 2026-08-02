import { useState, useEffect } from 'react';

export function useFamilyNotifications() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setTimeout(() => {
      setData([
        { id: '1', title: '血糖偏高', time: '2026-08-01 09:30' },
        { id: '2', title: '心率異常', time: '2026-08-01 11:12' },
      ]);
      setLoading(false);
    }, 400);
  }, []);

  return { data, loading, error };
}
