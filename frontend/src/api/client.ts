import { API_CONFIG } from '../config/api';
import { SmallTalk } from '../types/api';

export async function fetchSmallTalks(tag?: string, limit = 10, offset = 0) {
 const params = new URLSearchParams({
   limit: limit.toString(),
   offset: offset.toString(),
   ...(tag && { tag }),
 });

 const [countResponse, dataResponse] = await Promise.all([
   fetch(`${API_CONFIG.baseURL}/small-talk/count${tag ? `?tag=${tag}` : ''}`, {
     headers: API_CONFIG.headers,
   }),
   fetch(`${API_CONFIG.baseURL}/small-talk?${params}`, {
     headers: API_CONFIG.headers,
   })
 ]);

 if (!countResponse.ok || !dataResponse.ok) {
   throw new Error('Failed to fetch small talks or count');
 }

 const [{ total }, items] = await Promise.all([
   countResponse.json(),
   dataResponse.json()
 ]);

 return {
   items,
   total
 };
}

export async function fetchAnswers(talkId: number) {
 const response = await fetch(`${API_CONFIG.baseURL}/answers/${talkId}`, {
   headers: API_CONFIG.headers,
 });
 if (!response.ok) throw new Error('Failed to fetch answers');
 return response.json();
}

export async function createSmallTalk(data: Omit<SmallTalk, 'talk_id' | 'update_at'>) {
 const response = await fetch(`${API_CONFIG.baseURL}/small-talk`, {
   method: 'POST',
   headers: API_CONFIG.headers,
   body: JSON.stringify(data),
 });
 if (!response.ok) throw new Error('Failed to create small talk');
 return response.json();
}

export async function createAnswer(data: { talk_id: number; eng_sentence: string; kor_sentence: string; }) {
 const response = await fetch(`${API_CONFIG.baseURL}/answers`, {
   method: 'POST',
   headers: API_CONFIG.headers,
   body: JSON.stringify(data),
 });
 if (!response.ok) throw new Error('Failed to create answer');
 return response.json();
}

export async function getBotStatus() {
 const response = await fetch(`${API_CONFIG.baseURL}/bot/status`, {
   headers: API_CONFIG.headers,
 });
 if (!response.ok) throw new Error('Failed to get bot status');
 return response.json();
}

export async function toggleBot(start: boolean) {
 const response = await fetch(`${API_CONFIG.baseURL}/bot/${start ? 'start' : 'stop'}`, {
   method: 'POST',
   headers: API_CONFIG.headers,
 });
 if (!response.ok) throw new Error(`Failed to ${start ? 'start' : 'stop'} bot`);
 return response.json();
}

export async function sendMessageNow() {
 const response = await fetch(`${API_CONFIG.baseURL}/bot/send-now`, {
   method: 'POST',
   headers: API_CONFIG.headers,
 });
 if (!response.ok) throw new Error('Failed to send message');
 return response.json();
}