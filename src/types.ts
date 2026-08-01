export interface Resident {
  id: string;
  name: string;
  // 其他欄位依後端 API 定義
}

export interface Event {
  id: string;
  residentId: string;
  type: string;
  time: string;
}

export interface Reminder {
  id: string;
  residentId: string;
  title: string;
  scheduledAt: string;
}
