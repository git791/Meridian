"use client";

import { useState, useEffect } from "react";
import { getEvents } from "@/lib/api";

const HOURS = Array.from({ length: 10 }, (_, i) => i + 8); // 8am–5pm
const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"];

// Static demo data for the initial view
const STATIC_DEMO_EVENTS = [
  { day: 0, start: 9, duration: 1, title: "Design Review", color: "#3de8a0" },
  { day: 0, start: 14, duration: 0.5, title: "1:1 with Alice", color: "#7c6af7" },
  { day: 1, start: 10, duration: 2, title: "Q3 Planning", color: "#4db8ff" },
  { day: 2, start: 9, duration: 1, title: "Standup", color: "#3de8a0" },
  { day: 2, start: 11, duration: 1.5, title: "Client Sync — APAC", color: "#f97316" },
  { day: 3, start: 13, duration: 1, title: "Engineering All-Hands", color: "#ec4899" },
  { day: 4, start: 9, duration: 0.5, title: "Standup", color: "#3de8a0" },
  { day: 4, start: 15, duration: 2, title: "Sprint Retrospective", color: "#7c6af7" },
];

function getWeekDates(weekOffset: number) {
  const now = new Date();
  const day = now.getDay(); // 0=Sun
  const monday = new Date(now);
  // Get THIS week's Monday, but if it's the weekend, default to the UPCOMING Monday
  const diffToMonday = day === 0 ? 1 : day === 6 ? 2 : 1 - day;
  monday.setDate(now.getDate() + diffToMonday + (weekOffset * 7));
  
  return DAYS.map((_, i) => {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    return d;
  });
}

export default function CalendarView() {
  const [weekOffset, setWeekOffset] = useState(0);
  const weekDates = getWeekDates(weekOffset);
  const [now, setNow] = useState(new Date());
  const [dbEvents, setDbEvents] = useState<any[]>([]);

  useEffect(() => {
    // Fetch real data from the database
    const loadRealEvents = async () => {
      try {
        const data = await getEvents();
        // We filter out anything that looks like the demo data 
        // to avoid duplicates if the backend returns them
        setDbEvents(data);
      } catch (err) {
        console.error("Calendar fetch error:", err);
      }
    };

    loadRealEvents();
    const t = setInterval(() => setNow(new Date()), 60_000);
    return () => clearInterval(t);
  }, []);

  // Helper to calculate grid position for database ISO strings
  const getDbEventPosition = (isoString: string) => {
    const d = new Date(isoString);
    
    // Check if the event date falls within the currently displayed weekDates
    const isThisWeek = weekDates.some(wd => 
      wd.getFullYear() === d.getFullYear() && 
      wd.getMonth() === d.getMonth() && 
      wd.getDate() === d.getDate()
    );

    let dayIdx = d.getDay() - 1;
    if (dayIdx < 0) dayIdx = 6; // Handle Sunday  

    if (!isThisWeek) {
      dayIdx = -1; // Hide if not in current week view
    }

    const hour = d.getHours() + (d.getMinutes() / 60);
    // Start time position relative to 8am-5pm window
    const top = ((hour - 8) / 10) * 100;

    // Default duration 1 hour for display if end_time missing
    const height = 10;

    return { dayIdx, top, height };
  };

  const todayIdx = (() => {
    const d = now.getDay();
    return d === 0 || d === 6 ? -1 : d - 1;
  })();

  const nowOffset = (now.getHours() - 8 + now.getMinutes() / 60) / 10 * 100;

  return (
    <div className="cal-page">
      <div className="cal-toolbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div className="week-nav">
            <button className="nav-btn" onClick={() => setWeekOffset(prev => prev - 1)}>←</button>
            <button className="nav-btn" onClick={() => setWeekOffset(0)}>Today</button>
            <button className="nav-btn" onClick={() => setWeekOffset(prev => prev + 1)}>→</button>
          </div>
          <h2 className="cal-week-label">
            {weekDates[0]?.toLocaleDateString("en-US", { month: "long", day: "numeric" })}
            {" — "}
            {weekDates[4]?.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
          </h2>
        </div>
        <div className="cal-legend">
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#3de8a0" }} /> Syncs
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#4db8ff" }} /> Planning
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#f97316" }} /> Client
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#7c6af7" }} /> Confirmed
          </span>
        </div>
      </div>

      <div className="cal-grid">
        {/* Time axis */}
        <div className="time-col">
          <div className="day-header-spacer" />
          {HOURS.map((h) => (
            <div key={h} className="time-slot">
              {h === 12 ? "12pm" : h > 12 ? `${h - 12}pm` : `${h}am`}
            </div>
          ))}
        </div>

        {/* Day columns */}
        {DAYS.map((day, di) => (
          <div key={day} className={`day-col ${di === todayIdx ? "today-col" : ""}`}>
            <div className="day-header">
              <span className="day-name">{day}</span>
              {weekDates[di] && (
                <span className={`day-num ${di === todayIdx ? "today-num" : ""}`}>
                  {weekDates[di].getDate()}
                </span>
              )}
            </div>
            <div className="day-body">
              {HOURS.map((h) => (
                <div key={h} className="hour-cell" />
              ))}

              {/* Now indicator */}
              {di === todayIdx && nowOffset > 0 && nowOffset < 100 && (
                <div className="now-line" style={{ top: `${nowOffset}%` }}>
                  <div className="now-dot" />
                </div>
              )}

              {/* 1. RENDER STATIC DEMO EVENTS (only on current week) */}
              {weekOffset === 0 && STATIC_DEMO_EVENTS.filter((e) => e.day === di).map((ev, ei) => {
                const top = ((ev.start - 8) / 10) * 100;
                const height = (ev.duration / 10) * 100;
                return (
                  <div
                    key={`static-${ei}`}
                    className="cal-event"
                    style={{
                      top: `${top}%`,
                      height: `${height}%`,
                      borderLeft: `3px solid ${ev.color}`,
                      background: `color-mix(in srgb, ${ev.color} 12%, var(--bg3))`,
                    }}
                  >
                    <span className="event-title" style={{ color: ev.color }}>{ev.title}</span>
                    <span className="event-time">
                      {ev.start > 12 ? ev.start - 12 : ev.start}
                      {ev.start >= 12 ? "pm" : "am"}
                    </span>
                  </div>
                );
              })}

              {/* 2. RENDER REAL DATABASE EVENTS */}
              {dbEvents.map((ev, ei) => {
                // Extract positioning from the ISO start time
                const startTime = ev.start?.dateTime || ev.start;
                if (!startTime) return null;

                const { dayIdx, top, height } = getDbEventPosition(startTime);

                // Only render if it matches the current day column
                if (dayIdx !== di || dayIdx === -1) return null;

                return (
                  <div
                    key={`db-${ei}`}
                    className="cal-event"
                    style={{
                      top: `${top}%`,
                      height: `${height}%`,
                      borderLeft: `3px solid #7c6af7`,
                      background: `rgba(124, 106, 247, 0.15)`,
                      zIndex: 10 // Show on top of demo events
                    }}
                  >
                    <span className="event-title" style={{ color: "#7c6af7" }}>{ev.summary || ev.title}</span>
                    <span className="event-time">Confirmed</span>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .cal-page {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          padding: 0;
        }

        .cal-toolbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 28px 16px;
          border-bottom: 1px solid var(--border);
          flex-shrink: 0;
        }

        .cal-week-label {
          font-family: 'DM Serif Display', serif;
          font-size: 18px;
          font-weight: 400;
          color: var(--text-muted);
        }

        .week-nav {
          display: flex;
          gap: 6px;
          align-items: center;
        }

        .nav-btn {
          background: var(--bg2);
          border: 1px solid var(--border);
          color: var(--text);
          border-radius: 6px;
          padding: 6px 12px;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .nav-btn:hover {
          background: var(--bg3);
          border-color: var(--border-bright);
        }

        .cal-legend {
          display: flex;
          gap: 16px;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 5px;
          font-size: 12px;
          color: var(--text-dim);
        }

        .legend-dot {
          width: 8px; height: 8px;
          border-radius: 2px;
        }

        .cal-grid {
          display: flex;
          flex: 1;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: var(--border) transparent;
        }

        .time-col {
          width: 56px;
          flex-shrink: 0;
          border-right: 1px solid var(--border);
        }

        .day-header-spacer { height: 52px; border-bottom: 1px solid var(--border); }

        .time-slot {
          height: 64px;
          border-bottom: 1px solid var(--border);
          padding: 6px 8px 0;
          font-size: 10px;
          color: var(--text-dim);
          font-family: 'JetBrains Mono', monospace;
          text-align: right;
        }

        .day-col {
          flex: 1;
          border-right: 1px solid var(--border);
          display: flex;
          flex-direction: column;
        }

        .day-col:last-child { border-right: none; }

        .today-col { background: rgba(61,232,160,0.02); }

        .day-header {
          height: 52px;
          border-bottom: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 3px;
          flex-shrink: 0;
        }

        .day-name {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--text-dim);
        }

        .day-num {
          font-size: 16px;
          font-weight: 500;
          color: var(--text-muted);
        }

        .today-num {
          width: 28px; height: 28px;
          display: flex; align-items: center; justify-content: center;
          border-radius: 50%;
          background: var(--accent);
          color: #080c10;
          font-weight: 600;
        }

        .day-body {
          flex: 1;
          position: relative;
        }

        .hour-cell {
          height: 64px;
          border-bottom: 1px solid var(--border);
        }

        .now-line {
          position: absolute;
          left: 0; right: 0;
          display: flex;
          align-items: center;
          pointer-events: none;
          z-index: 5;
        }

        .now-line::after {
          content: '';
          flex: 1;
          height: 1px;
          background: var(--accent);
          opacity: 0.6;
        }

        .now-dot {
          width: 8px; height: 8px;
          border-radius: 50%;
          background: var(--accent);
          flex-shrink: 0;
        }

        .cal-event {
          position: absolute;
          left: 4px; right: 4px;
          border-radius: 6px;
          padding: 5px 8px;
          display: flex;
          flex-direction: column;
          justify-content: flex-start;
          overflow: hidden;
          cursor: pointer;
          transition: filter 0.15s;
          z-index: 2;
        }

        .cal-event:hover { filter: brightness(1.15); }

        .event-title {
          font-size: 11px;
          font-weight: 600;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          line-height: 1.3;
        }

        .event-time {
          font-size: 10px;
          color: var(--text-dim);
          font-family: 'JetBrains Mono', monospace;
          margin-top: 2px;
        }
      `}</style>
    </div>
  );
}