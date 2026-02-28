import os
from dotenv import load_dotenv

load_dotenv()

COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")

MAX_PAGES_PER_SITE = 200
MAX_PAGES_TO_FETCH = 8
MAX_CODE_RETRIES = 2
