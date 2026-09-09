# Dailies

### Autonomous release investigation for streaming teams.

Dailies is an AI agent that monitors the first 72 hours of a movie release, detects unusual performance, investigates what is happening, tests competing explanations against real data, and produces an evidence-backed release briefing.

Built for the **Agentic Cinema Hackathon**, ClickHouse Track.

> **Deterministic code decides what is unusual. Gemini investigates why. ClickHouse provides the evidence.**

---

## The problem

The first few days of a release matter.

When completion drops, viewing volume spikes, or a problem appears in one region or device type, a distribution team needs to answer:

**What changed?**

**Where is it happening?**

**Why might it be happening?**

**Do the data actually support that explanation?**

Normally, answering those questions means manually digging through dashboards and running SQL queries.

Dailies turns that investigation into an autonomous workflow.

---

## How Dailies works

Dailies follows a controlled investigation pipeline:

```text
┌──────────────┐
│   OBSERVE    │
│              │
│ Deterministic│
│ anomaly      │
│ detection    │
└──────┬───────┘
       ↓
┌──────────────┐
│ INVESTIGATE  │
│              │
│ Gemini runs  │
│ exploratory │
│ SQL queries  │
└──────┬───────┘
       ↓
┌──────────────┐
│ HYPOTHESIZE  │
│              │
│ Generate     │
│ competing   │
│ explanations│
└──────┬───────┘
       ↓
┌──────────────┐
│    VERIFY    │
│              │
│ Test each    │
│ hypothesis  │
│ with SQL     │
└──────┬───────┘
       ↓
┌──────────────┐
│   FINDING    │
│              │
│ Deterministic│
│ verdict      │
└──────┬───────┘
       ↓
┌──────────────┐
│    BRIEF     │
│              │
│ Evidence-    │
│ backed       │
│ release      │
│ briefing     │
└──────────────┘
```

The important part is that **Gemini does not get the final word**.

The agent can propose hypotheses and queries, but the controller determines whether a hypothesis is:

* `SUPPORTED`
* `CONTRADICTED`
* `INCONCLUSIVE`

A failed query cannot be treated as evidence.

---

## Why Dailies is different

### 1. Anomaly detection is deterministic

Gemini does not decide whether something is anomalous.

Dailies uses:

```text
anomaly_detection.sql
        +
anomaly_detector.py
        ↓
measured anomaly
```

The system compares observed release behavior against `baseline_pacing` using fixed statistical thresholds.

This keeps the initial signal reproducible.

---

### 2. Gemini investigates instead of guessing

Once an anomaly is detected, Gemini investigates it using ClickHouse.

It can break the anomaly down across dimensions such as:

```text
Region
Device
App version
Playback behavior
Time window
Viewing volume
Completion rate
Buffering
```

The model is not given fake evidence to reason over.

It has to query the actual warehouse.

---

### 3. Hypotheses are tested against data

Dailies does not stop at:

> "It looks like an app version problem."

Instead, the agent proposes competing explanations and creates targeted verification queries.

For example:

```text
Hypothesis A
App version 4.2 is responsible for the completion drop.

Hypothesis B
The problem is isolated to TV devices.

Hypothesis C
The issue is primarily regional.
```

Each hypothesis is tested independently.

---

### 4. Verdicts are controlled by the system

The controller evaluates the actual query execution and result.

```text
SUPPORTED
    ↓
Evidence supports the hypothesis.

CONTRADICTED
    ↓
Evidence argues against the hypothesis.

INCONCLUSIVE
    ↓
The evidence is insufficient or the verification query failed.
```

This matters because an LLM saying something is true does not make it true.

---

### 5. Every claim has an evidence trail

The final release brief is validated against the evidence log.

Dailies checks that:

* citations actually exist
* citations point to successful queries
* failed queries cannot be cited as evidence
* causal language requires a verified finding
* claims can be traced back to ClickHouse results

The result is not just an AI-generated explanation.

It is an explanation with an audit trail.

---

# Demo

The bundled dataset contains a synthetic release called:

## Orbital Ash

Its first 72 hours contain two deliberately seeded anomalies.

### LATAM completion drop

During hours 6–9:

```text
Completion
68%  →  ~39%
```

The drop is concentrated among:

* TV devices
* app version 4.2
* sessions with unusually high buffering

Dailies detects the anomaly, investigates the dimensions involved, generates competing explanations, and verifies them against ClickHouse.

### APAC viewing surge

During hours 8–11:

```text
Viewing volume
~2× baseline
```

The increase is concentrated in:

* mobile traffic
* TV traffic

Dailies investigates this independently and produces a second evidence-backed finding.

---

# Evidence Explorer

The investigation does not disappear into a black box.

Dailies exposes the evidence behind the agent's reasoning.

For every investigation, the team can inspect:

```text
Anomaly
   ↓
Investigation query
   ↓
Query result
   ↓
Hypothesis
   ↓
Verification query
   ↓
Verification result
   ↓
Final finding
   ↓
Release brief citation
```

This makes the agent's reasoning inspectable from end to end.

---

# Architecture

```text
                         ┌──────────────────┐
                         │    Next.js UI    │
                         │                  │
                         │ Release Overview │
                         │ Investigation    │
                         │ Evidence Explorer│
                         │ Release Brief    │
                         └────────┬─────────┘
                                  │
                                  │ SSE / HTTP
                                  ↓
                         ┌──────────────────┐
                         │     FastAPI      │
                         │                  │
                         │ Investigation API│
                         │ Evidence API     │
                         │ Brief API        │
                         └────────┬─────────┘
                                  │
                                  ↓
                         ┌──────────────────┐
                         │   Controller     │
                         │                  │
                         │ Deterministic    │
                         │ state machine    │
                         └───────┬──────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ↓                  ↓                  ↓
     ┌────────────────┐ ┌────────────────┐ ┌────────────────┐
     │ Anomaly        │ │ Gemini         │ │ Evidence       │
     │ Detector       │ │ Reasoners      │ │ Validator      │
     │                │ │                │ │                │
     │ Fixed SQL +    │ │ Investigate    │ │ Citations      │
     │ thresholds     │ │ Hypothesize    │ │ Query status   │
     │                │ │ Verify         │ │ Brief claims   │
     └────────────────┘ └───────┬────────┘ └────────────────┘
                                │
                                ↓
                         ┌──────────────────┐
                         │  SQL Safety      │
                         │                  │
                         │ query_safety.py  │
                         └────────┬─────────┘
                                  │
                                  ↓
                         ┌──────────────────┐
                         │ mcp-clickhouse   │
                         └────────┬─────────┘
                                  │
                                  ↓
                         ┌──────────────────┐
                         │ ClickHouse Cloud │
                         │                  │
                         │ ~18.7M viewing   │
                         │ events           │
                         └──────────────────┘
```

---

# Tech stack

| Layer             | Technology                      |
| ----------------- | ------------------------------- |
| Data warehouse    | ClickHouse Cloud                |
| Data              | ~18.7M synthetic viewing events |
| Database access   | `mcp-clickhouse`                |
| Agent framework   | Google ADK                      |
| LLM               | Gemini                          |
| Backend           | FastAPI                         |
| Real-time updates | Server-Sent Events              |
| Frontend          | Next.js 14                      |
| Frontend language | TypeScript                      |
| Styling           | Tailwind CSS                    |
| Runtime           | Python 3.14 + Node.js           |

The project follows the hackathon requirement to use Google's agent tooling. Gemini is accessed through Google ADK.

No LangChain or alternative agent framework is used.

---

# Repository structure

```text
dailies/
│
├── clickhouse/
│   └── schema, baseline pacing and anomaly SQL
│
├── data-generator/
│   └── synthetic dataset generation and loading
│
├── agent/
│   ├── anomaly_detector.py
│   │   └── Deterministic anomaly detection
│   │
│   ├── query_safety.py
│   │   └── Independent SQL safety layer
│   │
│   ├── mcp_client.py
│   │   └── ClickHouse MCP configuration
│   │
│   ├── tool_reasoner.py
│   │   └── Investigation and verification agents
│   │
│   ├── pure_reasoner.py
│   │   └── Hypothesis and briefing agents
│   │
│   ├── evidence.py
│   │   └── Evidence log and citation validation
│   │
│   └── controller.py
│       └── Deterministic investigation state machine
│
├── api/
│   └── FastAPI backend
│
└── web/
    └── Next.js frontend
```

---

# Running locally

## 1. Configure credentials

Copy the example environment file:

```bash
cp .env.example .env
```

Then configure:

```env
CLICKHOUSE_HOST=<your-instance>.clickhouse.cloud
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=<your-password>

GOOGLE_API_KEY=<your-Google-AI-Studio-key>

GEMINI_MODEL=gemini-3.5-flash-lite
```

Do not include a port suffix in `CLICKHOUSE_HOST`.

---

## 2. Install Python dependencies

From the project root:

```bash
pip install -r requirements.txt
```

The `mcp` and `fastmcp` versions are pinned because the agent stack depends on compatible versions.

Install the complete requirements file rather than resolving packages individually.

---

## 3. Generate and load the dataset

```bash
cd data-generator

python generate.py
python load_clickhouse.py
```

The loader is resumable.

This creates the synthetic viewing dataset used by the demo.

---

## 4. Start the backend

```bash
cd api

uvicorn main:app --reload --port 8000
```

The API will run at:

```text
http://localhost:8000
```

---

## 5. Start the frontend

```bash
cd web

cp .env.local.example .env.local

npm install
npm run dev
```

Then open:

```text
http://localhost:3000
```

Start an investigation and watch the agent work through the pipeline in real time.

---

# Safety and reliability

Dailies treats the LLM as a reasoning component, not an authority.

### SQL safety

`query_safety.py` provides an independent safety layer around the ClickHouse MCP interface.

The agent cannot simply execute arbitrary destructive SQL.

### Deterministic anomaly detection

Anomalies originate from SQL and fixed statistical thresholds rather than model intuition.

### Deterministic verdicts

The controller decides whether a hypothesis is supported, contradicted, or inconclusive based on actual query execution and evidence.

### Evidence validation

`validate_brief()` checks the final briefing before it reaches the UI.

A citation to a failed query is rejected.

Unsupported causal claims are rejected.

Missing evidence is not silently converted into certainty.

---

# Design principle

Dailies follows one simple rule:

> **The model can investigate the evidence. It cannot manufacture the evidence.**

That separation is intentional.

Deterministic systems handle:

```text
Anomaly detection
Query execution status
Evidence tracking
Verdict logic
Citation validation
```

Gemini handles:

```text
Investigation strategy
Query selection
Pattern interpretation
Hypothesis generation
Evidence explanation
Brief generation
```

This gives Dailies the flexibility of an agent without handing the truth function to an LLM.

---

# Known limitations

The current demo is intentionally focused.

* `orbital_ash` is the only fully investigable release in the bundled dataset.
* Comparable titles in `baseline_pacing` provide historical baseline data but are not independently investigable releases.
* The Evidence Explorer contains an Alerts concept that does not yet have a dedicated backing data model.
* `KEY_METRICS` and `NOTABLE_PATTERN` are currently prompt-level structured-output requests. The UI falls back to prose when Gemini does not provide them.

---

# What's next

Dailies could be extended with:

* multiple live releases
* historical release comparison
* persistent alert management
* automated Slack/email release alerts
* richer playback-quality signals
* real production streaming data
* investigation replay
* team annotations
* longer-term release health monitoring

The core architecture is already designed around evidence rather than generated answers, so these additions do not require turning the system into a chatbot.

---

# License

MIT
