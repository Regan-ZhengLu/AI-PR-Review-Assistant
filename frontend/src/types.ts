export type RiskLevel = 'high' | 'medium' | 'low';
export type Confidence = 'high' | 'medium' | 'low';

export interface ReviewRisk {
  file: string;
  line?: number | null;
  severity: RiskLevel;
  type: string;
  description: string;
  suggestion: string;
  confidence: Confidence;
}

export interface PullRequestInfo {
  title?: string;
  author?: string;
  repository?: string;
  pullNumber?: number;
  changedFiles?: number;
  additions?: number;
  deletions?: number;
}

export interface ReviewResult {
  summary: string;
  riskLevel: RiskLevel;
  risks: ReviewRisk[];
  suggestions: string[];
  mergeRecommendation: string;
  confidence?: Confidence;
  usedAi?: boolean;
  model?: string;
  fallbackReason?: string;
  pr?: PullRequestInfo;
}
