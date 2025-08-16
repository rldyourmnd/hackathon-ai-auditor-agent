"""Patch generation pipeline node."""

import logging
from typing import Any, Dict, List

from app.schemas.pipeline import PipelineState
from app.schemas.prompts import Patch
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)


async def propose_patches_node(state: PipelineState) -> PipelineState:
    """Generate improvement patches based on analysis results."""
    try:
        content = state.get_current_content()
        patches = []

        # Generate patches based on different analysis results

        # 1. Format fixes
        if not state.format_valid:
            format_patches = await _generate_format_patches(content, state.format_type)
            patches.extend(format_patches)

        # 2. Vocabulary improvements
        if state.vocab_changes:
            vocab_patches = _generate_vocab_patches(state.vocab_changes)
            patches.extend(vocab_patches)

        # 3. Contradiction fixes
        if state.contradictions:
            contradiction_patches = await _generate_contradiction_patches(content, state.contradictions)
            patches.extend(contradiction_patches)

        # 4. General quality improvements based on judge score
        if state.llm_judge_score and state.llm_judge_score < 8.0:
            quality_patches = await _generate_quality_patches(content, state.llm_judge_score, state.llm_judge_reasoning or "")
            patches.extend(quality_patches)

        # 5. Semantic clarity improvements
        if state.entropy_score and state.entropy_score > 0.5:
            clarity_patches = await _generate_clarity_patches(content, state.entropy_score)
            patches.extend(clarity_patches)

        # Update state
        state.patches = patches

        safe_count = sum(1 for p in patches if p.risk_level == "safe")
        risky_count = sum(1 for p in patches if p.risk_level == "risky")

        logger.info(f"Generated {len(patches)} patches ({safe_count} safe, {risky_count} risky)")

        return state

    except Exception as e:
        logger.error(f"Patch generation failed: {e}")
        state.add_error(f"Patch generation failed: {e}")
        return state


async def _generate_format_patches(content: str, format_type: str) -> List[Patch]:
    """Generate patches for format issues."""
    patches = []

    if format_type == "xml":
        # Basic XML fixes
        if "<" in content and not content.strip().startswith("<"):
            patches.append(Patch(
                id="xml_root_wrap",
                type="format",
                description="Wrap content in XML root element",
                current_text=content[:100] + "..." if len(content) > 100 else content,
                suggested_text=f"<root>{content}</root>",
                risk_level="safe",
                position={"start": 0, "end": len(content)},
                reasoning="XML content should be wrapped in a root element"
            ))

    elif format_type == "markdown":
        lines = content.split('\n')

        # Check for missing title
        if not any(line.strip().startswith('#') for line in lines[:3]):
            patches.append(Patch(
                id="md_add_title",
                type="format",
                description="Add markdown title",
                current_text=lines[0][:50] + "..." if lines and len(lines[0]) > 50 else (lines[0] if lines else ""),
                suggested_text=f"# Document Title\n\n{lines[0] if lines else ''}",
                risk_level="safe",
                position={"start": 0, "end": len(lines[0]) if lines else 0},
                reasoning="Markdown documents should have a clear title"
            ))

    return patches


def _generate_vocab_patches(vocab_changes: List[str]) -> List[Patch]:
    """Convert vocabulary changes to patches."""
    patches = []

    for i, change in enumerate(vocab_changes):
        # Parse change description to extract details
        if "Replaced" in change and "with" in change:
            try:
                # Extract old and new terms
                parts = change.split("'")
                if len(parts) >= 4:
                    old_term = parts[1]
                    new_term = parts[3]

                    patches.append(Patch(
                        id=f"vocab_{i}",
                        type="vocabulary",
                        description=f"Replace '{old_term}' with '{new_term}'",
                        current_text=old_term,
                        suggested_text=new_term,
                        risk_level="safe",
                        position={"start": 0, "end": 0},  # Position would need to be calculated
                        reasoning="Vocabulary standardization for consistency"
                    ))
            except Exception:
                # If parsing fails, create a general patch
                patches.append(Patch(
                    id=f"vocab_{i}",
                    type="vocabulary",
                    description=change,
                    current_text="[vocabulary improvement]",
                    suggested_text="[improved vocabulary]",
                    risk_level="safe",
                    position={"start": 0, "end": 0},
                    reasoning="Vocabulary improvement based on analysis"
                ))

    return patches


async def _generate_contradiction_patches(content: str, contradictions: List[Dict[str, Any]]) -> List[Patch]:
    """Generate patches to resolve contradictions."""
    patches = []

    llm = get_llm_service()

    for i, contradiction in enumerate(contradictions[:3]):  # Limit to 3 contradictions
        try:
            sentence1 = contradiction.get("sentence_1", "")
            sentence2 = contradiction.get("sentence_2", "")

            if not sentence1 or not sentence2:
                continue

            prompt = f"""These two statements contradict each other:

Statement 1: "{sentence1}"
Statement 2: "{sentence2}"

Provide a single, clear statement that resolves this contradiction by either:
1. Clarifying the relationship between the statements
2. Providing a unified statement that captures both intents
3. Prioritizing one over the other with clear reasoning

Respond with just the resolved statement (1-2 sentences max):"""

            resolution = await llm.ask("standard", prompt, max_tokens=150)

            patches.append(Patch(
                id=f"contradiction_{i}",
                type="contradiction",
                description=f"Resolve contradiction between statements",
                current_text=f"{sentence1} ... {sentence2}",
                suggested_text=resolution.strip(),
                risk_level="risky",  # Contradiction resolution changes meaning
                position={"start": 0, "end": 0},  # Would need actual positions
                reasoning=f"Resolves {contradiction.get('type', 'contradiction')}"
            ))

        except Exception as e:
            logger.error(f"Failed to generate contradiction patch {i}: {e}")

    return patches


async def _generate_quality_patches(content: str, judge_score: float, reasoning: str) -> List[Patch]:
    """Generate patches to improve overall quality."""
    patches = []

    try:
        llm = get_llm_service()

        prompt = f"""This prompt scored {judge_score:.1f}/10.0. Judge feedback: {reasoning}

Original prompt:
{content}

Suggest 2-3 specific improvements to increase the score. For each improvement, provide:
1. What to change (be specific about the text)
2. What to change it to
3. Why this improves the prompt

Focus on the biggest impact improvements. Be concise.

Format:
IMPROVEMENT 1:
Change: [specific text to change]
To: [replacement text]
Why: [brief reason]

IMPROVEMENT 2:
[etc.]"""

        response = await llm.ask("standard", prompt, max_tokens=400)

        # Parse improvements
        improvements = _parse_improvements(response)

        for i, improvement in enumerate(improvements):
            patches.append(Patch(
                id=f"quality_{i}",
                type="quality",
                description=improvement.get("description", "Quality improvement"),
                current_text=improvement.get("current", "")[:100],
                suggested_text=improvement.get("suggested", "")[:200],
                risk_level="risky",  # Quality changes can alter meaning
                position={"start": 0, "end": 0},
                reasoning=improvement.get("reasoning", "Improves overall prompt quality")
            ))

    except Exception as e:
        logger.error(f"Failed to generate quality patches: {e}")

    return patches


async def _generate_clarity_patches(content: str, entropy: float) -> List[Patch]:
    """Generate patches to improve semantic clarity."""
    patches = []

    if entropy > 0.7:  # High entropy suggests ambiguity
        try:
            llm = get_llm_service()

            prompt = f"""This prompt has high semantic ambiguity (entropy: {entropy:.2f}). Make it more specific and clear.

Original: {content}

Rewrite to be more specific and unambiguous. Focus on:
1. Clearer instructions
2. More specific requirements
3. Reduced ambiguity

Provide the improved version:"""

            improved = await llm.ask("standard", prompt, max_tokens=len(content) + 200)

            patches.append(Patch(
                id="clarity_overall",
                type="clarity",
                description="Improve overall clarity and reduce ambiguity",
                current_text=content[:100] + "..." if len(content) > 100 else content,
                suggested_text=improved.strip()[:300] + "..." if len(improved.strip()) > 300 else improved.strip(),
                risk_level="risky",
                position={"start": 0, "end": len(content)},
                reasoning=f"Reduces semantic ambiguity (entropy: {entropy:.2f})"
            ))

        except Exception as e:
            logger.error(f"Failed to generate clarity patch: {e}")

    return patches


def _parse_improvements(text: str) -> List[Dict[str, str]]:
    """Parse improvement suggestions from LLM response."""
    improvements = []

    import re

    # Try to extract improvements using pattern matching
    pattern = r"IMPROVEMENT \d+:(.*?)(?=IMPROVEMENT \d+:|$)"
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    for match in matches:
        lines = [line.strip() for line in match.strip().split('\n') if line.strip()]

        improvement = {}
        current_key = None

        for line in lines:
            if line.lower().startswith('change:'):
                improvement['current'] = line[7:].strip()
                current_key = 'current'
            elif line.lower().startswith('to:'):
                improvement['suggested'] = line[3:].strip()
                current_key = 'suggested'
            elif line.lower().startswith('why:'):
                improvement['reasoning'] = line[4:].strip()
                current_key = 'reasoning'
            elif current_key and not any(line.lower().startswith(prefix) for prefix in ['change:', 'to:', 'why:']):
                # Continue previous field
                improvement[current_key] += " " + line

        if improvement.get('current') and improvement.get('suggested'):
            improvement['description'] = f"Change '{improvement['current'][:30]}...' to improve quality"
            improvements.append(improvement)

    return improvements
