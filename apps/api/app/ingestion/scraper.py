"""HTTP scraper with rate limiting for university websites."""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.core.config import settings
from app.ingestion.schemas import ScrapeResult


class UniversityScraper:
    def __init__(
        self,
        *,
        timeout: float | None = None,
        rate_limit_per_domain: float | None = None,
        max_concurrency: int | None = None,
    ) -> None:
        self.timeout = timeout or settings.ingestion_timeout_seconds
        self.rate_limit = rate_limit_per_domain or settings.ingestion_rate_limit_per_domain
        self.semaphore = asyncio.Semaphore(max_concurrency or settings.ingestion_concurrency)
        self._domain_last_request: dict[str, float] = defaultdict(float)
        self._robots_cache: dict[str, RobotFileParser] = {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> UniversityScraper:
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": settings.ingestion_user_agent},
        )
        return self

    async def __aexit__(self, *args) -> None:
        if self._client:
            await self._client.aclose()

    def _domain(self, url: str) -> str:
        return urlparse(url).netloc.lower()

    async def _respect_rate_limit(self, domain: str) -> None:
        min_interval = 1.0 / self.rate_limit
        elapsed = time.monotonic() - self._domain_last_request[domain]
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._domain_last_request[domain] = time.monotonic()

    async def _can_fetch(self, url: str) -> bool:
        if not settings.ingestion_respect_robots:
            return True
        domain = self._domain(url)
        if domain not in self._robots_cache:
            parser = RobotFileParser()
            robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
            try:
                assert self._client is not None
                resp = await self._client.get(robots_url, timeout=5.0)
                if resp.status_code == 200:
                    parser.parse(resp.text.splitlines())
                else:
                    parser.parse([])
            except Exception:
                parser.parse([])
            self._robots_cache[domain] = parser
        return self._robots_cache[domain].can_fetch(settings.ingestion_user_agent, url)

    async def fetch(self, url: str) -> ScrapeResult:
        async with self.semaphore:
            domain = self._domain(url)
            await self._respect_rate_limit(domain)

            if not await self._can_fetch(url):
                return ScrapeResult(url=url, status_code=403, html="", error="Blocked by robots.txt")

            assert self._client is not None
            try:
                response = await self._client.get(url)
                return ScrapeResult(
                    url=url,
                    status_code=response.status_code,
                    html=response.text if response.status_code == 200 else "",
                    content_type=response.headers.get("content-type"),
                    error=None if response.status_code == 200 else f"HTTP {response.status_code}",
                )
            except httpx.HTTPError as exc:
                return ScrapeResult(url=url, status_code=0, html="", error=str(exc))

    async def fetch_batch(self, urls: list[str]) -> list[ScrapeResult]:
        return await asyncio.gather(*(self.fetch(url) for url in urls))
