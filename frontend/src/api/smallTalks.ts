import { API_CONFIG } from '../config/api';
import { SmallTalk } from '../types/api';
import { handleApiError } from '../utils/error';

export async function fetchSmallTalks(tag?: string, limit = 10, offset = 0) {
  try {
    // 데이터 조회와 개수 조회를 병렬로 처리
    const [dataResponse, countResponse] = await Promise.all([
      fetch(`${API_CONFIG.baseURL}/small-talk?${new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),        
        ...(tag && { tag }),
      })}`, {
        headers: API_CONFIG.headers,
      }),
      fetch(`${API_CONFIG.baseURL}/small-talk/count${tag ? `?tag=${tag}` : ''}`, {
        headers: API_CONFIG.headers,
      })
    ]);

    // 응답 확인
    if (!dataResponse.ok || !countResponse.ok) {
      console.error('Data response:', dataResponse.status, await dataResponse.text());
      console.error('Count response:', countResponse.status, await countResponse.text());
      throw new Error('Failed to fetch data');
    }

    // 응답 데이터 파싱
    const [items, countData] = await Promise.all([
      dataResponse.json(),
      countResponse.json()
    ]);

    return {
      items,
      total: countData.total
    };
  } catch (error) {
    console.error('Fetch error:', error);
    throw handleApiError(error);
  }
}

export async function createSmallTalk(data: Omit<SmallTalk, 'talk_id' | 'update_at'>) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/small-talk`, {
      method: 'POST',
      headers: API_CONFIG.headers,
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create small talk');
    return response.json();
  } catch (error) {
    throw handleApiError(error);
  }
}

export async function deleteSmallTalk(talkId: number) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/small-talk/${talkId}`, {
      method: 'DELETE',
      headers: API_CONFIG.headers,
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Delete error response:', response.status, errorData);
      throw new Error(
        `Failed to delete small talk: ${response.status} ${errorData}`
      );
    }

    return response.json();
  } catch (error) {
    console.error('Delete error:', error);
    throw handleApiError(error);
  }
}

export async function updateSmallTalk(talkId: number, data: Partial<SmallTalk>) {
  try {
    const response = await fetch(`${API_CONFIG.baseURL}/small-talk/${talkId}`, {
      method: 'PATCH',
      headers: API_CONFIG.headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorData = await response.text();
      console.error('Update error response:', response.status, errorData);
      throw new Error(`Failed to update small talk: ${response.status} ${errorData}`);
    }

    return response.json();
  } catch (error) {
    console.error('Update error:', error);
    throw handleApiError(error);
  }
}