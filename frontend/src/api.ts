import type { ReviewResult } from './types';

const apiBaseUrl = import.meta.env.VITE_BACKEND_URL ?? '';

export async function requestReview(prUrl: string): Promise<ReviewResult> {
  const response = await fetch(`${apiBaseUrl}/api/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prUrl }),
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const message = payload?.detail || payload?.message || `请求失败：HTTP ${response.status}`;
    throw new Error(message);
  }

  return payload as ReviewResult;
}
