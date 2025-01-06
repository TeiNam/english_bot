import { API_CONFIG } from '../config/api';
import { handleApiError } from '../utils/error';

export async function getBotStatus() {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/bot/status`, {
      headers: API_CONFIG.headers,
    });
    if (!response.ok) throw new Error('Failed to get bot status');
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

export async function toggleBot(start: boolean) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/bot/${start ? 'start' : 'stop'}`, {
      method: 'POST',
      headers: API_CONFIG.headers,
    });
    if (!response.ok) throw new Error(`Failed to ${start ? 'start' : 'stop'} bot`);
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

export async function sendMessageNow() {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/bot/send-now`, {
      method: 'POST',
      headers: API_CONFIG.headers,
    });
    if (!response.ok) throw new Error('Failed to send message');
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}