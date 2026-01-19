import google.generativeai as genai
from app.core.config import settings
from app.models.lead import Lead
import logging
import json

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

class GeminiService:
    def __init__(self):
        try:
            logger.info(f"google-generativeai version: {genai.__version__}")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    logger.info(f"Available model: {m.name}")
        except Exception as e:
            logger.error(f"Failed to list models: {e}")

        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Free tier model

    async def analyze_pain(self, lead: Lead) -> Lead:
        prompt = f"""
        Analyze the following social media post for operational pain points experienced by managers or founders.
        
        Post Content:
        {lead.post_excerpt}

        Return strictly valid JSON with no markdown formatting. The JSON must match this schema:
        {{
          "has_pain": boolean,
          "pain_category": "Chasing updates" | "Reporting delays" | "Lack of visibility" | "Tool overload" | "Other" | null,
          "pain_summary": "Short explanation in plain English" | null,
          "urgency_score": integer (1-10),
          "reasoning": "Why this qualifies"
        }}
        
        Criteria:
        - has_pain: true if the author is a manager/founder expressing frustration about operations, reporting, or visibility.
        - urgency_score: 1 (low) to 10 (high).
        """

        try:
            response = self.model.generate_content(prompt)
            # Cleanup potential markdown ticks
            text = response.text.strip().replace('```json', '').replace('```', '')
            data = json.loads(text)
            
            lead.has_pain = data.get("has_pain", False)
            if lead.has_pain:
                lead.pain_category = data.get("pain_category")
                lead.pain_summary = data.get("pain_summary")
                lead.urgency_score = data.get("urgency_score", 0)
                lead.notes = data.get("reasoning", "")
                
        except Exception as e:
            logger.error(f"Error analyzing pain with Gemini: {e}")
        
        return lead

    async def draft_outreach(self, lead: Lead) -> str:
        if not lead.has_pain:
            return ""

        prompt = f"""
        Draft a very short (max 3 sentences), casual, non-salesy DM to this person.
        Pretend you are a rough-around-the-edges founder (OpsPilot) who solves this exact pain.
        
        Context:
        Their Pain: {lead.pain_summary}
        Category: {lead.pain_category}
        
        Rules:
        - No emojis.
        - No links.
        - No "I hope this finds you well".
        - Just relate to the pain and offer a quick "same here" or "we fixed this by X".
        - Sound valid, not spammy.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error drafting outreach: {e}")
            return ""
