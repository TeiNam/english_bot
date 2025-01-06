import { API_CONFIG } from '../config/api';
import { handleApiError } from '../utils/error';

export async function fetchAnswers(talkId: number) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/answers/${talkId}`, {
      headers: API_CONFIG.headers,
    });
    if (!response.ok) throw new Error('Failed to fetch answers');
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

export async function createAnswer(data: { talk_id: number; eng_sentence: string; kor_sentence: string; }) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/answers`, {
      method: 'POST',
      headers: API_CONFIG.headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create answer');
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

export async function deleteAnswer(answerId: number) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/answers/${answerId}`, {
      method: 'DELETE',
      headers: API_CONFIG.headers,
    });
    if (!response.ok) throw new Error('Failed to delete answer');
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}