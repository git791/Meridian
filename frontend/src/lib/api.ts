export interface AgentEvent {
    agent: string;
    status: string;
    message?: string;
    slots?: any[];
    summary?: any;
}

export function streamSchedule(
    data: { message: string; audio_file?: string },
    onEvent: (event: AgentEvent) => void,
    onError: () => void
) {
    const controller = new AbortController();
    const baseUrl = ""; // Use relative path to hit Next.js rewrite proxy

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

// THE NEW CONFIRM FUNCTION
export async function confirmSlot(slot: { start: string; end: string }, title: string) {
    const baseUrl = ""; // Use relative path to hit Next.js rewrite proxy

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