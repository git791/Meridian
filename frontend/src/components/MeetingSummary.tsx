"use client";

interface ActionItem {
    owner: string;
    task: string;
    deadline: string | null;
}

interface SummaryData {
    title?: string;
    summary_paragraph?: string;
    key_decisions?: string[];
    action_items?: ActionItem[];
    topics_covered?: string[];
    follow_up_meeting_needed?: boolean;
}

export default function MeetingSummary({ summary }: { summary: Record<string, unknown> | null }) {
    if (!summary) {
        return (
            <div className="summary-empty">
                <div className="empty-icon">≋</div>
                <h3>No summaries yet</h3>
                <p>Upload a meeting recording and ask Meridian to summarise it. Action items, decisions, and follow-ups will appear here.</p>
                <style>{`
          .summary-empty {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 16px;
            padding: 60px;
            text-align: center;
          }
          .empty-icon {
            font-size: 48px;
            color: var(--text-dim);
            margin-bottom: 8px;
          }
          .summary-empty h3 {
            font-family: 'DM Serif Display', serif;
            font-size: 22px;
            font-weight: 400;
            color: var(--text-muted);
          }
          .summary-empty p {
            font-size: 14px;
            color: var(--text-dim);
            max-width: 360px;
            line-height: 1.7;
          }
        `}</style>
            </div>
        );
    }

    const s = summary as SummaryData;

    return (
        <div className="summary-page">
            <div className="summary-content">
                <div className="summary-card card-hero">
                    <div className="card-tag">Summary</div>
                    <h2>{s.title ?? "Meeting Summary"}</h2>
                    <p>{s.summary_paragraph}</p>
                    {s.follow_up_meeting_needed && (
                        <div className="followup-badge">↩ Follow-up meeting recommended</div>
                    )}
                </div>

                <div className="summary-grid">
                    {s.key_decisions && s.key_decisions.length > 0 && (
                        <div className="summary-card">
                            <div className="card-tag">Key Decisions</div>
                            <ul className="decision-list">
                                {s.key_decisions.map((d, i) => (
                                    <li key={i}><span className="dec-dot">◆</span>{d}</li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {s.topics_covered && s.topics_covered.length > 0 && (
                        <div className="summary-card">
                            <div className="card-tag">Topics Covered</div>
                            <div className="topic-chips">
                                {s.topics_covered.map((t, i) => (
                                    <span key={i} className="topic-chip">{t}</span>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {s.action_items && s.action_items.length > 0 && (
                    <div className="summary-card">
                        <div className="card-tag">Action Items</div>
                        <div className="action-list">
                            {s.action_items.map((item, i) => (
                                <div key={i} className="action-item">
                                    <div className="action-index">{i + 1}</div>
                                    <div className="action-body">
                                        <p className="action-task">{item.task}</p>
                                        <p className="action-meta">
                                            <span className="action-owner">@{item.owner}</span>
                                            {item.deadline && <span className="action-deadline">· Due {item.deadline}</span>}
                                        </p>
                                    </div>
                                    <div className="action-checkbox" />
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <style>{`
        .summary-page {
          flex: 1;
          overflow-y: auto;
          padding: 28px 36px;
        }

        .summary-content {
          max-width: 760px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .summary-card {
          background: var(--bg2);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 22px 24px;
        }

        .card-hero {
          background: linear-gradient(135deg, var(--bg2) 0%, rgba(61,232,160,0.04) 100%);
          border-color: rgba(61,232,160,0.15);
        }

        .card-tag {
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--accent);
          margin-bottom: 10px;
        }

        .card-hero h2 {
          font-family: 'DM Serif Display', serif;
          font-size: 22px;
          font-weight: 400;
          margin-bottom: 10px;
        }

        .card-hero p {
          font-size: 14px;
          color: var(--text-muted);
          line-height: 1.7;
        }

        .followup-badge {
          margin-top: 14px;
          display: inline-flex;
          padding: 6px 12px;
          border-radius: 8px;
          background: rgba(77,184,255,0.1);
          border: 1px solid rgba(77,184,255,0.25);
          color: var(--accent2);
          font-size: 12px;
        }

        .summary-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        .decision-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .decision-list li {
          display: flex;
          gap: 8px;
          font-size: 13px;
          color: var(--text-muted);
          line-height: 1.5;
        }

        .dec-dot { color: var(--accent); font-size: 10px; margin-top: 3px; flex-shrink: 0; }

        .topic-chips { display: flex; flex-wrap: wrap; gap: 6px; }

        .topic-chip {
          padding: 4px 10px;
          border-radius: 6px;
          background: var(--bg3);
          border: 1px solid var(--border);
          font-size: 12px;
          color: var(--text-muted);
        }

        .action-list { display: flex; flex-direction: column; gap: 10px; }

        .action-item {
          display: flex;
          align-items: flex-start;
          gap: 12px;
          padding: 12px 14px;
          border-radius: 10px;
          background: var(--bg3);
          border: 1px solid var(--border);
        }

        .action-index {
          width: 24px; height: 24px;
          border-radius: 6px;
          background: rgba(124,106,247,0.15);
          color: var(--agent-orch);
          display: flex; align-items: center; justify-content: center;
          font-size: 12px; font-weight: 600;
          flex-shrink: 0;
        }

        .action-body { flex: 1; }
        .action-task { font-size: 13px; font-weight: 500; margin-bottom: 4px; }
        .action-meta { font-size: 12px; color: var(--text-muted); }
        .action-owner { color: var(--accent2); }
        .action-deadline { margin-left: 4px; }

        .action-checkbox {
          width: 18px; height: 18px;
          border-radius: 4px;
          border: 1px solid var(--border-bright);
          flex-shrink: 0;
          margin-top: 2px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .action-checkbox:hover { border-color: var(--accent); background: rgba(61,232,160,0.1); }
      `}</style>
        </div>
    );
}