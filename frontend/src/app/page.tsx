"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import ChatInput from "@/components/ChatInput";
import AgentTrace from "@/components/AgentTrace";
import CalendarView from "@/components/CalendarView";
import MeetingSummary from "@/components/MeetingSummary";
import { streamSchedule, confirmSlot, AgentEvent } from "@/lib/api";

type Tab = "schedule" | "calendar" | "summaries";

export default function Home() {
    const [tab, setTab] = useState<Tab>("schedule");
    const [events, setEvents] = useState<AgentEvent[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [slots, setSlots] = useState<{ start: string; end: string }[]>([]);
    const [greeting, setGreeting] = useState("");

    // NEW: State for the summaries list
    const [dbSummaries, setDbSummaries] = useState<any[]>([]);
    const [selectedSummary, setSelectedSummary] = useState<Record<string, unknown> | null>(null);

    useEffect(() => {
        const h = new Date().getHours();
        if (h < 12) setGreeting("Good morning");
        else if (h < 17) setGreeting("Good afternoon");
        else setGreeting("Good evening");

        // Fetch existing summaries on load
        fetchSummaries();
    }, []);

    // Function to pull real data from the DB
    const fetchSummaries = async () => {
        try {
            const res = await fetch('/api/v1/summaries?demo=true');
            const data = await res.json();
            setDbSummaries(data);
            if (data.length > 0) {
                // Default the summary view to the latest one
                setSelectedSummary(data[0]);
            }
        } catch (err) {
            console.error("Failed to fetch summaries", err);
        }
    };

    const abortRef = useRef<(() => void) | null>(null);

    const handleSubmit = useCallback(async (message: string, audioFile?: File) => {
        setIsStreaming(true);
        setEvents([]);
        setSlots([]);

        const { abort } = streamSchedule(
            { message, audio_file: audioFile?.name },
            (event) => {
                setEvents((prev) => [...prev, event]);
                if (event.slots) setSlots(event.slots);
                // If a summary comes through the stream, update the view
                if (event.summary) {
                    setSelectedSummary(event.summary as Record<string, unknown>);
                    fetchSummaries(); // Refresh the list
                }
                if (event.agent === "done") setIsStreaming(false);
            },
            () => setIsStreaming(false)
        );
        abortRef.current = abort;
    }, []);

    const handleConfirm = async (slot: { start: string; end: string }) => {
        try {
            await confirmSlot(slot, "Team Sync");
            alert("Meeting Confirmed & Saved to Database!");
            setSlots([]);
            fetchSummaries(); // Refresh the summaries list after confirming
        } catch (err) {
            console.error(err);
            alert("Database Error: Is the backend running?");
        }
    };

    const handleStop = () => {
        abortRef.current?.();
        setIsStreaming(false);
    };

    return (
        <div className="app-shell">
            <aside className="sidebar">
                <div className="logo">
                    <span className="logo-icon">◈</span>
                    <span className="logo-text">Meridian</span>
                </div>
                <nav className="nav">
                    {(["schedule", "calendar", "summaries"] as Tab[]).map((t) => (
                        <button key={t} className={`nav-item ${tab === t ? "active" : ""}`} onClick={() => setTab(t)}>
                            <span>{t.charAt(0).toUpperCase() + t.slice(1)}</span>
                        </button>
                    ))}
                </nav>
            </aside>

            <main className="main">
                <header className="topbar">
                    <p className="greeting">{greeting}</p>
                    <h1 className="page-title">
                        {tab === "schedule" && "Smart Scheduler"}
                        {tab === "calendar" && "Team Calendar"}
                        {tab === "summaries" && "Meeting Insights"}
                    </h1>
                </header>

                {tab === "schedule" && (
                    <div className="schedule-layout">
                        <div className="chat-col">
                            <div className="examples">
                                {[
                                    "Schedule a 1-hour sync with alice@test.com next Tuesday",
                                    "Find a 30-min slot for a design review this week",
                                    "Summarise the last meeting and email action items",
                                ].map((ex) => (
                                    <button
                                        key={ex}
                                        className="example-chip"
                                        onClick={() => handleSubmit(ex)}
                                    >
                                        {ex}
                                    </button>
                                ))}
                            </div>

                            <ChatInput onSubmit={handleSubmit} onStop={handleStop} isStreaming={isStreaming} />

                            {slots.length > 0 && (
                                <div className="slots">
                                    <p className="slots-label">Available slots found</p>
                                    {slots.map((s, i) => (
                                        <button key={i} className="slot-card" onClick={() => handleConfirm(s)}>
                                            <span className="slot-index">{i + 1}</span>
                                            <div>
                                                <p className="slot-date">{new Date(s.start).toLocaleDateString()}</p>
                                                <p className="slot-time">
                                                    {new Date(s.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} →
                                                    {new Date(s.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                </p>
                                            </div>
                                            <span className="slot-confirm">Confirm →</span>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="trace-col">
                            <AgentTrace events={events} isStreaming={isStreaming} />
                        </div>
                    </div>
                )}

                {tab === "calendar" && <CalendarView />}

                {tab === "summaries" && (
                    <div className="summary-list">
                        {dbSummaries.length > 0 ? (
                            <MeetingSummary summary={selectedSummary || dbSummaries[0]} />
                        ) : (
                            <div className="no-data">No meetings found in database.</div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}