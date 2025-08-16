"""LLM-as-Judge scoring pipeline node."""

import json
import logging
from typing import Any, Dict

from app.schemas.pipeline import PipelineState
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)


async def judge_score_node(state: PipelineState) -> PipelineState:
    """Score the prompt using LLM-as-Judge with rubric."""
    try:
        content = state.get_current_content()

        # Get judge evaluation
        judge_result = await _evaluate_with_judge(content)

        # Update state
        state.llm_judge_score = judge_result["overall_score"]
        state.llm_judge_reasoning = judge_result["reasoning"]

        logger.info(f"Judge score: {judge_result['overall_score']:.2f}/10")

        return state

    except Exception as e:
        logger.error(f"Judge scoring failed: {e}")
        state.add_error(f"Judge scoring failed: {e}")
        # Set default score
        state.llm_judge_score = 5.0
        state.llm_judge_reasoning = "Scoring failed - default score assigned"
        return state


async def _evaluate_with_judge(content: str) -> Dict[str, Any]:
    """Evaluate prompt quality using LLM judge."""

    llm = get_llm_service()

    judge_prompt = f"""You are an expert prompt evaluator. Analyze this prompt and score it on multiple dimensions.

PROMPT TO EVALUATE:
{content}

EVALUATION RUBRIC:
Rate each dimension from 1-10 (1=poor, 10=excellent):

1. CLARITY (1-10): Is the prompt clear and unambiguous?
   - 1-3: Confusing, unclear intent
   - 4-6: Somewhat clear but could be clearer
   - 7-8: Generally clear with minor ambiguities
   - 9-10: Crystal clear, no ambiguity

2. SPECIFICITY (1-10): Does it provide enough specific details?
   - 1-3: Too vague, missing key details
   - 4-6: Some specifics but lacks important details
   - 7-8: Good level of detail with minor gaps
   - 9-10: Highly specific and detailed

3. ACTIONABILITY (1-10): Can someone easily act on this prompt?
   - 1-3: Unclear what action to take
   - 4-6: Action somewhat clear but confusing
   - 7-8: Clear actionable steps with minor gaps
   - 9-10: Perfectly actionable instructions

4. COMPLETENESS (1-10): Does it cover all necessary aspects?
   - 1-3: Major gaps in requirements
   - 4-6: Some gaps but covers basics
   - 7-8: Mostly complete with minor omissions
   - 9-10: Comprehensive and complete

5. STRUCTURE (1-10): Is it well-organized and coherent?
   - 1-3: Poor structure, incoherent
   - 4-6: Basic structure but could be better
   - 7-8: Well-structured with minor issues
   - 9-10: Excellent structure and flow

RESPOND IN JSON FORMAT:
{{
  "clarity": <score>,
  "specificity": <score>,
  "actionability": <score>,
  "completeness": <score>,
  "structure": <score>,
  "overall_score": <average of all scores>,
  "reasoning": "<2-3 sentence explanation of the overall assessment>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "weaknesses": ["<weakness 1>", "<weakness 2>"]
}}"""

    try:
        response = await llm.ask("standard", judge_prompt, max_tokens=500)

        # Try to parse JSON response
        try:
            result = json.loads(response.strip())

            # Validate required fields
            required_fields = ["clarity", "specificity", "actionability", "completeness", "structure", "overall_score", "reasoning"]

            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing field: {field}")

            # Ensure scores are in valid range
            for score_field in ["clarity", "specificity", "actionability", "completeness", "structure", "overall_score"]:
                score = result[score_field]
                if not isinstance(score, (int, float)) or score < 1 or score > 10:
                    result[score_field] = 5.0  # Default fallback

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse judge response as JSON: {e}")
            return _parse_judge_fallback(response)

    except Exception as e:
        logger.error(f"Judge evaluation request failed: {e}")
        return {
            "clarity": 5.0,
            "specificity": 5.0,
            "actionability": 5.0,
            "completeness": 5.0,
            "structure": 5.0,
            "overall_score": 5.0,
            "reasoning": f"Evaluation failed: {str(e)}",
            "strengths": [],
            "weaknesses": ["Evaluation could not be completed"]
        }


def _parse_judge_fallback(response: str) -> Dict[str, Any]:
    """Fallback parser if JSON parsing fails."""
    import re

    # Try to extract scores using regex
    scores = {}

    score_patterns = [
        (r"clarity[:\\s]*(\d+(?:\.\d+)?)", "clarity"),
        (r"specificity[:\\s]*(\d+(?:\.\d+)?)", "specificity"),
        (r"actionability[:\\s]*(\d+(?:\.\d+)?)", "actionability"),
        (r"completeness[:\\s]*(\d+(?:\.\d+)?)", "completeness"),
        (r"structure[:\\s]*(\d+(?:\.\d+)?)", "structure"),
        (r"overall[_\\s]*score[:\\s]*(\d+(?:\.\d+)?)", "overall_score"),
    ]

    for pattern, field in score_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            try:
                score = float(match.group(1))
                scores[field] = min(10.0, max(1.0, score))  # Clamp to 1-10
            except ValueError:
                scores[field] = 5.0
        else:
            scores[field] = 5.0

    # Calculate overall score if not found
    if "overall_score" not in scores:
        individual_scores = [scores.get(f, 5.0) for f in ["clarity", "specificity", "actionability", "completeness", "structure"]]
        scores["overall_score"] = sum(individual_scores) / len(individual_scores)

    # Extract reasoning if possible
    reasoning_match = re.search(r"reasoning[\"\\s:]*([^\\n\\r}]+)", response, re.IGNORECASE)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "Unable to parse detailed reasoning"

    return {
        **scores,
        "reasoning": reasoning,
        "strengths": [],
        "weaknesses": []
    }
