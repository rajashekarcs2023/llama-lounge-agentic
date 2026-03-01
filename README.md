# llama-lounge-agentic-HACKATHON

# DocAgent — Architecture & Approach

## Problem Statement

Coding agents like Claude Code, Cursor, Windsurf, and Copilot write great code but hallucinate APIs. Ask one to "build a CrewAI agent with Composio Slack tools" and it uses method names that don't exist, import paths that changed months ago, and authentication flows it invented. Why? Stale training data, not actual docs.

No existing AI tool can autonomously navigate multiple documentation sources, cross-reference them, and generate verified code.

**DocAgent is the missing layer between coding agents and documentation.** Given a task, it autonomously indexes doc sites via `llms.txt`, reasons about which pages across multiple sources are relevant, fetches only those pages, generates code using real API patterns, and validates the output in a sandbox. It reads the actual docs so your AI doesn't have to hallucinate.

## Our Solution

**DocAgent** is a multi-agent system (CrewAI + Composio) that acts like a senior developer who has read all the docs. You give it a task and a set of documentation sources. It:

1. **Indexes** each doc site via `llms.txt` (lightweight table of contents, not full content)
2. **Navigates** using an AI agent that reasons across ALL indexed sites to pick relevant pages
3. **Fetches** only the right pages from the right sources as clean markdown
4. **Generates** complete, production-ready code using a multi-agent crew
5. **Validates** the generated code in a Composio sandbox and auto-retries on errors

### Key Innovation: Agentic Retrieval Across Multiple Sources (Not RAG)

Traditional RAG crawls everything into one vector store and does dumb similarity search. That fails when:
- You need docs from MULTIPLE sites (Composio + CrewAI + Skyfire)
- The relevant info is spread across different sources
- You need the agent to DECIDE which source has what

**DocAgent uses agentic retrieval:**
1. Maintain a lightweight index of multiple doc sites (just page titles + descriptions)
2. When a task comes in, the **Navigator Agent reasons** across ALL indexed sites to pick the 3-8 most relevant pages — from ANY source
3. Fetch only those pages on demand
4. Feed precise, cross-source context to the code generation crew

The agent IS the retrieval system. It thinks like a developer: *"For this task I need the Composio Gmail toolkit docs, the CrewAI agent setup docs, and the Skyfire seller API docs."*

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          DocAgent                                 │
│                                                                   │
│  INTERFACES                                                       │
│  ┌──────────────┐    ┌──────────────────┐                        │
│  │  CLI          │    │  FastAPI + Skyfire │                       │
│  │  (Human)      │    │  (Agent-to-Agent)  │                      │
│  └──────┬───────┘    └────────┬──────────┘                       │
│         └─────────┬───────────┘                                   │
│                   ▼                                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                     CORE ENGINE                             │  │
│  │                                                             │  │
│  │  Phase 1: INDEX (one-time per doc site, cached)             │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Multi-Site Indexer                                    │  │  │
│  │  │ • Takes list of doc URLs (Composio, CrewAI, Skyfire)  │  │  │
│  │  │ • Firecrawl (via Composio) crawls each site's index   │  │  │
│  │  │ • Extracts (source, url, title, desc) for all pages   │  │  │
│  │  │ • Builds unified MULTI-SOURCE page index              │  │  │
│  │  │ • Cached — never re-crawls unless asked               │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │  Phase 2: NAVIGATE (per user task)                          │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Navigator Agent (CrewAI)                              │  │  │
│  │  │ • Receives: user task + unified page index            │  │  │
│  │  │ • Reasons ACROSS all indexed sites                    │  │  │
│  │  │ • Decides: "I need Composio Slack docs + CrewAI       │  │  │
│  │  │   agent docs + Skyfire seller docs for this task"     │  │  │
│  │  │ • Selects 3-8 pages from ANY source                   │  │  │
│  │  └────────────────────────┬─────────────────────────────┘  │  │
│  │                           ▼                                 │  │
│  │  Phase 3: FETCH (targeted, on-demand)                       │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Page Fetcher                                          │  │  │
│  │  │ • Firecrawl (via Composio) fetches selected pages     │  │  │
│  │  │ • Returns clean markdown from each source             │  │  │
│  │  │ • Caches fetched pages for reuse                      │  │  │
│  │  └────────────────────────┬─────────────────────────────┘  │  │
│  │                           ▼                                 │  │
│  │  Phase 4: GENERATE (multi-agent code crew)                  │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Code Generation Crew (CrewAI)                         │  │  │
│  │  │                                                       │  │  │
│  │  │ Agent: Doc Analyst                                    │  │  │
│  │  │ → Reads fetched pages from MULTIPLE doc sources       │  │  │
│  │  │ → Understands how tools/APIs from different           │  │  │
│  │  │   platforms connect together                          │  │  │
│  │  │ → Output: unified tool brief (cross-platform)         │  │  │
│  │  │                                                       │  │  │
│  │  │ Agent: Code Generator                                 │  │  │
│  │  │ → Writes production-ready code combining all tools    │  │  │
│  │  │ → Output: complete, runnable script                   │  │  │
│  │  └────────────────────────┬─────────────────────────────┘  │  │
│  │                           ▼                                 │  │
│  │  Phase 5: VALIDATE (sandbox + auto-retry)                   │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Code Validator                                        │  │  │
│  │  │ • Runs code in Composio remote sandbox                │  │  │
│  │  │ • Checks for syntax, import, and runtime errors       │  │  │
│  │  │ • If errors found: re-generates with error context    │  │  │
│  │  │ • Auto-retries up to 2 times                          │  │  │
│  │  │ • Falls back to local syntax check if sandbox unavail │  │  │
│  │  │ • Output: validated, runnable code                    │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Agent Design (CrewAI)

### Agent 1: Navigator Agent
- **Role:** Multi-Source Documentation Navigator
- **Goal:** Given a user's task and a unified page index spanning multiple doc sites, identify the 3-8 most relevant pages to fetch — from ANY source
- **Backstory:** Expert technical researcher who understands how different tools and platforms connect. Can scan tables of contents across Composio, CrewAI, Skyfire, and any other indexed doc site, and pinpoint exactly which combination of pages from which sources will provide the information needed.
- **Tools:** None (pure reasoning over the unified page index passed as context)
- **Output:** List of (source, url, reason) tuples explaining which pages from which doc sites to fetch and why

### Agent 2: Doc Analyst
- **Role:** Technical Documentation Analyst
- **Goal:** Extract structured, actionable information from raw documentation pages
- **Backstory:** Senior developer who reads documentation and distills it into clear API references, authentication flows, required parameters, and working code patterns
- **Tools:** None (reasoning over fetched page content)
- **Output:** Structured brief containing: available tools/APIs, authentication method, required parameters, code examples, common pitfalls

### Agent 3: Code Generator
- **Role:** Production Code Generator
- **Goal:** Write complete, runnable Python code that accomplishes the user's task
- **Backstory:** Senior engineer who writes clean, production-ready code with proper error handling, imports, and documentation. Never leaves placeholder code.
- **Tools:** None (uses Doc Analyst brief as context)
- **Output:** Complete Python script ready to copy-paste and run

### Agent 4: Code Validator
- **Role:** Code Validator
- **Goal:** Run generated code in a Composio remote sandbox to verify it has no syntax, import, or runtime errors
- **Backstory:** QA engineer who validates Python scripts before deployment
- **Tools:** Composio Remote Bash Tool (sandbox execution)
- **Output:** Validation result (VALID or ERROR with details). If invalid, triggers auto-retry with error context

---

## Composio Integration Points

| Component | Composio Toolkit | Purpose |
|-----------|-----------------|---------|
| Doc indexing | **llms.txt** | Index doc sites via the llms.txt standard for LLM consumption |
| Code validation | **Remote Bash Tool** | Run generated code in Composio sandbox to verify it works |
| Output delivery | **GitHub** (optional) | Push generated code to user's repo |
| Agent framework | **`composio_crewai`** | Native CrewAI tool integration |

---

## Skyfire Integration

DocAgent is deployed as a **Skyfire seller service**, enabling agent-to-agent commerce:

https://app.skyfire.xyz/seller/e3d4c13b-29c1-4927-9a63-c4ac387d7c97/services

Seller ServiceID : 04133e15-9573-490c-915a-adc935145a13

```
POST /api/generate
Headers:
  Authorization: Bearer <skyfire_payment_token>
Body:
  {
    "doc_url": "https://docs.composio.dev",
    "task": "Send a Slack message using Composio's Slack toolkit"
  }
Response:
  {
    "code": "from composio import Composio...",
    "explanation": "This script authenticates with...",
    "pages_referenced": ["https://docs.composio.dev/toolkits/slack", ...]
  }
```

**Pricing:** $0.05-0.10 per query. Other AI agents can autonomously call DocAgent to learn how to use any tool.

---

## Tech Stack

| Component | Technology | Reason |
|-----------|-----------|--------|
| Agent orchestration | **CrewAI** | Multi-agent crew with defined roles and task delegation |
| Tool integrations | **Composio** (`composio_crewai`) | Native CrewAI tool integration |
| LLM | **OpenAI GPT-4o** | Powers all agents (navigator, doc analyst, code generator) |
| Doc indexing | **llms.txt** | Lightweight doc site indexing via the llms.txt standard |
| API layer | **FastAPI** | Backend API + Skyfire seller endpoint |
| Frontend | **Next.js + TypeScript + Tailwind** | Modern dark-theme web UI |
| CLI | **Rich** | Terminal interface for local usage |
| Caching | **In-memory dict** | Cache page indexes and fetched pages |

---

## Project Structure

```
llama-lounge-agentic/
├── ARCHITECTURE.md          # This file
├── README.md                # Project overview + setup instructions
├── requirements.txt         # Python dependencies
├── .env.example             # Required API keys template
├── main.py                  # CLI entry point (Rich terminal UI)
├── api.py                   # FastAPI server (Skyfire seller endpoint)
├── src/
│   ├── __init__.py
│   ├── indexer.py           # Multi-site sitemap indexer (Firecrawl via Composio)
│   ├── navigator.py         # Navigator agent (cross-source page selection)
│   ├── crew.py              # Code generation crew (Doc Analyst + Code Generator)
│   ├── validator.py         # Code validator (Composio sandbox + auto-retry loop)
│   ├── engine.py            # Core engine (orchestrates index → navigate → fetch → generate → validate)
│   └── cache.py             # In-memory cache for indexes and fetched pages
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration and environment variables
└── frontend/                # Next.js + TypeScript web UI
    ├── app/page.tsx          # Main DocAgent interface
    ├── next.config.ts        # API proxy to FastAPI backend
    └── package.json
```
