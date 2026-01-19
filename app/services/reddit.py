import requests
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.models.lead import Lead
import logging
import time

logger = logging.getLogger(__name__)

class RedditService:
    """
    Read-only Reddit service using public JSON API.
    No authentication required - accesses public Reddit data.
    """
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.headers = {
            "User-Agent": settings.REDDIT_USER_AGENT
        }
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # 1 second between requests to be respectful

    def _make_request(self, url: str) -> Optional[Dict[Any, Any]]:
        """Make a rate-limited request to Reddit's JSON API."""
        # Rate limiting: wait at least 1 second between requests
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                logger.warning("Rate limited by Reddit. Waiting 60 seconds...")
                time.sleep(60)
                return None
            else:
                logger.error(f"Reddit API returned status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error making request to Reddit: {e}")
            return None

    def fetch_recent_posts(self, limit: int = 20) -> List[Lead]:
        leads = []
        
        # Fetch from each subreddit individually (JSON API limitation)
        for subreddit in settings.SUBREDDITS:
            logger.info(f"Scanning subreddit: r/{subreddit}")
            url = f"{self.base_url}/r/{subreddit}/new.json?limit={limit}"
            
            data = self._make_request(url)
            if not data:
                continue
            
            try:
                posts = data.get("data", {}).get("children", [])
                for post_wrapper in posts:
                    post = post_wrapper.get("data", {})
                    
                    # Basic pre-filter: check if relevant keywords exist
                    full_text = f"{post.get('title', '')} {post.get('selftext', '')}"
                    if self._basic_keyword_match(full_text):
                        lead = self._post_to_lead(post)
                        leads.append(lead)
            except Exception as e:
                logger.error(f"Error parsing Reddit data for r/{subreddit}: {e}")
        
        logger.info(f"Found {len(leads)} potential leads from Reddit")
        return leads

    def _basic_keyword_match(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in settings.KEYWORDS)

    def _post_to_lead(self, post: Dict[Any, Any]) -> Lead:
        """Convert Reddit JSON post data to Lead object."""
        author = post.get("author", "[deleted]")
        permalink = post.get("permalink", "")
        
        return Lead(
            platform="Reddit",
            author_handle=author,
            post_url=f"https://www.reddit.com{permalink}",
            post_excerpt=f"{post.get('title', '')}\n\n{post.get('selftext', '')}"[:1000],
            author_profile_url=f"https://www.reddit.com/user/{author}" if author != "[deleted]" else None
        )
