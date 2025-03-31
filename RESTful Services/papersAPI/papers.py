import logging
import random
from typing import List, Optional, Tuple

import aiohttp
import feedparser
from fastapi import FastAPI, HTTPException, Request, status, Security, Depends
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# OAuth2 scheme for security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Security configuration
API_KEY = "api-key-example"
api_key_header = APIKeyHeader(name="X-API-Key")


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key


class Paper(BaseModel):
    title: str
    authors: List[str]
    summary: str
    published: str
    link: str
    pdf: Optional[str] = None


async def fetch_associated_words(
    session: aiohttp.ClientSession, search_term: str
) -> Tuple[bool, List[str]]:
    """
    Fetch associated words from the arXiv API.

    Args:
        session: aiohttp ClientSession for making requests
        search_term: The search term to use
    Returns:
        Tuple containing success flag and list of associated words
    """
    BASE_URL = r"https://api.datamuse.com/words?"
    query = f"rel_trg={search_term}"
    url = BASE_URL + query

    words = [search_term]

    try:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"Datamuse API error: {response.status}")
                return False, words

            data = await response.json()
            for word in data:
                words.append(word["word"])

            return True, words
    except Exception as e:
        logger.error(f"Error fetching data from Datamuse: {str(e)}")
        return False, words


async def fetch_arxiv_papers(
    session: aiohttp.ClientSession, words: List[str]
) -> Tuple[bool, str, List[Paper]]:
    """
    Fetch papers from arXiv API based on the provided parameters.

    Args:
        session: aiohttp ClientSession for making requests
        words: List of words to search for

    Returns:
        Tuple containing success flag, the search term and a list of Paper objects
    """

    def create_search_term(words: List[str]) -> str:
        """
        Create a search term from the list of words.
        """
        search_terms = []
        for word in words:
            word = word.replace(" ", "+")
            word = f"%22{word}%22"
            search_terms.append(word)
        return "+".join(search_terms)

    BASE_URL = r"http://export.arxiv.org/api/query?"
    search_term = create_search_term(words)

    query = (
        f"search_query=ti:{search_term}ORabs:{search_term}"
        f"&start=0"
        f"&max_results=10"
        f"&sortBy=relevance"
        f"&sortOrder=descending"
    )
    url = BASE_URL + query

    papers = []

    try:
        async with session.get(url) as response:
            if response.status != 200:
                logger.error(f"arXiv API error: {response.status}")
                return False, search_term, papers

            feed_content = await response.text()
            feed = feedparser.parse(feed_content)

            for entry in feed.entries:
                paper = Paper(
                    title=entry.title,  # type: ignore
                    authors=[author.name for author in entry.authors],  # type: ignore
                    summary=entry.summary,  # type: ignore
                    published=entry.published,  # type: ignore
                    link=entry.link,  # type: ignore
                    pdf=entry.links[1].href,  # type: ignore
                )
                papers.append(paper)

            return True, search_term, papers
    except Exception as e:
        logger.error(f"Error fetching data from arXiv: {str(e)}")
        return False, search_term, papers


@app.get("/", response_class=HTMLResponse)
async def get_home():
    """
    Serve the static HTML home page
    """
    return templates.TemplateResponse("index.html", {"request": {}})


@app.get("/api/{word}")
async def get_paper_by_word(word: str, api_key: str = Depends(get_api_key)):
    """
    Fetch random papers based on the provided word.
    """
    WORDS_LIMIT = 10
    async with aiohttp.ClientSession() as session:
        # Fetch associated words
        success_words, words = await fetch_associated_words(session, word)
        if not success_words:
            raise HTTPException(
                status_code=500,
                detail="Internal server error: Failed to fetch data from Datamuse API",
            )

        # Fetch papers
        success_papers, search_term, papers = await fetch_arxiv_papers(
            session, words[:WORDS_LIMIT]
        )
        if not success_papers:
            raise HTTPException(
                status_code=500,
                detail="Internal server error: Failed to fetch data from arXiv API",
            )

        if not papers:
            raise HTTPException(
                status_code=404,
                detail="No papers found for the given search term",
            )

        return {"search_term": search_term, "paper": random.choice(papers).model_dump()}


@app.get("/paper", response_class=HTMLResponse)
async def get_paper_html(request: Request, word: str):
    """
    Fetch a paper using the existing API and display it as HTML.
    """
    try:
        # Reuse the existing API endpoint
        paper_data = await get_paper_by_word(word)
        paper = paper_data["paper"]

        # Return the template with the paper data
        return templates.TemplateResponse(
            "paper.html", {"request": request, "paper": paper}
        )

    except HTTPException as e:
        # Return error template
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error_message": e.detail},
            status_code=e.status_code,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
