"use client";

import { useState, useRef, useCallback } from "react";

interface ChatInputProps {
    onSubmit: (message: string, audioFile?: File) => void;
    onStop: () => void;
    isStreaming: boolean;
}

export default function ChatInput({ onSubmit, onStop, isStreaming }: ChatInputProps) {
    const [message, setMessage] = useState("");
    const [isRecording, setIsRecording] = useState(false);
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [recordingSeconds, setRecordingSeconds] = useState(0);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const startRecording = useCallback(async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mr = new MediaRecorder(stream);
            mediaRecorderRef.current = mr;
            chunksRef.current = [];
            setRecordingSeconds(0);

            mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
            mr.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: "audio/webm" });
                const file = new File([blob], "recording.webm", { type: "audio/webm" });
                setAudioFile(file);
                stream.getTracks().forEach((t) => t.stop());
                if (timerRef.current) clearInterval(timerRef.current);
            };

            mr.start();
            setIsRecording(true);
            timerRef.current = setInterval(() => setRecordingSeconds((s) => s + 1), 1000);
        } catch {
            alert("Microphone access denied.");
        }
    }, []);

    const stopRecording = useCallback(() => {
        mediaRecorderRef.current?.stop();
        setIsRecording(false);
        if (timerRef.current) clearInterval(timerRef.current);
    }, []);

    const handleSubmit = () => {
        if (!message.trim() && !audioFile) return;
        onSubmit(message.trim() || "Summarise this meeting recording", audioFile ?? undefined);
        setMessage("");
        setAudioFile(null);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const fmt = (s: number) => `${Math.floor(s / 60).toString().padStart(2, "0")}:${(s % 60).toString().padStart(2, "0")}`;

    return (
        <div className="input-wrapper">
            {audioFile && (
                <div className="audio-badge">
                    <span className="audio-icon">🎙</span>
                    <span>{audioFile.name} · {fmt(recordingSeconds)}</span>
                    <button onClick={() => setAudioFile(null)} className="audio-remove">✕</button>
                </div>
            )}

            <div className="input-box">
                <textarea
                    ref={textareaRef}
                    className="textarea"
                    value={message}
                    onChange={(e) => {
                        setMessage(e.target.value);
                        e.target.style.height = "auto";
                        e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px";
                    }}
                    onKeyDown={handleKeyDown}
                    placeholder="Describe what you need — schedule a meeting, find a time slot, summarise a recording…"
                    rows={2}
                    disabled={isStreaming}
                />

                <div className="input-actions">
                    <div className="input-actions-left">
                        <button
                            className={`mic-btn ${isRecording ? "recording" : ""}`}
                            onClick={isRecording ? stopRecording : startRecording}
                            title={isRecording ? "Stop recording" : "Record meeting audio"}
                        >
                            {isRecording ? (
                                <>
                                    <span className="rec-dot" />
                                    <span className="mono">{fmt(recordingSeconds)}</span>
                                </>
                            ) : (
                                <span>⏺</span>
                            )}
                        </button>

                        <label className="attach-btn" title="Attach audio file">
                            <input
                                type="file"
                                accept="audio/*"
                                style={{ display: "none" }}
                                onChange={(e) => e.target.files?.[0] && setAudioFile(e.target.files[0])}
                            />
                            ⊕
                        </label>
                    </div>

                    {isStreaming ? (
                        <button className="stop-btn" onClick={onStop}>
                            ◼ Stop
                        </button>
                    ) : (
                        <button
                            className="send-btn"
                            onClick={handleSubmit}
                            disabled={!message.trim() && !audioFile}
                        >
                            Send ↵
                        </button>
                    )}
                </div>
            </div>


        </div>
    );
}