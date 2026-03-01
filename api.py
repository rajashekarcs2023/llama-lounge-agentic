"""DocAgent — FastAPI Backend API.

Run with: uvicorn api:app --reload --port 8000
"""

import os
import asyncio

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.cache import cache
from src.indexer import index_site, fetch_pages
from src.navigator import navigate
from src.crew import generate_code
from src.validator import validate_and_fix

app = FastAPI(title="DocAgent API", description="The developer that reads ALL the docs.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/index")
async def api_index(request: Request):
    """Index a documentation site via llms.txt."""
    body = await request.json()
    url = body.get("url", "").strip().rstrip("/")
    if not url:
        return JSONResponse({"error": "url is required"}, status_code=400)
    if not url.startswith("http"):
        url = "https://" + url

    loop = asyncio.get_event_loop()
    pages = await loop.run_in_executor(None, index_site, url)
    return {
        "status": "ok",
        "site": url,
        "pages_indexed": len(pages),
        "pages": [
            {"title": p["title"], "section": p.get("section", ""), "url": p["url"]}
            for p in pages[:50]
        ],
    }


@app.get("/api/status")
async def api_status():
    """Show indexed sources and stats."""
    stats = cache.stats()
    indexes = cache.get_all_indexes()
    sources = []
    for site, pages in indexes.items():
        sections = sorted(set(p.get("section", "General") for p in pages))
        sources.append({"site": site, "pages": len(pages), "sections": sections[:10]})
    return {"stats": stats, "sources": sources}


@app.get("/api/pages")
async def api_pages():
    """Return all indexed pages grouped by site — for demo/inspection."""
    indexes = cache.get_all_indexes()
    result = {}
    for site, pages in indexes.items():
        result[site] = [
            {"title": p["title"], "url": p["url"], "section": p.get("section", "")}
            for p in pages
        ]
    return {"sites": result, "total": sum(len(p) for p in result.values())}


@app.post("/api/generate")
async def api_generate(request: Request):
    """Full pipeline: navigate docs + generate code for a task.
    
    Also serves as the Skyfire seller endpoint.
    """
    body = await request.json()
    task = body.get("task", "").strip()
    doc_urls = body.get("doc_urls", [])

    if not task:
        return JSONResponse({"error": "task is required"}, status_code=400)

    # Index any provided URLs that aren't cached
    for url in doc_urls:
        url = url.strip().rstrip("/")
        if not url.startswith("http"):
            url = "https://" + url
        if not cache.has_index(url):
            await asyncio.get_event_loop().run_in_executor(None, index_site, url)

    unified_index = cache.get_unified_index()
    if not unified_index:
        return JSONResponse({"error": "No doc sites indexed. Index at least one site first."}, status_code=400)

    # Phase 1: Navigate
    loop = asyncio.get_event_loop()
    selected_urls = await loop.run_in_executor(None, navigate, task, unified_index)
    if not selected_urls:
        return JSONResponse({"error": "Navigator could not find relevant pages."}, status_code=500)

    # Phase 2: Fetch
    doc_contents = await loop.run_in_executor(None, fetch_pages, selected_urls)

    # Phase 3: Generate code
    code = await loop.run_in_executor(None, generate_code, task, doc_contents)

    # Phase 4: Validate + Retry
    validation_log = []
    if code:
        final_code, validation_log = await loop.run_in_executor(
            None, validate_and_fix, code, task, doc_contents, generate_code
        )
    else:
        final_code = ""

    # Save to file
    if final_code:
        with open("generated_code.py", "w") as f:
            f.write(final_code)

    return {
        "status": "ok",
        "task": task,
        "pages_used": selected_urls,
        "code": final_code or "",
        "validation": validation_log,
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "DocAgent"}
