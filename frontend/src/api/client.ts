const API_BASE_URL = 'http://localhost:8000';

export async function fetchSmallTalks(tag?: string, limit = 10, offset = 0) {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    ...(tag && { tag }),
  });
  
  const response = await fetch(`${API_BASE_URL}/small-talk?${params}`);
  if (!response.ok) throw new Error('Failed to fetch small talks');
  return response.json();
}

export async function fetchAnswers(talkId: number) {
  const response = await fetch(`${API_BASE_URL}/answers/${talkId}`);
  if (!response.ok) throw new Error('Failed to fetch answers');
  return response.json();
}

export async function createSmallTalk(data: Omit<SmallTalk, 'talk_id' | 'update_at'>) {
  const response = await fetch(`${API_BASE_URL}/small-talk`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create small talk');
  return response.json();
}

export async function createAnswer(data: { talk_id: number; eng_sentence: string; kor_sentence: string; }) {
  const response = await fetch(`${API_BASE_URL}/answers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to create answer');
  return response.json();
}

export async function getBotStatus() {
  const response = await fetch(`${API_BASE_URL}/bot/status`);
  if (!response.ok) throw new Error('Failed to get bot status');
  return response.json();
}

export async function toggleBot(start: boolean) {
  const response = await fetch(`${API_BASE_URL}/bot/${start ? 'start' : 'stop'}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error(`Failed to ${start ? 'start' : 'stop'} bot`);
  return response.json();
}

export async function sendMessageNow() {
  const response = await fetch(`${API_BASE_URL}/bot/send-now`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to send message');
  return response.json();
}