"use client";

import { useEffect, useRef } from "react";

export interface AgentEvent {
    agent: string;
    status?: string;
    message?: string;
    data?: Record<string, unknown>;
    slots?: { start: string; end: string }[];
    summary?: unknown;
    chars?: number;
    count?: number;
}

const AGENT_META: Record<string, { label: string; color: string; icon: string }> = {
    orchestrator: { label: "Orchestrator", color: "#7c6af7", icon: "⟡" },
    calendar_agent: { label: "Calendar Agent", color: "#3de8a0", icon: "▦" },
    email_agent: { label: "Email Agent", color: "#4db8ff", icon: "✉" },
    transcription_agent: { label: "Transcription", color: "#f97316", icon: "⏺" },
    summary_agent: { label: "Summary Agent", color: "#ec4899", icon: "≋" },
    done: { label: "Complete", color: "#3de8a0", icon: "✓" },
};

function AgentNode({ active, color, icon, label }: { active: boolean; color: string; icon: string; label: string }) {
    return (
        <div className="agent-node" style={{ "--agent-color": color } as React.CSSProperties}>
            <div className={`node-icon ${active ? "node-active" : ""}`}>{icon}</div>
            <span className="node-label">{label}</span>
            <style>{`
        .agent-node { display: flex; flex-direction: column; align-items: center; gap: 4px; }
        .node-icon {
          width: 36px; height: 36px;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.1);
          background: var(--bg3);
          display: flex; align-items: center; justify-content: center;
          font-size: 16px;
          color: var(--text-dim);
          transition: all 0.3s;
        }
        .node-icon.node-active {
          border-color: var(--agent-color);
          background: color-mix(in srgb, var(--agent-color) 15%, transparent);
          color: var(--agent-color);
          box-shadow: 0 0 16px color-mix(in srgb, var(--agent-color) 40%, transparent);
        }
        .node-label { font-size: 10px; color: var(--text-dim); text-align: center; max-width: 60px; line-height: 1.3; }
      `}</style>
        </div>
    );
}

function EventRow({ event, index }: { event: AgentEvent; index: number }) {
    const meta = AGENT_META[event.agent] ?? { label: event.agent, color: "#5a6a7a", icon: "·" };

    const detail = (() => {
        if (event.message) return event.message;
        if (event.slots) return `Found ${event.slots.length} slot${event.slots.length !== 1 ? "s" : ""}`;
        if (event.chars) return `Transcribed ${event.chars.toLocaleString()} chars`;
        if (event.count !== undefined) return `Sent ${event.count} emails`;
        if (event.data) return JSON.stringify(event.data).slice(0, 80) + "…";
        if (event.status) return event.status;
        return "";
    })();

    return (
        <div
            className="event-row"
            style={{
                "--color": meta.color,
                animationDelay: `${index * 0.04}s`,
            } as React.CSSProperties}
        >
            <div className="event-dot" />
            <div className="event-body">
                <div className="event-header">
                    <span className="event-agent" style={{ color: meta.color }}>{meta.label}</span>
                    {event.status && <span className="event-status">{event.status}</span>}
                </div>
                {detail && <p className="event-detail">{detail}</p>}
            </div>

            <style>{`
        .event-row {
          display: flex;
          gap: 10px;
          padding: 10px 0;
          border-bottom: 1px solid var(--border);
          animation: fadeSlideIn 0.25s ease both;
        }
        @keyframes fadeSlideIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .event-dot {
          width: 6px; height: 6px;
          border-radius: 50%;
          background: var(--color);
          margin-top: 6px;
          flex-shrink: 0;
          box-shadow: 0 0 8px var(--color);
        }
        .event-body { flex: 1; min-width: 0; }
        .event-header { display: flex; align-items: center; gap: 8px; margin-bottom: 2px; }
        .event-agent { font-size: 12px; font-weight: 600; }
        .event-status {
          font-size: 10px;
          padding: 1px 6px;
          border-radius: 4px;
          background: rgba(255,255,255,0.06);
          color: var(--text-muted);
          font-family: 'JetBrains Mono', monospace;
        }
        .event-detail {
          font-size: 12px;
          color: var(--text-muted);
          line-height: 1.5;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
      `}</style>
        </div>
    );
}

export default function AgentTrace({ events, isStreaming }: { events: AgentEvent[]; isStreaming: boolean }) {
    const bottomRef = useRef<HTMLDivElement>(null);
    const activeAgents = new Set(events.map((e) => e.agent));

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [events]);

    return (
        <div className="trace-panel">
            <div className="trace-header">
                <span>Agent Activity</span>
                {isStreaming && <span className="streaming-badge">● Live</span>}
            </div>

            {/* Agent topology */}
            <div className="topology">
                {Object.entries(AGENT_META).filter(([k]) => k !== "done").map(([key, meta]) => (
                    <AgentNode
                        key={key}
                        active={activeAgents.has(key)}
                        color={meta.color}
                        icon={meta.icon}
                        label={meta.label}
                    />
                ))}
            </div>

            {/* Event log */}
            <div className="event-log">
                {events.length === 0 ? (
                    <div className="empty-trace">
                        <p>Agent trace will appear here</p>
                        <p>as your request is processed.</p>
                    </div>
                ) : (
                    events.map((e, i) => <EventRow key={i} event={e} index={i} />)
                )}
                {isStreaming && (
                    <div className="thinking">
                        <span />
                        <span />
                        <span />
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            <style>{`
        .trace-panel {
          height: 100%;
          display: flex;
          flex-direction: column;
          background: var(--bg2);
        }

        .trace-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
          border-bottom: 1px solid var(--border);
          font-size: 13px;
          font-weight: 600;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.06em;
          flex-shrink: 0;
        }

        .streaming-badge {
          font-size: 11px;
          color: var(--accent);
          animation: pulse2 1.5s ease-in-out infinite;
        }

        @keyframes pulse2 { 50% { opacity: 0.4; } }

        .topology {
          display: flex;
          justify-content: space-around;
          padding: 16px 12px;
          border-bottom: 1px solid var(--border);
          flex-shrink: 0;
        }

        .event-log {
          flex: 1;
          overflow-y: auto;
          padding: 0 16px;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }

        .empty-trace {
          padding: 40px 0;
          text-align: center;
          font-size: 13px;
          color: var(--text-dim);
          line-height: 1.8;
        }

        .thinking {
          display: flex;
          gap: 4px;
          padding: 12px 0;
          align-items: center;
        }

        .thinking span {
          width: 5px; height: 5px;
          border-radius: 50%;
          background: var(--text-dim);
          animation: bounce 1.2s ease-in-out infinite;
        }

        .thinking span:nth-child(2) { animation-delay: 0.15s; }
        .thinking span:nth-child(3) { animation-delay: 0.3s; }

        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
          40% { transform: translateY(-5px); opacity: 1; }
        }
      `}</style>
        </div>
    );
}