import type { ReviewResult } from './types';

export async function requestReview(prUrl: string): Promise<ReviewResult> {
  const response = await fetch('/api/review', {
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
