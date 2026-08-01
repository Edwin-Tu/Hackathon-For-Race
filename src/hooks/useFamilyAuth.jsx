import { useState, useEffect } from 'react';

export function useFamilyAuth() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = async () => {
    // 假資料
    setData([
      { id: '1', username: 'caregiver1', status: '已授權' },
      { id: '2', username: 'caregiver2', status: '待授權' },
    ]);
    setLoading(false);
  };

  useEffect(() => {
    refetch();
  }, []);

  return { data, loading, error, refetch };
}
