import type { FormEvent } from 'react';
import { useState } from 'react';
import { requestReview } from './api';
import { formatReviewMarkdown } from './formatReviewMarkdown';
import { RiskBadge } from './RiskBadge';
import type { ReviewResult } from './types';

const exampleUrl = 'https://github.com/facebook/react/pull/30872';

function App() {
  const [prUrl, setPrUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [review, setReview] = useState<ReviewResult | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedUrl = prUrl.trim();
    if (!trimmedUrl) {
      setError('请输入 GitHub Pull Request 链接。');
      return;
    }

    setLoading(true);
    setError('');
    setReview(null);

    try {
      const result = await requestReview(trimmedUrl);
      setReview(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '分析失败，请稍后重试。');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-card">
        <div className="hero-copy">
          <p className="eyebrow">AI PR Review Assistant</p>
          <h1>输入 GitHub PR 链接，快速获得代码评审摘要与风险建议</h1>
          <p className="hero-description">
            系统会自动获取 PR 标题、描述和 diff 内容，结合规则预分析与 AI Review 输出结构化评审结果。
          </p>
        </div>

        <form className="review-form" onSubmit={handleSubmit}>
          <label htmlFor="pr-url">GitHub PR 链接</label>
          <div className="input-row">
            <input
              id="pr-url"
              type="url"
              value={prUrl}
              onChange={(event) => setPrUrl(event.target.value)}
              placeholder={exampleUrl}
              disabled={loading}
            />
            <button type="submit" disabled={loading}>
              {loading ? '分析中...' : '开始分析'}
            </button>
          </div>
          <p className="form-hint">示例：{exampleUrl}</p>
        </form>
      </section>

      {error && <div className="alert alert--error">{error}</div>}
      {loading && <LoadingState />}
      {review && <ReviewResultView review={review} />}
      {!loading && !review && !error && <EmptyState />}
    </main>
  );
}

function LoadingState() {
  return (
    <section className="status-card">
      <div className="spinner" />
      <div>
        <h2>正在分析 PR</h2>
        <p>正在获取 GitHub PR 数据并生成 Review 建议，请稍候。</p>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <section className="status-card status-card--muted">
      <h2>准备开始</h2>
      <p>输入一个公开 GitHub PR 链接后，这里会展示 Summary、Risks、Suggestions 和 Merge Recommendation。</p>
    </section>
  );
}

function ReviewResultView({ review }: { review: ReviewResult }) {
  const pr = review.pr;
  const [copyStatus, setCopyStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const markdown = formatReviewMarkdown(review);

  async function handleCopyMarkdown() {
    setCopyStatus('idle');
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error('当前浏览器不支持剪贴板 API');
      }
      await navigator.clipboard.writeText(markdown);
      setCopyStatus('success');
    } catch (err) {
      setCopyStatus('error');
    }
  }

  return (
    <section className="result-grid">
      <article className="panel panel--summary">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Summary</p>
            <h2>PR 变更总结</h2>
          </div>
          <div className="summary-actions">
            <RiskBadge level={review.riskLevel} />
            <button className="copy-button" type="button" onClick={handleCopyMarkdown}>
              复制 Review
            </button>
          </div>
        </div>

        {pr && (
          <div className="pr-meta">
            <span>{pr.repository ? `${pr.repository} #${pr.pullNumber ?? ''}` : 'Pull Request'}</span>
            {pr.author && <span>作者：{pr.author}</span>}
            <span>文件：{pr.changedFiles ?? 0}</span>
            <span className="stat-add">+{pr.additions ?? 0}</span>
            <span className="stat-del">-{pr.deletions ?? 0}</span>
          </div>
        )}

        {pr?.title && <h3 className="pr-title">{pr.title}</h3>}
        <p className="summary-text">{review.summary}</p>

        <div className="model-row">
          <span>{review.usedAi ? 'AI 分析已启用' : '当前为规则预分析结果'}</span>
          {review.model && <span>模型：{review.model}</span>}
          {review.confidence && <span>置信度：{review.confidence}</span>}
        </div>
        {copyStatus === 'success' && <p className="copy-status copy-status--success">已复制 Markdown Review，可直接粘贴到 GitHub PR 评论区。</p>}
        {copyStatus === 'error' && <p className="copy-status copy-status--error">复制失败，请手动复制下方 Markdown 内容。</p>}
        {review.fallbackReason && <p className="fallback-note">Fallback 原因：{review.fallbackReason}</p>}
      </article>

      <article className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Risks</p>
            <h2>风险代码列表</h2>
          </div>
          <span className="count-pill">{review.risks.length}</span>
        </div>

        {review.risks.length > 0 ? (
          <div className="risk-list">
            {review.risks.map((risk, index) => (
              <div className="risk-item" key={`${risk.file}-${risk.line ?? 'file'}-${index}`}>
                <div className="risk-item__header">
                  <code>
                    {risk.file}
                    {risk.line ? `:${risk.line}` : ''}
                  </code>
                  <RiskBadge level={risk.severity} />
                </div>
                <div className="risk-tags">
                  <span>{risk.type}</span>
                  <span>confidence: {risk.confidence}</span>
                </div>
                <p>{risk.description}</p>
                {risk.suggestion && <p className="suggestion-line">建议：{risk.suggestion}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-copy">未发现明确风险。建议仍结合业务语义进行人工确认。</p>
        )}
      </article>

      <article className="panel">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Suggestions</p>
            <h2>Review 建议</h2>
          </div>
        </div>
        {review.suggestions.length > 0 ? (
          <ul className="suggestion-list">
            {review.suggestions.map((item, index) => (
              <li key={`${item}-${index}`}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="empty-copy">暂无额外建议。</p>
        )}
      </article>

      <article className="panel panel--markdown">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Markdown</p>
            <h2>可复制 Review 内容</h2>
          </div>
          <button className="copy-button copy-button--secondary" type="button" onClick={handleCopyMarkdown}>
            复制 Markdown
          </button>
        </div>
        <pre className="markdown-preview">{markdown}</pre>
      </article>

      <article className="panel panel--recommendation">
        <p className="eyebrow">Merge Recommendation</p>
        <h2>合并建议</h2>
        <p>{review.mergeRecommendation}</p>
      </article>
    </section>
  );
}

export default App;
