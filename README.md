# llama-lounge-agentic-HACKATHON

# DocAgent — Architecture & Approach

## Problem Statement

Every developer — especially at hackathons — faces the same painful workflow:

1. You have a task: *"Build a service that sends emails and accepts payments"*
2. You need to figure out WHICH tools/APIs to use across multiple platforms
3. You manually read through docs for Composio, CrewAI, Skyfire, etc.
4. You copy-paste relevant sections into a file
5. You feed it to an AI assistant and hope it generates working code

This is slow, error-prone, and doesn't scale. A platform like Composio alone has 980+ toolkits. No human can know what's available across all these doc sites. And no existing AI tool can autonomously navigate multiple documentation sources to build a solution.

**DocAgent solves this: given a task, it autonomously decides which documentation sources to consult, navigates to the right pages across multiple doc sites, understands the tools/APIs/auth flows, and generates production-ready code — exactly like a senior developer would, but in seconds.**

## Our Solution

**DocAgent** is a multi-agent system (CrewAI + Composio) that acts like a senior developer who has read all the docs. You give it a task and a set of documentation sources. It:

1. **Indexes** each doc site's structure (table of contents, not full content)
2. **Reasons** about which docs across which sites are relevant for YOUR task
3. **Fetches** only the right pages from the right sources
4. **Generates** complete, tested, runnable code

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
│  │  │ Agent: Solution Architect                             │  │  │
│  │  │ → Takes user task + cross-platform tool brief         │  │  │
│  │  │ → Designs how to wire the pieces together             │  │  │
│  │  │ → Output: step-by-step implementation plan            │  │  │
│  │  │                                                       │  │  │
│  │  │ Agent: Code Generator                                 │  │  │
│  │  │ → Writes production-ready code combining all tools    │  │  │
│  │  │ → Uses Composio Code Interpreter to validate          │  │  │
│  │  │ → Retries on errors (max 2)                           │  │  │
│  │  │ → Output: complete, runnable script                   │  │  │
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

### Agent 3: Solution Architect
- **Role:** Solution Architect
- **Goal:** Design a clean, minimal implementation plan for the user's task based on the documentation analysis
- **Backstory:** Architect who designs elegant solutions using the least amount of code and the most appropriate APIs
- **Tools:** None (pure reasoning)
- **Output:** Step-by-step implementation plan with specific API calls, imports, and data flow

### Agent 4: Code Generator
- **Role:** Production Code Generator
- **Goal:** Write complete, runnable Python code that accomplishes the user's task
- **Backstory:** Senior engineer who writes clean, production-ready code with proper error handling, imports, and documentation. Never leaves placeholder code — every script must run.
- **Tools:** Composio Code Interpreter (to validate the generated code actually executes)
- **Output:** Complete Python script ready to copy-paste and run

---

## Composio Integration Points

| Component | Composio Toolkit | Purpose |
|-----------|-----------------|---------|
| Doc crawling | **Firecrawl** | Crawl sitemap, fetch individual pages as clean markdown |
| Code validation | **Code Interpreter** | Run generated code in sandbox to verify it works |
| Output delivery | **GitHub** (optional) | Push generated code to user's repo |
| Agent framework | **`composio_crewai`** | Native CrewAI tool integration |

---

## Skyfire Integration

DocAgent is deployed as a **Skyfire seller service**, enabling agent-to-agent commerce:

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
| Tool integrations | **Composio** (`composio_crewai`) | Firecrawl for crawling, Code Interpreter for validation |
| LLM | **Llama 3.3 70B** (via Together AI / Groq) | Fits hackathon theme; OpenAI GPT-4o as fallback |
| Monetization | **Skyfire** seller API | Agent-to-agent payments for doc queries |
| API layer | **FastAPI** | Wraps core engine for Skyfire seller endpoint + programmatic access |
| Human interface | **CLI (Rich)** | Clean terminal UI for demo — no Streamlit |
| Caching | **In-memory dict** | Cache page indexes and fetched pages to avoid re-crawling |

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
│   ├── crew.py              # Code generation crew (Doc Analyst + Architect + Generator)
│   ├── engine.py            # Core engine (orchestrates index → navigate → fetch → generate)
│   └── cache.py             # In-memory cache for indexes and fetched pages
└── config/
    ├── __init__.py
    └── settings.py          # Configuration and environment variables
```
