import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.lead import Lead

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock env vars BEFORE app imports (which trigger Settings load)
with patch.dict('os.environ', {
    'GEMINI_API_KEY': 'test_key',
    'REDDIT_CLIENT_ID': 'test_id',
    'REDDIT_CLIENT_SECRET': 'test_secret',
    'GOOGLE_SERVICE_ACCOUNT_JSON': 'test.json'
}):
    from app.models.lead import Lead
    from app.core.workflow import run_discovery_cycle
    # We need to re-import/mock services inside the test because they might have been imported at module level
    # But since we use patch on the module path, it should be fine if we patch where they are USED.

async def test_discovery_workflow():
    logger.info("Starting Test Discovery Cycle (MOCKED)...")

    # Mock Leads
    mock_lead_good = Lead(
        platform="Reddit", author_handle="manager_mike", post_url="http://reddit.com/r/1", 
        post_excerpt="I am drowning in manual reports and excel sheets. My team is lost.",
        author_profile_url="http://reddit.com/u/manager_mike"
    )
    mock_lead_bad = Lead(
        platform="Reddit", author_handle="spammer_steve", post_url="http://reddit.com/r/2",
        post_excerpt="Buy my crypto!",
        author_profile_url="http://reddit.com/u/spammer_steve"
    )

    # Patch services
    with patch('app.core.workflow.RedditService') as MockReddit, \
         patch('app.core.workflow.LinkedinService') as MockLinkedin, \
         patch('app.core.workflow.TwitterService') as MockTwitter, \
         patch('app.core.workflow.GeminiService') as MockGemini, \
         patch('app.core.workflow.SheetsService') as MockSheets:
        
        # Setup Mocks
        reddit_instance = MockReddit.return_value
        reddit_instance.fetch_recent_posts.return_value = [mock_lead_good, mock_lead_bad]
        
        linkedin_instance = MockLinkedin.return_value
        linkedin_instance.enabled = True
        linkedin_instance.fetch_recent_posts = AsyncMock(return_value=[])

        twitter_instance = MockTwitter.return_value
        twitter_instance.enabled = True
        twitter_instance.fetch_recent_posts = AsyncMock(return_value=[])

        gemini_instance = MockGemini.return_value
        # Async mocks for Gemini
        async def mock_analyze(lead):
            if "manual reports" in lead.post_excerpt:
                lead.has_pain = True
                lead.pain_category = "Reporting delays"
                lead.pain_summary = "User hates manual reporting."
                lead.urgency_score = 8
            else:
                lead.has_pain = False
            return lead
        
        gemini_instance.analyze_pain = AsyncMock(side_effect=mock_analyze)
        gemini_instance.draft_outreach = AsyncMock(return_value="Hey Mike, OpPilot fixes reporting.")

        sheets_instance = MockSheets.return_value
        sheets_instance.is_duplicate.return_value = False
        sheets_instance.append_lead.return_value = True

        # Run workflow
        result = await run_discovery_cycle()
        
        print("\n--- Test Results ---")
        print(f"Saved: {result['saved']} (Expected 1)")
        print(f"Dupes: {result['dupes']} (Expected 0)")
        print(f"Low Quality: {result['low_quality']} (Expected 1)")
        
        assert result['saved'] == 1
        assert result['low_quality'] == 1

if __name__ == "__main__":
    asyncio.run(test_discovery_workflow())
