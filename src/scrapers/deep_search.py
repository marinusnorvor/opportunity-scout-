"""Deep Search & Web Discovery Engine.

Discovers new opportunities from across the entire web (Wildcard ATS, LinkedIn, Google/DuckDuckGo indexes)
without being constrained to a pre-defined list of companies.
"""

import logging
import re
import urllib.parse
from typing import List, Optional, Set
from bs4 import BeautifulSoup
from src.scrapers.base_scraper import BaseScraper
from src.models import JobOpportunity

logger = logging.getLogger(__name__)


class DeepSearchEngine(BaseScraper):
    """Executes targeted web dorks and search queries to discover unlisted opportunities."""

    SEARCH_DORKS = [
        # Wildcard ATS across all fields worldwide (Business, Tech, Operations, Design, Finance)
        'site:boards.greenhouse.io ("intern" OR "internship" OR "fellowship") ("Remote" OR "Worldwide" OR "Ghana" OR "Relocation")',
        'site:jobs.lever.co ("intern" OR "internship" OR "fellowship") ("Remote" OR "Worldwide" OR "Ghana")',
        'site:ashbyhq.com ("intern" OR "internship") ("Remote" OR "Worldwide")',
        # Ghana local & regional internship discovery
        'site:jobberman.com.gh/job-listing ("intern" OR "internship" OR "trainee" OR "service personnel")',
        # Funded global undergraduate fellowships (Any discipline)
        '("fully funded" OR "flight and accommodation" OR "stipend provided") ("undergraduate" OR "student") ("internship" OR "fellowship")',
        # LinkedIn public indexed postings
        'site:linkedin.com/jobs/view ("intern" OR "internship") ("Ghana" OR "Remote Worldwide" OR "visa sponsorship")',
    ]

    def __init__(self, queries: Optional[List[str]] = None, timeout: int = 15):
        super().__init__(name="DeepSearchEngine", timeout=timeout)
        self.queries = queries or self.SEARCH_DORKS

    def fetch_opportunities(self, limit: Optional[int] = None) -> List[JobOpportunity]:
        """Run deep search across configured dorks and return discovered jobs."""
        discovered: List[JobOpportunity] = []
        seen_urls: Set[str] = set()

        for query in self.queries:
            if limit and len(discovered) >= limit:
                break
            
            logger.info(f"[DeepSearch] Running discovery query: {query[:60]}...")
            results = self._search_duckduckgo(query)
            
            for res in results:
                url = res.get("url", "")
                if not url or url in seen_urls:
                    continue
                
                seen_urls.add(url)
                company, title = self._extract_company_and_title(res.get("title", ""), url)
                job_id = self.generate_id(company, title, url)
                
                opp = JobOpportunity(
                    id=job_id,
                    title=title,
                    company=company,
                    location="Discovered via Deep Search (Check Listing)",
                    url=url,
                    source="Deep Web Search",
                    description_snippet=res.get("snippet", "")[:1200],
                    raw_metadata={"query": query, "raw_title": res.get("title")},
                )
                discovered.append(opp)
                
                if limit and len(discovered) >= limit:
                    break

        logger.info(f"[DeepSearch] Discovered {len(discovered)} potential new opportunities.")
        return discovered

    def _search_duckduckgo(self, query: str) -> List[dict]:
        """Perform search query against DuckDuckGo HTML endpoint (zero API key needed)."""
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "b": ""}
        
        headers = dict(self.DEFAULT_HEADERS)
        headers["Referer"] = "https://html.duckduckgo.com/"
        
        try:
            response = self.session.post(url, data=data, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning(f"[DeepSearch] Search returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, "html.parser")
            results = []
            
            for result_div in soup.find_all("div", class_=re.compile(r"result\s+results_links")):
                title_tag = result_div.find("a", class_="result__a")
                snippet_tag = result_div.find("a", class_="result__snippet")
                
                if not title_tag:
                    continue
                    
                raw_href = title_tag.get("href", "")
                actual_url = self._decode_ddg_url(raw_href)
                title = title_tag.get_text(strip=True)
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                
                # Verify that the URL actually looks like a job posting
                if self._is_relevant_job_link(actual_url, title, snippet):
                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet
                    })
                    
            return results
        except Exception as exc:
            logger.warning(f"[DeepSearch] Error querying DuckDuckGo: {exc}")
            return []

    @staticmethod
    def _decode_ddg_url(raw_url: str) -> str:
        """Decode DuckDuckGo redirect URL wrapper."""
        if "uddg=" in raw_url:
            match = re.search(r"uddg=([^&]+)", raw_url)
            if match:
                return urllib.parse.unquote(match.group(1))
        return raw_url

    @staticmethod
    def _is_relevant_job_link(url: str, title: str, snippet: str) -> bool:
        """Filter out unrelated search results (forums, blogs, aggregators of aggregators)."""
        lowered = f"{url} {title} {snippet}".lower()
        if not ("intern" in lowered or "fellow" in lowered or "student" in lowered or "co-op" in lowered):
            return False
        
        # Exclude common noise
        noise = ["reddit.com", "quora.com", "wikipedia.org", "youtube.com", "facebook.com", "twitter.com"]
        if any(n in url.lower() for n in noise):
            return False
            
        return True

    @staticmethod
    def _extract_company_and_title(raw_title: str, url: str) -> tuple[str, str]:
        """Extract company name and title from search result title or URL structure."""
        # Check if URL contains ATS patterns
        # e.g., boards.greenhouse.io/datadog/jobs/123 -> Company: Datadog
        gh_match = re.search(r"greenhouse\.io/([^/]+)", url)
        if gh_match:
            company = gh_match.group(1).replace("-", " ").title()
            title = re.sub(r"\s*-\s*Greenhouse.*", "", raw_title, flags=re.I).strip()
            return company, title

        lever_match = re.search(r"lever\.co/([^/]+)", url)
        if lever_match:
            company = lever_match.group(1).replace("-", " ").title()
            title = re.sub(r"\s*-\s*Lever.*", "", raw_title, flags=re.I).strip()
            return company, title

        ashby_match = re.search(r"ashbyhq\.com/([^/]+)", url)
        if ashby_match:
            company = ashby_match.group(1).replace("-", " ").title()
            return company, raw_title

        # Try splitting on common separators " - ", " | ", " at "
        for sep in [" - ", " | ", " at ", " @ "]:
            if sep in raw_title:
                parts = raw_title.split(sep)
                if len(parts) >= 2:
                    return parts[-1].strip(), parts[0].strip()

        # Fallback to domain name
        domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
        return domain.split(".")[0].title(), raw_title
