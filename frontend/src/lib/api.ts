export interface AgentEvent {
    agent: string;
    status: string;
    message?: string;
    slots?: any[];
    summary?: any;
}

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "https://meridian-api-845410043165.us-central1.run.app";

export function streamSchedule(
    data: { message: string; audio_file?: string },
    onEvent: (event: AgentEvent) => void,
    onError: () => void
) {
    const controller = new AbortController();
    const baseUrl = BACKEND_URL;

    fetch(`${baseUrl}/api/v1/schedule?demo=true`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        signal: controller.signal,
    })
        .then(async (response) => {
            if (!response.ok) {
                console.error("Stream Error:", response.status);
                onError();
                return;
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            if (!reader) return;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        try {
                            const event = JSON.parse(line.replace("data: ", ""));
                            onEvent(event);
                        } catch (e) {
                            console.error("Parse error", e);
                        }
                    }
                }
            }
        })
        .catch((err) => {
            if (err.name !== "AbortError") {
                console.error("Fetch error", err);
                onError();
            }
        });

    return { abort: () => controller.abort() };
}

export async function confirmSlot(slot: { start: string; end: string }, title: string) {
    const baseUrl = BACKEND_URL;

    const response = await fetch(`${baseUrl}/api/v1/calendar/confirm?demo=true`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            slot,
            title,
            attendees: ["user@example.com"]
        }),
    });

    if (!response.ok) throw new Error("Failed to confirm slot");
    return await response.json();
}

export async function getSummaries() {
    const response = await fetch(`${BACKEND_URL}/api/v1/summaries?demo=true`);
    if (!response.ok) throw new Error("Failed to fetch summaries");
    return await response.json();
}

export async function getEvents() {
    const response = await fetch(`${BACKEND_URL}/api/v1/events?demo=true`);
    if (!response.ok) throw new Error("Failed to fetch events");
    return await response.json();
}