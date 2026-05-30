import type { ReviewResult, ReviewRisk, RiskLevel } from './types';

const riskLabels: Record<RiskLevel, string> = {
  high: 'High Risk',
  medium: 'Medium Risk',
  low: 'Low Risk',
};

export function formatReviewMarkdown(review: ReviewResult): string {
  const lines: string[] = [];
  const pr = review.pr;

  lines.push('## AI Review Summary');
  lines.push('');
  if (pr?.repository || pr?.title) {
    lines.push(`**PR:** ${formatPrTitle(review)}`);
    lines.push('');
  }
  lines.push(review.summary || '暂无 PR 总结。');
  lines.push('');
  lines.push(`**Overall Risk:** ${riskLabels[review.riskLevel] ?? review.riskLevel}`);
  if (review.confidence) {
    lines.push(`**Confidence:** ${review.confidence}`);
  }
  if (review.usedAi === false) {
    lines.push('**Mode:** Rule-based fallback review');
  } else if (review.model) {
    lines.push(`**Model:** ${review.model}`);
  }
  lines.push('');

  lines.push('## Risks');
  lines.push('');
  if (review.risks.length === 0) {
    lines.push('未发现明确风险，建议仍结合业务语义进行人工确认。');
  } else {
    appendGroupedRisks(lines, review.risks);
  }
  lines.push('');

  lines.push('## Suggestions');
  lines.push('');
  if (review.suggestions.length === 0) {
    lines.push('- 暂无额外建议。');
  } else {
    review.suggestions.forEach((suggestion) => lines.push(`- ${suggestion}`));
  }
  lines.push('');

  lines.push('## Merge Recommendation');
  lines.push('');
  lines.push(review.mergeRecommendation || '建议人工确认后再合并。');

  return `${lines.join('\n').trim()}\n`;
}

function appendGroupedRisks(lines: string[], risks: ReviewRisk[]) {
  const order: RiskLevel[] = ['high', 'medium', 'low'];

  order.forEach((level) => {
    const group = risks.filter((risk) => risk.severity === level);
    if (group.length === 0) {
      return;
    }

    lines.push(`### ${riskLabels[level]}`);
    lines.push('');
    group.forEach((risk) => {
      lines.push(`- \`${formatRiskLocation(risk)}\``);
      lines.push(`  - 类型：${risk.type || 'unknown'}`);
      lines.push(`  - 问题：${risk.description || '未提供问题说明。'}`);
      if (risk.suggestion) {
        lines.push(`  - 建议：${risk.suggestion}`);
      }
      lines.push(`  - 置信度：${risk.confidence}`);
    });
    lines.push('');
  });
}

function formatRiskLocation(risk: ReviewRisk): string {
  if (!risk.file) {
    return risk.line ? `line ${risk.line}` : 'unknown location';
  }
  return risk.line ? `${risk.file}:${risk.line}` : risk.file;
}

function formatPrTitle(review: ReviewResult): string {
  const pr = review.pr;
  const repoAndNumber = pr?.repository ? `${pr.repository}${pr.pullNumber ? ` #${pr.pullNumber}` : ''}` : '';
  const title = pr?.title ?? '';
  return [repoAndNumber, title].filter(Boolean).join(' - ');
}
