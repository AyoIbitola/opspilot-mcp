import logging
import asyncio
import random
from typing import List
from twikit import Client
from app.core.config import settings
from app.models.lead import Lead

logger = logging.getLogger(__name__)

class TwitterService:
    def __init__(self):
        self.client = None
        self.enabled = False

        if settings.TWITTER_USERNAME and settings.TWITTER_PASSWORD:
            self.client = Client('en-US')
            self.enabled = True
        else:
            logger.info("Twitter credentials not provided. Service disabled.")

    async def _authenticate(self):
        if not self.enabled:
            return False
        
        try:
            # Twikit requires async login
            # Note: 2FA or email challenges might occur. 
            # Ideally cookies should be saved/loaded to avoid repetitive logins, 
            # but for MVP we attempt fresh login.
            await self.client.login(
                auth_info_1=settings.TWITTER_USERNAME,
                auth_info_2=settings.TWITTER_EMAIL,
                password=settings.TWITTER_PASSWORD
            )
            logger.info("Twitter authenticated successfully.")
            return True
        except Exception as e:
            logger.error(f"Twitter auth failed: {e}")
            self.enabled = False
            return False

    async def fetch_recent_posts(self, limit: int = 20) -> List[Lead]:
        if not self.enabled:
            return []

        # Authenticate if needed (simple check)
        # In a real app we'd verify cookie validity
        try:
            # We assume session might need init. 
            # Warning: Frequent logins can trigger security locks.
            # A robust implementation would load cookies.json
            await self._authenticate()
        except Exception:
            return []

        leads = []
        try:
            # Search query construction
            # Twikit search syntax similar to web: "keyword1 OR keyword2"
            # We'll take top 5 keywords to avoid query complexity issues
            query_keywords = " OR ".join(settings.KEYWORDS[:5])
            query = f"({query_keywords}) -filter:retweets"
            
            logger.info(f"Searching X for: {query[:50]}...")
            
            tweets = await self.client.search_tweet(query, 'Latest', count=limit)
            
            for tweet in tweets:
                leads.append(self._tweet_to_lead(tweet))
                
            # Random delay to be safe
            await asyncio.sleep(random.uniform(5, 10))
            
        except Exception as e:
            logger.error(f"Error fetching from Twitter: {e}")

        return leads

    def _tweet_to_lead(self, tweet) -> Lead:
        return Lead(
            platform="X",
            author_handle=tweet.user.screen_name,
            post_url=f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
            post_excerpt=tweet.text[:1000],
            author_profile_url=f"https://x.com/{tweet.user.screen_name}",
            has_pain=False
        )
