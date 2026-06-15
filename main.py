import asyncio
import aiohttp
from fastapi import FastAPI, Query
from pydantic import BaseModel

# Vercel finds this exactly where it expects it!
app = FastAPI()

ACCOUNT_URL = "https://www.netflix.com/YourAccount"
TARGET_SVG_PATH = 'd="M8 1.5a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13M8 0a8 8 0 1 1 0 16A8 8 0 0 1 8 0m1.5 3h-3l.833 7h1.334zM8 11a1 1 0 1 1 0 2 1 1 0 0 1 0-2"'
TARGET_ICON_ATTR = 'data-icon="CircleExclamationPointSmall"'

class StatusResponse(BaseModel):
    status: str
    result: str
    details: str

async def check_account_status_api(login_link: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }
    connector = aiohttp.TCPConnector(ssl=False, ttl_dns_cache=300, limit=1)
    timeout = aiohttp.ClientTimeout(total=5.0) 
    
    async with aiohttp.ClientSession(connector=connector, headers=headers, timeout=timeout) as session:
        try:
            async with session.get(login_link, allow_redirects=True) as init_resp:
                if init_resp.status != 200:
                    return {"status": "error", "result": "INVALID_ENTRY_LINK", "details": "The session entry link refused to connect properly."}

            async with session.get(ACCOUNT_URL, allow_redirects=True) as resp:
                final_path = resp.url.path.lower()
                html_content = await resp.text()
                
                if any(segment in final_path for segment in ["payment", "simplemember", "signup", "fix"]):
                    return {"status": "success", "result": "HOLD", "details": f"Session redirected to an accounting funnel path: {final_path}"}

                if TARGET_SVG_PATH in html_content or TARGET_ICON_ATTR in html_content:
                    return {"status": "success", "result": "HOLD", "details": "Warning indicator element signature identified."}
                
                return {"status": "success", "result": "GOOD", "details": "Account verified clear. No structural alert flags were found."}

        except asyncio.TimeoutError:
            return {"status": "error", "result": "TIMEOUT", "details": "The validation request tracking exceeded engine execution time window limits."}
        except Exception as e:
            return {"status": "error", "result": "CONNECTION_FAILURE", "details": str(e)}

@app.get("/api/check", response_model=StatusResponse)
async def check_endpoint(url: str = Query(..., description="The session entry url link")):
    return await check_account_status_api(url)
