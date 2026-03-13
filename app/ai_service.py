"""
AI services for AI Notes - Summary, Tags generation, and Smart Search
"""
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, MAX_SUMMARY_LENGTH, MAX_TAGS


class AIService:
    """AI service for note processing"""
    
    def __init__(self):
        self.client = None
        self.model = OPENAI_MODEL
        if OPENAI_API_KEY:
            self.client = OpenAI(
                api_key=OPENAI_API_KEY,
                base_url=OPENAI_BASE_URL
            )
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.client is not None
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[str]:
        """Call LLM with prompts"""
        if not self.is_available():
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"AI service error: {e}")
            return None
    
    def generate_summary(self, content: str) -> Optional[str]:
        """Generate a summary of the note content"""
        if not content or len(content.strip()) < 50:
            return None
        
        system_prompt = f"""You are a helpful assistant that summarizes text concisely.
Rules:
- Provide a summary in {MAX_SUMMARY_LENGTH} characters or less
- Capture the main points and key ideas
- Be concise and clear
- Respond with only the summary, no extra text"""
        
        user_prompt = f"Please summarize the following text:\n\n{content}"
        
        return self._call_llm(system_prompt, user_prompt)
    
    def generate_tags(self, title: str, content: str) -> List[str]:
        """Generate relevant tags for a note"""
        if not self.is_available():
            return []
        
        system_prompt = f"""You are a helpful assistant that generates relevant tags for text.
Rules:
- Generate at most {MAX_TAGS} tags
- Tags should be relevant to the main topics
- Use lowercase, short words (1-2 words each)
- Respond with ONLY a JSON array of strings, e.g., ["tag1", "tag2", "tag3"]
- No other text or explanation"""
        
        text = f"Title: {title}\n\nContent: {content[:2000]}"  # Limit content length
        user_prompt = f"Please generate relevant tags for the following text:\n\n{text}"
        
        result = self._call_llm(system_prompt, user_prompt, temperature=0.5)
        
        if not result:
            return []
        
        try:
            # Try to parse as JSON
            tags = json.loads(result)
            if isinstance(tags, list):
                return [str(tag).strip().lower()[:20] for tag in tags[:MAX_TAGS]]
        except json.JSONDecodeError:
            # Fallback: try to extract from text
            import re
            tags = re.findall(r'["\']([\w\s-]+)["\']', result)
            if tags:
                return [tag.strip().lower()[:20] for tag in tags[:MAX_TAGS]]
            # Last resort: split by comma
            tags = [tag.strip() for tag in result.split(",") if tag.strip()]
            return tags[:MAX_TAGS]
        
        return []
    
    def smart_search(self, query: str, notes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform semantic search across notes"""
        if not self.is_available() or not notes or not query.strip():
            return []
        
        system_prompt = """You are a helpful assistant that evaluates the relevance of notes to a search query.
For each note, determine if it's relevant to the query and provide a relevance score (0-100).
Respond with ONLY a JSON array in this exact format:
[{"note_id": 1, "relevance": 85, "reason": "brief explanation"}, ...]
Include only notes with relevance > 30. No other text."""
        
        notes_text = "\n\n".join([
            f"Note ID: {note['id']}\nTitle: {note['title']}\nContent: {note['content'][:500]}...\nTags: {', '.join(note.get('tags', []))}"
            for note in notes[:20]  # Limit to 20 notes for performance
        ])
        
        user_prompt = f"Query: {query}\n\nNotes to search:\n{notes_text}"
        
        result = self._call_llm(system_prompt, user_prompt, temperature=0.3)
        
        if not result:
            return []
        
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                result = json_match.group(0)
            
            search_results = json.loads(result)
            if isinstance(search_results, list):
                return sorted(search_results, key=lambda x: x.get('relevance', 0), reverse=True)
        except json.JSONDecodeError as e:
            print(f"Failed to parse search results: {e}")
            return []
        
        return []
    
    def enhance_content(self, content: str, instruction: str = "improve") -> Optional[str]:
        """Enhance note content based on instruction"""
        if not self.is_available() or not content:
            return None
        
        system_prompt = """You are a helpful writing assistant.
Improve the text based on the user's instruction while maintaining the original meaning.
Respond with only the improved text, no extra explanations."""
        
        user_prompt = f"Instruction: {instruction}\n\nText:\n{content}"
        
        return self._call_llm(system_prompt, user_prompt, temperature=0.4)


# Global AI service instance
ai_service = AIService()
