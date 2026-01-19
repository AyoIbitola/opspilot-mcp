import logging
import asyncio
from app.services.reddit import RedditService
from app.services.linkedin import LinkedinService
from app.services.twitter import TwitterService
from app.services.gemini import GeminiService
from app.services.sheets import SheetsService
from app.models.lead import Lead

logger = logging.getLogger(__name__)

async def run_discovery_cycle():
    logger.info("Starting Daily Discovery Cycle...")
    
    # Initialize Services
    reddit = RedditService()
    linkedin = LinkedinService()
    twitter = TwitterService()
    gemini = GeminiService()
    sheets = SheetsService()
    
    # 1. Ingest
    leads: list[Lead] = []
    
    # Reddit
    logger.info("Fetching Reddit posts...")
    leads.extend(reddit.fetch_recent_posts(limit=25))
    
    # LinkedIn
    if linkedin.enabled:
        logger.info("Fetching LinkedIn posts...")
        leads.extend(await linkedin.fetch_recent_posts(limit=10)) 
        
    # Twitter
    if twitter.enabled:
        logger.info("Fetching X (Twitter) posts...")
        leads.extend(await twitter.fetch_recent_posts(limit=20))
        
    logger.info(f"Total raw leads fetched: {len(leads)}")
    
    processed_count = 0
    skipped_dupes = 0
    skipped_quality = 0
    saved_count = 0
    
    for lead in leads:
        # 2. Deduplication (Fast check)
        if sheets.is_duplicate(lead):
            skipped_dupes += 1
            continue
            
        # 3. AI Analysis
        # We only analyze if it passed dedupe
        try:
            lead = await gemini.analyze_pain(lead)
            
            if not lead.has_pain or lead.urgency_score < 6:
                skipped_quality += 1
                continue
                
            # 4. Draft Outreach
            lead.suggested_outreach_message = await gemini.draft_outreach(lead)
            
            # 5. Save
            if sheets.append_lead(lead):
                saved_count += 1
                logger.info(f"Saved lead: {lead.platform} - {lead.author_handle}")
                
        except Exception as e:
            logger.error(f"Error processing lead {lead.post_url}: {e}")
            
    logger.info(f"Discovery Cycle Complete. Saved: {saved_count}, Dupes: {skipped_dupes}, Low Quality: {skipped_quality}")
    
    return {
        "saved": saved_count,
        "dupes": skipped_dupes,
        "low_quality": skipped_quality
    }
