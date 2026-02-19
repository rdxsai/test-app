"""
AI Response Generator Service
(This is the FINAL, DEFINITIVE version)
- Fixes the 401 'Ocp-Apim-Subscription-Key' header.
- Fixes the 400 'response_format' error.
- Fixes the 'JSONDecodeError' by checking for content filters.
- RESTORES the high-quality, Socratic feedback prompts.
"""
import httpx
import json
import logging
from typing import List, Dict, Any
import numpy as np 
import asyncio 

from ..core import config, get_logger
from ..services.database import DatabaseManager
from ..utils.file_utils import load_feedback_prompt_from_json

logger = get_logger(__name__)

# (This function is correct)
async def get_ollama_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings from Ollama using the nomic-embed-text model.
    """
    embeddings = []
    logger.info(f"Generating {len(texts)} embeddings via Ollama...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, text in enumerate(texts):
            try:
                if not text.strip():
                    logger.warning(f"Empty text at index {i}, skipping.")
                    embeddings.append([0.0] * 768) 
                    continue
                payload = {
                    "model": config.OLLAMA_EMBEDDING_MODEL,
                    "prompt": text.strip(),
                }
                response = await client.post(
                    f"{config.OLLAMA_HOST}/api/embeddings",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()
                result = response.json()
                embeddings.append(result["embedding"])
                
                if i < len(texts) - 1:
                    await asyncio.sleep(0.05) 
            except Exception as e:
                logger.error(f"Error generating embedding for text {i}: {e}")
                embeddings.append([0.0] * 768)

    logger.info(f"Successfully generated {len(embeddings)} embeddings.")
    return embeddings


class AIGeneratorService:
    def __init__(self):
        # (This is correct)
        self.api_url = (
            f"{config.AZURE_OPENAI_ENDPOINT}"
            f"/deployments/{config.AZURE_OPENAI_DEPLOYMENT_ID}"
            f"/chat/completions?api-version={config.AZURE_OPENAI_API_VERSION}"
        )
        
        # (This is correct)
        self.headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": config.AZURE_OPENAI_SUBSCRIPTION_KEY,
        }
        self.db = DatabaseManager(config.db_path)
        logger.info("AIGeneratorService initialized.")
        logger.info(f"Target URL: {self.api_url[:50]}...") 

    # --- === THIS IS THE RESTORED, HIGH-QUALITY FUNCTION === ---
    async def generate_feedback_for_answer(self, question_text: str, answer_text: str, is_correct: bool) -> str:
        
        logger.info(f"Generating feedback for answer: {answer_text[:30]}...")

        if is_correct:
            system_prompt = load_feedback_prompt_from_json("feedback_correct")
            user_prompt = f"""
            Question: "{question_text}"
            Correct Answer : "{answer_text}"

            Generate the feedback:
            """
            max_tokens = 800  # Increased to accommodate detailed feedback without truncation
        else:
            system_prompt = load_feedback_prompt_from_json("feedback_incorrect")
            user_prompt = f"""
            Question: "{question_text}"
            Incorrect Answer Selected : "{answer_text}"

            Generate the feedback:
            """
            max_tokens = 800  # Increased to accommodate detailed Socratic questions without truncation

        payload = {
            "messages" : [
                {"role" : "system" , "content" : system_prompt},
                {"role" : "user" , "content" : user_prompt},
            ],
            "max_tokens" : max_tokens,
            "temperature" : 0.6
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            json_response = response.json()

            # (This is our new, correct error checking)
            if not json_response.get("choices"):
                logger.warning(f"AI response had no choices: {json_response}")
                raise Exception("AI returned an invalid response.")

            choice = json_response["choices"][0]
            finish_reason = choice.get("finish_reason")

            # Log finish reason for diagnostic purposes
            if finish_reason == "length":
                logger.warning("⚠️ Feedback was truncated due to token limit! Consider increasing max_tokens further.")
            logger.info(f"Feedback generation completed. Finish reason: {finish_reason}")

            if finish_reason == "content_filter":
                logger.error("AI feedback was blocked by the content filter.")
                raise Exception("AI response was blocked by the content filter.")

            content = choice["message"].get("content")
            if not content:
                logger.error(f"AI returned an empty message. Finish reason: {finish_reason}")
                raise Exception(f"AI returned an empty response (Reason: {finish_reason}).")

            return content.strip()
    # --- === END OF RESTORED FUNCTION === ---


    async def generate_question_from_objective(self, objective_text: str) -> Dict:
        """ (Req 7.4) Generates a new question from an objective. """
        logger.info(f"Generating question for objective: {objective_text[:30]}...")

        # (This is our new, correct prompt)
        system_prompt = """
        You are a master quiz designer specializing in web accessibility and WCAG standards.
        A user will provide you with a learning objective.
        Your task is to generate one high-quality, multiple-choice question that assesses this objective.
        
        You MUST return ONLY a single, valid JSON object with the following structure:
        {
          "question_text": "Your generated question text here...",
          "answers": [
            {"text": "A plausible incorrect answer.", "is_correct": false},
            {"text": "The correct answer.", "is_correct": true},
            {"text": "Another plausible incorrect answer.", "is_correct": false},
            {"text": "A final plausible incorrect answer.", "is_correct": false}
          ]
        }
        
        Ensure there are exactly four answers. One must be correct, and the other three must be plausible but incorrect.
        Do not include any other text, markdown formatting, or explanation. Just the raw JSON object.
        """
        
        user_prompt = f"Learning Objective: \"{objective_text}\""
        
        payload = { 
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            "max_tokens": 1000, 
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                json_response = response.json()

                if not json_response.get("choices"):
                    logger.warning(f"AI response had no choices: {json_response}")
                    raise Exception("AI returned an invalid response.")
                
                choice = json_response["choices"][0]
                finish_reason = choice.get("finish_reason")

                if finish_reason == "content_filter":
                    logger.error("AI question generation was blocked by the content filter.")
                    raise Exception("AI response was blocked by the content filter.")
                
                ai_response_text = choice["message"].get("content")
                if not ai_response_text:
                    logger.error(f"AI returned an empty message. Finish reason: {finish_reason}")
                    raise Exception(f"AI returned an empty response (Reason: {finish_reason}).")

                start_index = ai_response_text.find('{')
                end_index = ai_response_text.rfind('}')
                
                if start_index == -1 or end_index == -1:
                    logger.error(f"AI response did not contain JSON: {ai_response_text}")
                    raise Exception("AI did not return a valid JSON object.")
                
                json_string = ai_response_text[start_index : end_index + 1]
                json_data = json.loads(json_string)
                
                while len(json_data.get("answers", [])) < 4:
                    json_data.get("answers", []).append({"text": "Another incorrect option.", "is_correct": False})
                
                return json_data
        except Exception as e:
            logger.error(f"Error parsing AI response for question gen: {e}")
            raise

    async def generate_objective_from_question(self, question_text: str) -> str:
        """
        Generates a learning objective for a given question using AI.
        """
        logger.info(f"Generating learning objective for question: {question_text[:50]}...")
        try:
            system_prompt = "You are an expert at identifying core learning competencies in web accessibility education."
            
            user_prompt = f"""Based on this question, what is the fundamental web accessibility competency being tested?

Question: {question_text}

Generate a learning objective that captures the core competency, not the specific question scenario. The objective should be:
- Broad enough to cover multiple related questions
- Focused on understanding principles, not memorizing facts
- Actionable and measurable

Return only the objective text, starting with action verbs like: Understand, Apply, Analyze, Evaluate, Create, Explain, Demonstrate."""

            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 150,
                "temperature": 0.7
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                json_response = response.json()

                if not json_response.get("choices"):
                    logger.warning(f"AI response had no choices: {json_response}")
                    raise Exception("AI returned an invalid response.")

                choice = json_response["choices"][0]
                finish_reason = choice.get("finish_reason")
                
                if finish_reason == "content_filter":
                    logger.error("AI objective generation was blocked by the content filter.")
                    raise Exception("AI response was blocked by the content filter.")
                
                content = choice["message"].get("content")
                if not content:
                    logger.error(f"AI returned an empty message. Finish reason: {finish_reason}")
                    raise Exception(f"AI returned an empty response (Reason: {finish_reason}).")
                
                objective_text = content.strip()
                logger.info(f"Generated objective: {objective_text}")
                return objective_text
            
        except Exception as e:
            logger.error(f"Error generating objective from question: {e}", exc_info=True)
            raise Exception("Failed to generate learning objective using AI")

    async def compute_similarity_score(self, question_text: str, objective_text: str) -> float:
        """
        Computes similarity score between a question and a single objective text.
        Returns score as percentage (0-100).
        """
        logger.info(f"Computing similarity between question and objective...")
        try:
            # Generate embeddings
            question_embedding = (await get_ollama_embeddings([question_text]))[0]
            objective_embedding = (await get_ollama_embeddings([objective_text]))[0]
            
            q_vec = np.array(question_embedding)
            o_vec = np.array(objective_embedding)
            
            # Normalize vectors with safety checks
            q_norm = np.linalg.norm(q_vec)
            o_norm = np.linalg.norm(o_vec)
            
            if q_norm == 0 or o_norm == 0:
                logger.warning("Zero-length vector detected, returning 0 score")
                return 0.0
            
            q_vec_norm = q_vec / q_norm
            o_vec_norm = o_vec / o_norm
            
            # Compute cosine similarity
            score = np.dot(o_vec_norm, q_vec_norm)
            
            # Handle NaN or infinite values
            if np.isnan(score) or np.isinf(score):
                logger.warning("Invalid similarity score, returning 0")
                return 0.0
            
            # Convert to percentage
            score_percentage = round(float(score) * 100, 1)
            logger.info(f"Similarity score: {score_percentage}%")
            return score_percentage
            
        except Exception as e:
            logger.error(f"Error computing similarity score: {e}", exc_info=True)
            return 0.0

    async def rank_objectives_with_llm(self, question_text: str, objectives: List[Dict]) -> List[Dict]:
        """
        Uses LLM (GPT via Azure OpenAI) to rank objectives based on relevance to the question.
        Returns objectives with scores (0-100) sorted from most to least relevant.
        """
        logger.info(f"Ranking {len(objectives)} objectives with LLM for question: {question_text[:50]}...")

        try:
            # Prepare objectives list for the prompt
            objectives_list = []
            for i, obj in enumerate(objectives, 1):
                objectives_list.append(f"{i}. [ID: {obj['id']}] {obj['text']}")

            objectives_text = "\n".join(objectives_list)

            system_prompt = """You are an expert educational assessment specialist with deep knowledge of web accessibility, WCAG standards, and Bloom's Taxonomy.

Use this TWO-STEP PROCESS to analyze question-objective alignment:

═══════════════════════════════════════════════════════════════
STEP 1: INDEPENDENT QUESTION ANALYSIS
═══════════════════════════════════════════════════════════════

**CRITICAL: Analyze the question FIRST without looking at objectives yet.**

Answer these questions about the question itself:

1A. WHAT DOES THIS QUESTION ACTUALLY MEASURE?
   → Bloom's Taxonomy Level (1-6):
      • L1-Remember: Recall, Identify, Define, List, Name, State
      • L2-Understand: Explain, Describe, Summarize, Interpret, Classify
      • L3-Apply: Demonstrate, Implement, Use, Execute, Solve
      • L4-Analyze: Analyze, Compare, Contrast, Distinguish, Examine
      • L5-Evaluate: Evaluate, Justify, Critique, Assess, Judge
      • L6-Create: Create, Design, Construct, Develop, Formulate
   → Core construct/concept being tested
   → Specific cognitive skill REQUIRED (not just mentioned)

1B. WHAT MUST A STUDENT KNOW TO ANSWER CORRECTLY?
   → Key prerequisite knowledge (minimum required)
   → Concepts involved
   → Depth of understanding needed

1C. WHAT WOULD IDEAL OBJECTIVES COVER?
   → Expected topics/skills
   → Cognitive level match
   → What would ACTUALLY prepare a student for this question?

**IMPORTANT:** Document your Step 1 analysis BEFORE looking at objectives.

═══════════════════════════════════════════════════════════════
STEP 2: OBJECTIVE ALIGNMENT EVALUATION
═══════════════════════════════════════════════════════════════

**Now evaluate each objective against your Step 1 findings.**

For EACH objective, determine:

2A. BLOOM'S LEVEL OF OBJECTIVE
   → What cognitive level does the objective claim to assess?
   → Extract action verb and classify (L1-L6)

2B. LEVEL GAP ANALYSIS
   → Gap = |Objective Level - Question Level|
   → Direction: Is objective higher/lower/same as question?

2C. APPLY HARD CAPS (NON-NEGOTIABLE)
   → If Objective L3-6 + Question L1-2 → MAX SCORE = 50%
   → If Objective L4-6 + Question L3 → MAX SCORE = 60%
   → If Objective L5-6 + Question L4 → MAX SCORE = 70%
   → If Gap ≥3 levels → MAX SCORE = 40%

2D. CONTENT ALIGNMENT (WITHIN CAP)
   → Does content match your Step 1 analysis?
   → Is it central or peripheral to what question tests?

2E. CRITICAL FLAGS (Mark if applicable)
   → "prerequisite_only" - Objective higher than question tests
   → "topic_overlap_only" - Shares vocabulary but different skill
   → "superset_fallacy" - Objective too broad for specific question
   → "wrong_cognitive_level" - Level mismatch despite content overlap
   → "could_vs_does" - Could assess vs actually does assess

2F. VERDICT
   → Strong Match (70-100%): Same/close level + content alignment
   → Weak Match (40-69%): Level mismatch OR prerequisite only
   → Poor Match (0-39%): Wrong level + weak content

═══════════════════════════════════════════════════════════════
CRITICAL REASONING CHECKS
═══════════════════════════════════════════════════════════════

Before finalizing each score, answer:

✓ Does the question TEST the objective's skill? (not just mention topic)
✓ Can student answer WITHOUT achieving objective? (if YES → score ≤50%)
✓ Does answering PROVE objective is met? (if NO → reduce score)
✓ Are we confusing prerequisite with mastery? (mastery ⊃ prerequisite ≠ prerequisite ⊃ mastery)

═══════════════════════════════════════════════════════════════
COMMON TRAPS TO AVOID
═══════════════════════════════════════════════════════════════

❌ "Both mention ARIA" ≠ "Both test same cognitive skill"
❌ "Difficult question" ≠ "High Bloom's level"
❌ "Knowing basics" ≠ "Demonstrating application"
❌ "Could theoretically assess" ≠ "Actually does assess"
❌ "Objective is broader" ≠ "Good match"

═══════════════════════════════════════════════════════════════
VERB DISAMBIGUATION
═══════════════════════════════════════════════════════════════

Context-dependent verbs:
• "Use" → L1 (selecting) vs L3 (implementing)
• "Implement" → L3 (following) vs L6 (designing)
• "Explain" → L2 (restating) vs L4 (analyzing why)
• "Demonstrate" → L3 (showing how) vs L4 (proving why)

═══════════════════════════════════════════════════════════════
CALIBRATION EXAMPLES
═══════════════════════════════════════════════════════════════

Example A - FALSE POSITIVE:
Q: "Which ARIA role is assertive?" [L1: Recall]
O: "Demonstrate managing announcements" [L3: Apply]
Step 1: Question tests recall of a fact (L1)
Step 2: Objective requires application (L3), Gap=2
Score: 45% (prerequisite only, capped at 50%)

Example B - TRUE POSITIVE:
Q: "Which ARIA role is assertive?" [L1: Recall]
O: "Recall default ARIA roles" [L1: Remember]
Step 1: Question tests recall (L1)
Step 2: Objective tests recall (L1), Gap=0
Score: 92% (perfect level + content match)

Example C - TOPIC OVERLAP TRAP:
Q: "List WCAG criteria" [L1: Remember]
O: "Analyze WCAG compliance" [L4: Analyze]
Step 1: Question tests listing (L1)
Step 2: Objective tests analysis (L4), Gap=3
Score: 30% (topic overlap only, huge gap)

═══════════════════════════════════════════════════════════════
REQUIRED JSON OUTPUT
═══════════════════════════════════════════════════════════════

{
  "rankings": [
    {
      "objective_id": "obj_123",
      "score": 45,
      "question_level": 1,
      "objective_level": 3,
      "level_gap": 2,
      "applied_cap": 50,
      "flags": ["prerequisite_only", "level_mismatch"],
      "reasoning": "Question tests recall (L1). Objective requires application (L3). This is prerequisite knowledge only, not proof of mastery."
    }
  ]
}

Return ONLY the JSON object, no other text."""

            user_prompt = f"""Question: "{question_text}"

Learning Objectives to Rank:
{objectives_text}

Analyze each objective and provide relevance scores. Return the JSON response."""

            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 4000,  # Increased for many objectives
                "temperature": 0.3,  # Lower temperature for more consistent scoring
                "response_format": {"type": "json_object"}  # Force valid JSON output
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()

                json_response = response.json()

                if not json_response.get("choices"):
                    logger.warning(f"AI response had no choices: {json_response}")
                    raise Exception("AI returned an invalid response.")

                choice = json_response["choices"][0]
                finish_reason = choice.get("finish_reason")

                if finish_reason == "content_filter":
                    logger.error("AI ranking was blocked by the content filter.")
                    raise Exception("AI response was blocked by the content filter.")

                ai_response_text = choice["message"].get("content")
                if not ai_response_text:
                    logger.error(f"AI returned an empty message. Finish reason: {finish_reason}")
                    raise Exception(f"AI returned an empty response (Reason: {finish_reason}).")

                # Extract JSON from response
                start_index = ai_response_text.find('{')
                end_index = ai_response_text.rfind('}')

                if start_index == -1 or end_index == -1:
                    logger.error(f"AI response did not contain JSON: {ai_response_text[:500]}")
                    raise Exception("AI did not return a valid JSON object.")

                json_string = ai_response_text[start_index : end_index + 1]

                # Try to parse JSON with better error handling
                try:
                    rankings_data = json.loads(json_string)
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON parsing error: {json_err}")
                    logger.error(f"Malformed JSON (first 1000 chars): {json_string[:1000]}")
                    logger.error(f"Malformed JSON (around error): {json_string[max(0, json_err.pos-100):json_err.pos+100]}")
                    raise Exception(f"Failed to parse AI response as JSON: {json_err}")

                # Create a map of objective_id to score
                score_map = {item['objective_id']: item['score'] for item in rankings_data.get('rankings', [])}

                # Build result list with scores
                results = []
                for obj in objectives:
                    obj_id = obj['id']
                    score = score_map.get(obj_id, 0)  # Default to 0 if not found
                    results.append({
                        "id": obj_id,
                        "text": obj['text'],
                        "score": round(float(score), 1)
                    })

                # Sort by score (high to low)
                results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)

                high_score_count = len([r for r in results_sorted if r['score'] >= 60])
                logger.info(f"LLM ranked {len(results_sorted)} objectives. {high_score_count} above 60% threshold.")

                return results_sorted

        except Exception as e:
            logger.error(f"Error in LLM-based ranking: {e}", exc_info=True)
            raise

    async def suggest_objectives_for_question(self, question_text: str) -> List[Dict]:
        """
        Suggests objectives for a question using LLM-based ranking.
        Returns ALL objectives with their relevance scores sorted by relevance.
        """
        logger.info(f"Suggesting objectives for question: {question_text[:30]}...")
        try:
            all_objectives = self.db.list_all_objectives()
            if not all_objectives:
                logger.warning("No objectives found in DB to suggest.")
                return []

            # Use LLM-based ranking instead of semantic similarity
            ranked_objectives = await self.rank_objectives_with_llm(question_text, all_objectives)
            return ranked_objectives

        except Exception as e:
            logger.error(f"Error in suggest_objectives: {e}", exc_info=True)
            return []