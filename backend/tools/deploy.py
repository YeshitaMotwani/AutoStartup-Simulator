"""
Landing page "deployment" - writes the generated HTML to disk under data/landing_pages/.
Owner: Lakshit

Kept intentionally local/free per project scope (no paid hosting). Swapping in a real
free-tier host (Vercel/Netlify) later just means replacing save_landing_page's body —
callers only depend on it returning a path/URL string.
"""
import re
from pathlib import Path
import os
import zipfile
import io
import requests
from backend.utils.logger import get_logger
from dotenv import load_dotenv
load_dotenv()

logger = get_logger(__name__)

NETLIFY_API = "https://api.netlify.com/api/v1"

OUTPUT_DIR = Path("data/landing_pages")


def _slugify(idea: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", idea.lower()).strip("-")
    return slug[:60] or "landing-page"


def save_landing_page(idea: str, html: str) -> str:
    """Write the generated HTML to disk and return its path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{_slugify(idea)}.html"
    path.write_text(html, encoding="utf-8")
    return str(path)


def deploy_to_netlify(idea: str, html: str) -> dict:
    """Deploy a single HTML file as a new Netlify site. Returns {"url": ..., "success": bool}."""
    api_token = os.getenv("NETLIFY_API_TOKEN")
    if not api_token:
        logger.warning("NETLIFY_API_TOKEN not set — skipping real deploy, local save only")
        return {"url": None, "success": False, "error": "NETLIFY_API_TOKEN not set"}

    slug = _slugify(idea)  # reuse existing slugify function in this file
    headers = {"Authorization": f"Bearer {api_token}"}

    try:
        # 1. Create a new site
        site_resp = requests.post(
            f"{NETLIFY_API}/sites",
            headers=headers,
            json={"name": f"autostartup-{slug}-{os.urandom(3).hex()}"},
            timeout=15,
        )
        site_resp.raise_for_status()
        site = site_resp.json()
        site_id = site["id"]
        site_url = site["url"]

        # 2. Zip the HTML file in-memory as index.html
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            zf.writestr("index.html", html)
        zip_buffer.seek(0)

        # 3. Deploy the zip
        deploy_resp = requests.post(
            f"{NETLIFY_API}/sites/{site_id}/deploys",
            headers={**headers, "Content-Type": "application/zip"},
            data=zip_buffer.getvalue(),
            timeout=30,
        )
        deploy_resp.raise_for_status()

        logger.info(f"Deployed to Netlify: {site_url}")
        return {"url": site_url, "success": True}

    except requests.exceptions.RequestException as e:
        logger.error(f"Netlify deploy failed: {e}")
        return {"url": None, "success": False, "error": str(e)}
