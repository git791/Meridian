# Meridian: Multi-Agent Intelligent Meeting Scheduling Platform

Meridian is an intelligent meeting scheduling and lifecycle automation system powered by multi-agent AI and Google Cloud. Instead of forcing users through tedious email threads, manual calendar checks, and forgotten post-meeting notes, Meridian uses autonomous, specialized agents that parse natural language, negotiate free calendar slots, dispatch email invites, transcribe recordings, extract action items, and deliver automated meeting reminders.

---

## Contributors

- **Bibi Sufiya Shariff** (GitHub: [@Suf78](https://github.com/Suf78))
- **Mohammed Ayaan Adil Ahmed** (GitHub: [@git791](https://github.com/git791))

---

## Why We Built This (The Problem and Motivation)

We have all experienced the exhausting routine of organizing a group meeting:
1. **The Email Ping-Pong**: "Are you free Tuesday at 3?" "No, how about Wednesday at 10?" "Wednesday works for me, but what about John?"
2. **Context Switching and Calendar Fatigue**: Opening calendars, checking time zones, inspecting conflicting meetings, generating video call links, and copying attendee addresses manually.
3. **The Meeting Note Black Hole**: After the call ends, discussions vanish into thin air. Key decisions are forgotten, deadlines slip, and no one remembers who owned which deliverable.
4. **Follow-Up Friction**: Manually typing recap emails, chasing people for updates, and sending "1 hour before" reminders takes valuable time away from actual engineering and creative work.

### Why a Single LLM Chatbot is Not Enough
A generic chatbot cannot solve this reliably. If you ask a single prompt to parse dates, query Google Calendar API, resolve time conflicts, send emails, process audio files, and write summaries, it becomes brittle, prone to hallucinations, and slow.

Meridian solves this by using a **Multi-Agent Architecture**. Each agent is an independent expert with a single responsibility (orchestration, calendar logic, communications, transcription, or summarization). They collaborate dynamically, talk to each other through structured schemas, and stream their live thought process back to the user interface in real time.

---

## Core System Architecture

Meridian follows an asynchronous, event-driven architecture centered around a central orchestrator and streaming communication.

```mermaid
flowchart TD
    User([User in Browser]) -->|Natural Language or Audio| Frontend[Next.js 14 Frontend]
    Frontend -->|POST /api/v1/schedule| API[FastAPI Gateway]
    
    subgraph MultiAgentEngine [Multi-Agent Orchestration Engine]
        API --> Orchestrator[Orchestrator Agent - Gemini 1.5 Pro]
        
        Orchestrator -->|Intent: Schedule or Reschedule| CalAgent[Calendar Agent]
        Orchestrator -->|Intent: Send Invites or Reminders| EmailAgent[Email Agent]
        Orchestrator -->|Intent: Transcribe or Summarise| TransAgent[Transcription Agent]
        TransAgent --> SummaryAgent[Summary Agent]
        SummaryAgent --> EmailAgent
    end

    subgraph ExternalServices [External Services & Cloud]
        CalAgent <-->|Free/Busy Query & Event Creation| GCal[Google Calendar API v3]
        EmailAgent -->|Live Inbound/Outbound| Gmail[Gmail API v1]
        EmailAgent -->|Local/Demo Mode| MailHog[MailHog SMTP Server]
        TransAgent <-->|Multimodal Audio Processing| VertexGemini[Vertex AI Gemini 1.5 Pro]
        SummaryAgent <-->|Structured JSON Extraction| VertexGemini
    end

    subgraph DataAndBackground [Persistence & Background Services]
        CalAgent -->|Save Meeting| DB[(PostgreSQL Database)]
        SummaryAgent -->|Save Summaries & Action Items| DB
        Daemon[Background Reminder Daemon] -->|Polls every 60s| DB
        Daemon -->|Triggers 24h & 1h Alerts| EmailAgent
    end

    API -.->|Server-Sent Events SSE| Frontend
```

---

## System Layers

Meridian is structured into six clean, decoupled layers:

### 1. Presentation Layer (Frontend)
- **Framework**: Next.js 14 (App Router), React 18, TypeScript.
- **Styling**: Modern, responsive dark mode glassmorphism interface with custom CSS variables and glowing active agent nodes.
- **Real-Time Streaming**: Built-in Server-Sent Events (SSE) reader (`streamSchedule` in `src/lib/api.ts`) that listens to chunked transfer streams from FastAPI and animates agent activity in real time.
- **Audio Capture**: Direct in-browser audio recording using the HTML5 `MediaRecorder` API, letting users talk to the scheduler or upload meeting recordings directly.
- **Views**:
  - **Schedule View**: Chat prompt, voice recording, live agent execution traces, and interactive slot selection cards.
  - **Calendar View**: Weekly scheduling grid showing confirmed meetings alongside simulated or synced Google Calendar events.
  - **Summaries View**: Meeting minutes archive with searchable executive overviews, key decisions, and interactive action items with owner tags and deadlines.

### 2. API and Routing Layer (FastAPI Gateway)
- **Framework**: FastAPI with Uvicorn.
- **Endpoints**:
  - `POST /api/v1/schedule`: The main SSE streaming pipeline that initializes the orchestrator and yields step-by-step progress events.
  - `POST /api/v1/calendar/confirm`: Confirms a chosen time slot, creates the event, and triggers automatic attendee emails.
  - `GET /api/v1/events`: Retrieves meetings within a time range, blending local PostgreSQL records with live Google Calendar items.
  - `GET /api/v1/summaries`: Returns past meeting summaries and action items.
  - `GET /health` and `GET /api/v1/config`: Operational diagnostics and client configuration handshakes.
- **Middleware**: CORS handling for multiple origins, request latency timing via `X-Process-Time` headers, and global exception logging.

### 3. Orchestration Layer (The Brain)
- **File**: `backend/agents/orchestrator.py`
- **Model**: Google Gemini 1.5 Pro via Google Cloud Vertex AI.
- **Role**: 
  - Analyzes raw user prompts.
  - Uses Pydantic schemas (`IntentSchema`) to enforce strict JSON output with zero markdown or conversational fluff.
  - Classifies user intent into one of six routes: `schedule`, `reschedule`, `transcribe`, `summarise`, `cancel`, or `query`.
  - Extracts meeting metadata: attendee emails, desired durations, natural language preferences (such as "next Tuesday afternoon"), and meeting titles.
  - Coordinates execution order between the subordinate worker agents.

### 4. Autonomous Worker Agents
- **Calendar Agent (`backend/agents/calendar_agent.py`)**:
  - Translates colloquial phrases ("next Thursday after lunch") into ISO 8601 query boundaries with Gemini.
  - Checks attendee busy schedules via Google Calendar `freebusy` queries.
  - Calculates the top 3 conflict-free meeting windows (defaulting to 30 or 60 minute increments).
  - Inserts events into Google Calendar with auto-generated Google Meet conference links.
- **Email Agent (`backend/agents/email_agent.py`)**:
  - Dispatches HTML-formatted calendar invites, cancellations, reminder notices, and meeting summaries.
  - Operates in hybrid mode: sends via official Gmail API when authenticated, or routes through local SMTP (MailHog) for local development and testing.
- **Transcription Agent (`backend/agents/transcription_agent.py`)**:
  - Ingests audio files (such as `.webm` audio recorded directly from the user's browser).
  - Leverages Gemini 1.5 Pro's multimodal audio capabilities to transcribe recordings verbatim with distinct speaker labels.
- **Summary Agent (`backend/agents/summary_agent.py`)**:
  - Reads transcripts and generates a structured breakdown: executive summary, major decisions made, topics covered, follow-up flags, and individual action items with deadlines and assignees.
  - Automatically identifies attendees and delivers personalized emails highlighting the exact tasks assigned to each person.

### 5. Persistence and Background Layer
- **Database**: PostgreSQL 15, managed via SQLAlchemy 2.0 ORM and Alembic schema migrations.
- **Models**:
  - `Meeting`: Stores meeting titles, start/end timestamps, JSON attendee lists, statuses (`scheduled`, `confirmed`), and reminder logs.
  - `MeetingSummary`: Stores meeting minutes, JSON-serialized summary dictionaries, and attendee rosters.
- **Background Daemon (`background_reminder_task`)**:
  - An asynchronous background loop that boots alongside FastAPI in the lifespan handler.
  - Wakes up every 60 seconds to inspect confirmed meetings starting within the next 24 hours.
  - Dispatches automated reminders at the 24-hour mark ("1d") and the 1-hour mark ("1h") to ensure nobody misses a meeting.

### 6. Cloud and Infrastructure Layer
- **Google Cloud Platform (GCP)**: Vertex AI (`gemini-1.5-pro-001`), Secret Manager, Pub/Sub, and Google Cloud Run.
- **Containerization**: Docker multi-stage builds for both backend and frontend.
- **CI/CD**: GitHub Actions automating linting (Ruff), type checking (Mypy), automated testing (Pytest), and deployment to Google Cloud Run.

---

## Detailed Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend Framework** | Next.js 14 (App Router) | Server-rendered and client-rendered interactive web interface |
| **Frontend Language** | TypeScript & React 18 | Type-safe UI components, hooks, and state management |
| **Audio Capture** | Web MediaRecorder API | Native browser recording of meeting discussions and voice prompts |
| **Backend Framework** | FastAPI (Python 3.11) | High-performance asynchronous REST and Server-Sent Events API |
| **ASGI Web Server** | Uvicorn | Production-ready asynchronous Python web server |
| **Generative AI & LLM** | Google Gemini 1.5 Pro | Multi-turn reasoning, intent classification, audio transcription, summarization |
| **AI Cloud Platform** | Google Cloud Vertex AI | Managed enterprise SDK for Gemini models |
| **Database & ORM** | PostgreSQL 15 & SQLAlchemy 2.0 | Relational data persistence with declarative Python models |
| **Schema Migrations** | Alembic | Trackable database schema revisions and upgrades |
| **Validation** | Pydantic v2 & Pydantic-Settings | Request/response validation and environment variable management |
| **External APIs** | Google Calendar API v3 & Gmail API v1 | Calendar event creation, free/busy calculation, email dispatch |
| **Local Mail Testing** | MailHog | SMTP capture server and web UI for verifying outgoing emails locally |
| **Event Messaging** | Google Cloud Pub/Sub | Scalable publish/subscribe pipeline for asynchronous meeting events |
| **Containerization** | Docker & Docker Compose | Multi-container local development and production container packaging |
| **CI/CD & Cloud Hosting** | GitHub Actions & Google Cloud Run | Automated testing, linting, container builds, and serverless deployment |
| **Code Quality** | Pytest, Ruff, Mypy, Codecov | Automated test suite, linter, static type checking, and test coverage |

---

## How It Works (Under the Hood)

### 1. Natural Language Intent Parsing
When you type a message such as:
> *"Book a 45-minute sync with alice@example.com and bob@example.com next Wednesday morning to review design specs"*

The request lands on `POST /api/v1/schedule`. The Orchestrator queries Gemini with a strict schema prompt (`ROUTING_PROMPT`). Gemini returns pure JSON:

```json
{
  "intent": "schedule",
  "attendees": ["alice@example.com", "bob@example.com"],
  "duration_minutes": 45,
  "preferred_time": "next Wednesday morning",
  "meeting_title": "Review design specs",
  "notes": ""
}
```

### 2. Live Agent Trace via Server-Sent Events (SSE)
Instead of making the user wait in silence for 10 seconds, the backend immediately returns a streaming HTTP connection (`text/event-stream`). As each agent works, it emits structured JSON chunks:

```text
data: {"agent": "orchestrator", "status": "thinking", "message": "Parsing your request..."}

data: {"agent": "calendar_agent", "status": "searching", "message": "Checking calendars for 2 attendee(s)..."}

data: {"agent": "calendar_agent", "status": "found", "slots": [{"start": "...", "end": "..."}]}
```

The frontend catches these messages in real time. The agent nodes on the screen light up with distinctive colors and icons (Purple for Orchestrator, Green for Calendar, Blue for Email, Orange for Transcription, Pink for Summary).

### 3. Calendar Conflict Resolution
The Calendar Agent queries the Google Calendar `freebusy` endpoint for all listed attendees across the requested search window. It scans in 30-minute steps, filters out any time block overlapping an existing meeting, and returns up to 3 candidate slots.

### 4. Slot Confirmation and Meeting Dispatch
The user clicks their preferred slot on the UI. The frontend issues a `POST /api/v1/calendar/confirm`:
1. The Calendar Agent calls `events().insert()`, creating the Google Calendar meeting with an automated Google Meet room link.
2. The meeting record is written to PostgreSQL.
3. The Email Agent immediately fires HTML calendar invitations to all attendees.

### 5. Multimodal Audio Transcription and Summarization
If the user uploads an audio recording or uses the mic button to record a standup or lecture:
1. The Transcription Agent passes the audio bytes directly to Gemini 1.5 Pro, generating a transcript with speaker tags.
2. The Summary Agent extracts key decisions, bulleted topic overviews, and action items with deadlines and owners.
3. The Summary Agent records the entry in the database and triggers the Email Agent to send a personalized action-item checklist directly to each attendee's inbox.

### 6. Background Reminder Engine
Inside the FastAPI lifespan context, an asynchronous background task runs continuously:
- Every 60 seconds, it queries PostgreSQL for meetings confirmed within the next 24 hours.
- If a meeting is between 23 and 24 hours away and has not received its 1-day alert, an email reminder is dispatched and recorded in `reminders_sent`.
- If a meeting is within 1 hour, a high-priority 1-hour warning email is sent with the direct meeting link.

---

## User Workflow (Step-by-Step Experience)

Here is what the end-to-end journey looks like for someone using Meridian:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Student
    participant UI as Meridian Frontend
    participant API as FastAPI Backend
    participant Orch as Orchestrator Agent
    participant Cal as Calendar Agent
    participant Email as Email Agent
    participant DB as PostgreSQL DB

    User->>UI: Enters "Schedule sync with bob@work.com tomorrow"
    UI->>API: POST /api/v1/schedule
    API->>Orch: Parse intent & extract entities
    Orch-->>UI: SSE: Status = "Parsing your request"
    Orch->>Cal: Find available slots for bob@work.com
    Cal-->>UI: SSE: Status = "Found 2 available slots"
    UI->>User: Displays interactive slot selection cards
    
    User->>UI: Clicks "Select Slot: 10:00 AM - 11:00 AM"
    UI->>API: POST /api/v1/calendar/confirm
    API->>Cal: Create event in Google Calendar
    Cal->>DB: Save meeting to database
    API->>Email: Send invitation emails to attendees
    Email-->>User: Invite delivered to inboxes
    UI->>User: Shows confirmation checkmark and updates calendar view
```

1. **Ask Meridian**: In the chat box, type what you need in plain English or record your voice.
2. **Watch the Agents Think**: The Agent Trace panel reveals the exact reasoning steps as the Orchestrator, Calendar, and Email agents coordinate.
3. **Pick a Time**: Meridian displays clean candidate cards showing open times where all attendees are free.
4. **Confirm with One Click**: Meridian locks in the slot, updates the PostgreSQL database, and shoots out email invites.
5. **View Your Calendar**: Switch to the **Calendar** tab to inspect your visual weekly timetable.
6. **Upload & Summarize**: After your meeting, head to the **Summaries** tab or upload the audio recording. Meridian transcribes the entire conversation, extracts takeaways, and distributes the action items.

---

## Developer Onboarding Guide

Welcome to the Meridian codebase! If you are stepping in as a new developer or maintainer, this section covers everything you need to know to get running in minutes.

### Repository Layout

```text
Meridian/
├── backend/                        # FastAPI Application
│   ├── agents/                     # Multi-agent implementations
│   │   ├── orchestrator.py         # Gemini intent parser and task distributor
│   │   ├── calendar_agent.py       # Google Calendar query and event creator
│   │   ├── email_agent.py          # Gmail API & SMTP email dispatcher
│   │   ├── transcription_agent.py  # Audio transcription via multimodal Gemini
│   │   └── summary_agent.py        # Executive summaries & action items extraction
│   ├── alembic/                    # Database migrations
│   │   └── versions/               # Individual revision scripts
│   ├── api/                        # REST and SSE route handlers
│   │   ├── auth.py                 # OAuth2 and demo user authentication
│   │   └── routes.py               # API endpoints (/schedule, /events, etc.)
│   ├── core/                       # Core infrastructure settings
│   │   ├── config.py               # Pydantic Settings and environment parsing
│   │   └── pubsub.py               # Google Cloud Pub/Sub event helper
│   ├── models/                     # SQLAlchemy models and Pydantic schemas
│   │   ├── database.py             # Engine, SessionLocal, Meeting & Summary models
│   │   └── schemas.py              # Pydantic schemas for intent and responses
│   ├── scripts/                    # Development utilities
│   │   └── sink_smtp.py            # Raw local TCP SMTP test sink
│   ├── tests/                      # Automated unit and integration tests
│   │   ├── test_calendar_agent.py  # Calendar free/busy and event creation tests
│   │   ├── test_orchestrator.py    # Intent parsing and routing tests
│   │   └── test_summary_agent.py   # Summarization prompt tests
│   ├── alembic.ini                 # Alembic configuration
│   ├── Dockerfile                  # Production container definition for backend
│   ├── main.py                     # App factory, lifespan, CORS, reminder daemon
│   └── requirements.txt            # Python dependencies
│
├── frontend/                       # Next.js 14 Frontend Application
│   ├── public/                     # Static assets
│   ├── src/
│   │   ├── app/
│   │   │   ├── globals.css         # Complete UI design system and themes
│   │   │   ├── layout.tsx          # Root HTML layout and fonts
│   │   │   └── page.tsx            # Main application page and tab navigation
│   │   ├── components/             # Reusable React components
│   │   │   ├── AgentTrace.tsx      # Real-time SSE visual agent status flow
│   │   │   ├── CalendarView.tsx    # Weekly interactive timetable grid
│   │   │   ├── ChatInput.tsx       # Text input, microphone recorder, file attach
│   │   │   └── MeetingSummary.tsx  # Summaries card and action items list
│   │   └── lib/
│   │       └── api.ts              # Fetch wrappers and SSE streaming client
│   ├── Dockerfile                  # Production container definition for frontend
│   ├── package.json                # Node dependencies and scripts
│   └── tsconfig.json               # TypeScript configuration
│
├── infra/                          # Cloud Deployment Configurations
│   ├── cloud-run-service.yaml      # Cloud Run service deployment spec
│   └── cloudbuild.yaml             # Google Cloud Build pipeline
│
├── .github/workflows/
│   └── ci-cd.yml                   # GitHub Actions pipeline (test, build, deploy)
├── docker-compose.yml              # Local multi-service composition
├── .env.example                    # Environment variable template
└── README.md                       # Project documentation
```

---

## Configuration and Environment Variables

Copy `.env.example` to `.env` in the root directory before running the system:

```bash
cp .env.example .env
```

Here is a breakdown of the configuration keys:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `DEMO_MODE` | Set to `true` to run without GCP credentials or live API keys | `true` |
| `GEMINI_API_KEY` | Google Gemini API key (Vertex AI or AI Studio) | `AIzaSy...` |
| `GCP_PROJECT` | Google Cloud project ID (required for Vertex AI in live mode) | `your-gcp-project-id` |
| `REGION` | Cloud deployment region | `asia-southeast1` |
| `VERTEX_LOCATION` | Vertex AI model hosting location | `us-central1` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/meetings` |
| `GOOGLE_CLIENT_ID` | OAuth2 Client ID for Google login | `your-google-client-id` |
| `GOOGLE_CLIENT_SECRET` | OAuth2 Client Secret for Google login | `your-google-client-secret` |
| `NEXT_PUBLIC_API_URL`| Base URL for frontend to communicate with backend | `http://localhost:8080` |
| `SMTP_HOST` | Hostname for email dispatch (use `127.0.0.1` or `mailhog`) | `127.0.0.1` |
| `SMTP_PORT` | SMTP port (MailHog uses `1025`, standard SMTP uses `587`) | `1025` |

---

## Demo Mode vs Live Production Mode

Meridian has a built-in switch that makes local testing seamless:

### Demo Mode (`DEMO_MODE=true`)
- Does not require a Google Cloud billing account or live API tokens.
- Intent classification uses smart keyword heuristics to simulate routing.
- Returns realistic, dynamically generated calendar slots relative to the current time.
- Uses sample meeting audio transcripts and realistic Q3 review summaries.
- Outgoing emails route through MailHog or the local test sink without hitting real inboxes.
- Meetings and summaries are still saved to the local PostgreSQL database.

### Live Mode (`DEMO_MODE=false`)
- Directly invokes Google Cloud Vertex AI (`gemini-1.5-pro-001`) with structured JSON schemas.
- Queries real attendee calendars via the Google Calendar API v3.
- Dispatches live calendar invites and Google Meet links via the Gmail API.
- Transcribes user-recorded `.webm` files using Gemini's native multimodal capabilities.

---

## Quickstart: Running with Docker Compose (Recommended)

The easiest way to spin up the entire stack (FastAPI backend, Next.js frontend, PostgreSQL database, and MailHog email server) is with Docker Compose:

```bash
# 1. Clone the repository
git clone https://github.com/git791/Meridian.git
cd Meridian

# 2. Set up your environment variables
cp .env.example .env

# 3. Spin up all services
docker compose up --build
```

Once running:
- **Frontend**: Open `http://localhost:3000` in your browser.
- **Backend API & Swagger Docs**: Visit `http://localhost:8080/docs`.
- **MailHog Web UI**: Visit `http://localhost:8025` to see all generated emails in real time.
- **Health Check**: Check `http://localhost:8080/health`.

To stop everything:
```bash
docker compose down -v
```

---

## Manual Local Development Setup

If you prefer to run backend and frontend natively on your host machine for rapid debugging:

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL running locally on port 5432 (database named `meetings`)
- (Optional) MailHog running locally or use the included `backend/scripts/sink_smtp.py`

### 2. Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### 3. Frontend Setup
In a new terminal window:
```bash
# Navigate to the frontend directory
cd frontend

# Install Node modules
npm install

# Start the Next.js dev server
npm run dev
```

Visit `http://localhost:3000` to interact with the application.

---

## Database Migrations with Alembic

When you modify SQLAlchemy models in `backend/models/database.py`, manage your migrations using Alembic:

```bash
cd backend

# Create a new revision after updating models
alembic revision --autogenerate -m "describe your schema change"

# Apply pending migrations to the database
alembic upgrade head

# Roll back the most recent migration
alembic downgrade -1
```

*Note: In `main.py`, `Base.metadata.create_all(bind=engine)` runs during startup inside the lifespan handler, ensuring tables are automatically created even if migrations have not been run manually in test environments.*

---

## Testing and Quality Assurance

Meridian includes an automated testing suite using `pytest` and mock configurations to verify agent behavior without requiring live Google Cloud calls.

```bash
cd backend

# Run the test suite with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Run code style checks
ruff check .

# Run static type checking
mypy . --ignore-missing-imports
```

### Key Testing Patterns Used
- **Mocking External APIs**: We patch `googleapiclient.discovery.build` to simulate Google Calendar and Gmail responses.
- **Async Iteration Testing**: The orchestrator and agents use asynchronous generators (`yield`). Tests use an `aiter` utility helper to verify streaming events without network overhead.
- **Gemini Mocking**: We mock `GenerativeModel.generate_content` to return controlled JSON strings to test parsing edge cases.

---

## CI/CD and Google Cloud Deployment

Meridian is equipped with a complete GitHub Actions CI/CD pipeline (`.github/workflows/ci-cd.yml`):

1. **Continuous Integration**:
   - On every pull request or push to `main` and `develop`.
   - Sets up Python 3.11, caches pip packages, runs `ruff` linting, runs `mypy` type checking, and executes `pytest` with a minimum test coverage threshold of 75%.
2. **Continuous Deployment**:
   - Triggers when commits merge into `main`.
   - Authenticates to GCP via service account key.
   - Builds the backend Docker container and pushes to **Google Artifact Registry** (`asia-southeast1-docker.pkg.dev`).
   - Deploys the service to **Google Cloud Run** with auto-scaling (0 to 5 instances, 1 vCPU, 1 GB RAM, 80 concurrency limit).
   - Injects secrets from Google Secret Manager (`GEMINI_API_KEY`, `DB_PASSWORD`).
   - Performs an automated post-deployment health check against the `/health` endpoint.

---

## Architectural Quirks and Gotchas for New Developers

Every real-world project has nuances. Keep these tips in mind when modifying Meridian:

1. **Server-Sent Events (SSE) Flushing**:
   In `backend/agents/calendar_agent.py`, you will notice `await asyncio.sleep(0.1)` calls before intensive work. This gives the event loop time to flush the SSE packet over the socket so the browser updates immediately rather than buffering multiple events together.
2. **Dual-Path Email Logic**:
   The `EmailAgent` checks whether `self.service` (Gmail API) exists. If running locally or without Google OAuth credentials, it gracefully falls back to SMTP (`_send_smtp`). If you do not have MailHog running, you can run `python backend/scripts/sink_smtp.py` to capture emails on port 1025 without crashing.
3. **Database JSON String Columns**:
   Attendees and reminder tags in the `Meeting` table are stored as JSON-encoded text strings (`json.dumps(...)`) for maximum portability across SQLite and PostgreSQL. When querying or editing these fields, remember to parse them using `json.loads()`.
4. **Resilient CORS Config**:
   `backend/core/config.py` allows `CORS_ORIGINS` to be supplied either as a valid JSON list or as a simple comma-separated string. This prevents environment variable parsing bugs between Docker Compose and Google Cloud Run.
5. **Lifespan Task Cancellation**:
   The background reminder task is spawned via `asyncio.create_task` during the FastAPI lifespan startup. Make sure to keep `reminder_task.cancel()` in the shutdown block so background threads do not hang during restarts.

---

## Future Roadmap

Looking to contribute? Here are key features and enhancements ready for implementation:

- [ ] **Multi-Calendar Support**: Add Microsoft Outlook and Apple iCloud calendar integrations.
- [ ] **WhatsApp and Slack Bot Connectors**: Allow users to schedule meetings and receive summary digests directly inside Slack channels or WhatsApp chats.
- [ ] **Live Audio Streaming Transcription**: Stream audio chunks via WebSockets for real-time live captions during ongoing calls.
- [ ] **Conflict Resolution Negotiation**: If no free slots match all attendees, have an agent propose optimal compromise times based on attendee time zones and historical schedule flexibility.
- [ ] **Vector Search on Past Summaries**: Implement embeddings (using Google Vertex AI text-embedding models) stored in pgvector to let users search through past meetings with questions like *"What did we decide about the database migration last month?"*.
