"""
Virality Pre-Score Gate — Only Produce Content That Can Hit 1M Views

Scores each script on 12 dimensions before it enters the production pipeline.
Scripts below the threshold are killed before wasting production resources.

Scoring dimensions:
 1. Hook Power (0-10)      — Will someone stop scrolling?
 2. Named Entity (0-10)    — Does title contain searchable name?
 3. Emotional Intensity (0-10)  — Does it trigger strong emotions?
 4. Information Gap (0-10)  — Does it create irresistible curiosity?
 5. Shareability (0-10)    — Would someone send this to a friend?
 6. Comment Bait (0-10)    — Will viewers argue about this?
 7. Trend Alignment (0-10) — Is this topic being searched RIGHT NOW?
 8. Title CTR (0-10)       — Would you click this title?
 9. Retention Prediction (0-10) — Will viewers watch to the end?
10. Uniqueness (0-10)      — Has this angle been done to death?
11. Visual Potential (0-10) — Can we make stunning visuals for this?
12. Replay Value (0-10)    — Would someone watch this twice?

Final score = weighted average → threshold 75/100 to enter production
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

VIRALITY_THRESHOLD = 75
MINIMUM_THRESHOLD = 60

SCORING_WEIGHTS = {
    "hook_power": 1.5,
    "named_entity": 1.3,
    "emotional_intensity": 1.2,
    "information_gap": 1.2,
    "shareability": 1.4,
    "comment_bait": 1.1,
    "trend_alignment": 1.3,
    "title_ctr": 1.5,
    "retention_prediction": 1.2,
    "uniqueness": 1.0,
    "visual_potential": 0.8,
    "replay_value": 0.9,
}

TOTAL_WEIGHT = sum(SCORING_WEIGHTS.values())


def score_script_ai(script: dict) -> dict:
    """Use Gemini to score a script across all 12 virality dimensions."""
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    title = script.get("title", "")
    hook = script.get("hook", "")
    body = script.get("body", "")
    outro = script.get("outro", "")
    full_script = script.get("full_script", f"{hook} {body} {outro}")
    niche = script.get("niche", "tech")

    prompt = f"""You are a YouTube Shorts virality analyst with data from 100,000+ shorts.
Score this script across 12 dimensions. Be BRUTALLY honest — we only want to produce
scripts that can realistically hit 100K+ views.

SCRIPT TO SCORE:
Title: {title}
Hook: {hook}
Body (first 200 chars): {body[:200]}
Outro: {outro}
Niche: {niche}

SCORING CRITERIA (score each 0-10, 10 = viral masterpiece):

1. HOOK_POWER: Does the first sentence make you stop scrolling? 
   10 = physically impossible to scroll past. 0 = boring, generic opener.
   
2. NAMED_ENTITY: Does the title contain a recognizable, searchable name?
   10 = major celebrity/company everyone knows. 0 = no named entity at all.
   
3. EMOTIONAL_INTENSITY: How strong is the emotional reaction?
   10 = makes you gasp, laugh, or feel angry. 0 = no emotional response.
   
4. INFORMATION_GAP: Does it create irresistible curiosity?
   10 = "I MUST know the answer." 0 = "I already know this" or "I don't care."
   
5. SHAREABILITY: Would someone send this to a friend?
   10 = "OMG you need to see this." 0 = "meh, whatever."
   
6. COMMENT_BAIT: Will viewers argue about this?
   10 = divisive topic that forces sides. 0 = nothing to discuss.
   
7. TREND_ALIGNMENT: Is this topic being actively searched?
   10 = trending globally right now. 0 = nobody cares about this topic.
   
8. TITLE_CTR: Would you click this title in a feed?
   10 = irresistible click magnet. 0 = scroll right past.
   
9. RETENTION_PREDICTION: Will viewers watch to the end?
   10 = builds perfectly, impossible to stop watching. 0 = viewers leave after 3 seconds.
   
10. UNIQUENESS: Has this angle been done to death?
    10 = completely fresh angle. 0 = seen this exact video 100 times.
    
11. VISUAL_POTENTIAL: Can we make stunning visuals for this?
    10 = incredibly visual topic. 0 = abstract concept hard to visualize.
    
12. REPLAY_VALUE: Would someone watch this twice?
    10 = packed with details you miss first time. 0 = no reason to rewatch.

Return ONLY JSON (no markdown, no code fences):
{{
  "scores": {{
    "hook_power": <0-10>,
    "named_entity": <0-10>,
    "emotional_intensity": <0-10>,
    "information_gap": <0-10>,
    "shareability": <0-10>,
    "comment_bait": <0-10>,
    "trend_alignment": <0-10>,
    "title_ctr": <0-10>,
    "retention_prediction": <0-10>,
    "uniqueness": <0-10>,
    "visual_potential": <0-10>,
    "replay_value": <0-10>
  }},
  "strengths": ["top 2 strengths"],
  "weaknesses": ["top 2 weaknesses"],
  "improvement_suggestions": ["specific actionable improvement 1", "specific actionable improvement 2"],
  "viral_probability": "<low/medium/high/very_high>",
  "comparable_to": "name a real viral short this reminds you of and why"
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        result = json.loads(text)
        return result
    except Exception as e:
        print(f"    ⚠️  AI scoring failed: {e}")
        return None


def calculate_weighted_score(scores: dict) -> float:
    """Calculate the weighted virality score (0-100)."""
    if not scores:
        return 0

    weighted_sum = 0
    for dimension, weight in SCORING_WEIGHTS.items():
        raw_score = scores.get(dimension, 5)
        weighted_sum += raw_score * weight

    return round((weighted_sum / TOTAL_WEIGHT) * 10, 1)


def score_script(script: dict) -> dict:
    """Score a single script and return the full analysis."""
    print(f"    🔬 Scoring: \"{script.get('title', 'Untitled')[:50]}...\"")

    ai_result = score_script_ai(script)
    if not ai_result or "scores" not in ai_result:
        return {
            "final_score": 50,
            "passed": False,
            "reason": "AI scoring failed — defaulting to pass-through",
            "scores": {},
        }

    scores = ai_result["scores"]
    final_score = calculate_weighted_score(scores)
    passed = final_score >= VIRALITY_THRESHOLD

    result = {
        "final_score": final_score,
        "passed": passed,
        "threshold": VIRALITY_THRESHOLD,
        "dimension_scores": scores,
        "strengths": ai_result.get("strengths", []),
        "weaknesses": ai_result.get("weaknesses", []),
        "improvements": ai_result.get("improvement_suggestions", []),
        "viral_probability": ai_result.get("viral_probability", "unknown"),
        "comparable_to": ai_result.get("comparable_to", ""),
    }

    status = "✅ PASSED" if passed else "❌ KILLED"
    print(f"    {status} — Score: {final_score}/100 (threshold: {VIRALITY_THRESHOLD})")
    if not passed:
        print(f"    📋 Weaknesses: {', '.join(ai_result.get('weaknesses', []))}")
        print(f"    💡 Improvements: {', '.join(ai_result.get('improvement_suggestions', []))}")

    return result


def score_batch(scripts: list[dict], kill_below_threshold: bool = True) -> tuple[list[dict], list[dict]]:
    """Score a batch of scripts. Returns (passed, killed) lists."""
    passed = []
    killed = []

    print(f"\n  🔬 VIRALITY PRE-SCORE GATE — Scoring {len(scripts)} scripts...")
    print(f"  {'─'*50}")

    for script in scripts:
        result = score_script(script)
        script["virality_score"] = result

        if result["passed"] or not kill_below_threshold:
            passed.append(script)
        elif result["final_score"] >= MINIMUM_THRESHOLD:
            # Scripts between minimum and threshold get improvement pass
            print(f"    🔄 Script at {result['final_score']}/100 — eligible for improvement")
            passed.append(script)
        else:
            killed.append(script)

    print(f"\n  📊 Virality Gate Results:")
    print(f"     ✅ Passed: {len(passed)}/{len(scripts)}")
    print(f"     ❌ Killed: {len(killed)}/{len(scripts)}")

    if passed:
        avg_score = sum(s["virality_score"]["final_score"] for s in passed) / len(passed)
        print(f"     📈 Average score (passed): {avg_score:.1f}/100")

    return passed, killed


def improve_script(script: dict, score_result: dict) -> dict:
    """Use Gemini to improve a script based on scoring feedback."""
    import google.generativeai as genai
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")

    weaknesses = score_result.get("weaknesses", [])
    improvements = score_result.get("improvements", [])
    scores = score_result.get("dimension_scores", {})

    # Find the lowest-scoring dimensions
    low_dims = sorted(scores.items(), key=lambda x: x[1])[:3]
    low_dims_text = ", ".join(f"{d[0]}={d[1]}/10" for d in low_dims)

    prompt = f"""You are a viral content optimizer. Improve this YouTube Shorts script to maximize virality.

CURRENT SCRIPT:
Title: {script.get('title', '')}
Hook: {script.get('hook', '')}
Body: {script.get('body', '')}
Outro: {script.get('outro', '')}

WEAKNESSES IDENTIFIED: {', '.join(weaknesses)}
LOWEST SCORES: {low_dims_text}
SUGGESTED IMPROVEMENTS: {', '.join(improvements)}

REWRITE the script to fix these weaknesses. Keep the same topic but make it significantly more viral.

Rules:
- Hook MUST start with the most shocking word (name, number, or superlative)
- Title MUST contain a recognizable named entity
- Outro MUST be a divisive binary question
- Total words: 140-170
- Every sentence must earn its place — if it doesn't shock, inform, or build tension, cut it

Return ONLY JSON (no markdown):
{{
  "title": "improved title",
  "hook": "improved hook",
  "body": "improved body",
  "outro": "improved outro",
  "changes_made": ["what you changed and why"]
}}"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        improved = json.loads(text)
        script["title"] = improved.get("title", script["title"])
        script["hook"] = improved.get("hook", script["hook"])
        script["body"] = improved.get("body", script["body"])
        script["outro"] = improved.get("outro", script["outro"])
        script["full_script"] = f"{script['hook']} {script['body']} {script['outro']}"
        script["word_count"] = len(script["full_script"].split())
        script["improvement_log"] = improved.get("changes_made", [])
        script["improved"] = True

        print(f"    ✨ Script improved: {', '.join(improved.get('changes_made', [])[:2])}")
        return script
    except Exception as e:
        print(f"    ⚠️  Improvement failed: {e}")
        return script


def gate_and_improve(scripts: list[dict], max_improvement_rounds: int = 2) -> list[dict]:
    """Full virality gate: score → improve weak ones → re-score → final filter."""
    passed, killed = score_batch(scripts)

    # Improvement loop for borderline scripts
    for round_num in range(max_improvement_rounds):
        needs_improvement = [
            s for s in passed
            if s.get("virality_score", {}).get("final_score", 0) < VIRALITY_THRESHOLD
        ]

        if not needs_improvement:
            break

        print(f"\n  🔄 Improvement Round {round_num + 1} — {len(needs_improvement)} scripts...")
        for script in needs_improvement:
            score_result = script.get("virality_score", {})
            script = improve_script(script, score_result)

            # Re-score after improvement
            new_result = score_script(script)
            script["virality_score"] = new_result

    # Final filter
    final_passed = [
        s for s in passed
        if s.get("virality_score", {}).get("final_score", 0) >= MINIMUM_THRESHOLD
    ]

    print(f"\n  🏁 Final Gate Result: {len(final_passed)}/{len(scripts)} scripts passed")
    return final_passed


def main():
    """Score all scripts in the pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description="Score scripts for virality potential")
    parser.add_argument("--scripts", nargs="*", help="Specific script IDs to score")
    parser.add_argument("--threshold", type=int, default=VIRALITY_THRESHOLD)
    args = parser.parse_args()

    if args.scripts:
        paths = [config.SCRIPTS_DIR / f"{sid}.json" for sid in args.scripts]
    else:
        paths = sorted(config.SCRIPTS_DIR.glob("*.json"))

    scripts = []
    for p in paths:
        if p.exists():
            scripts.append(json.loads(p.read_text()))

    if not scripts:
        print("No scripts found to score.")
        return

    results = gate_and_improve(scripts)

    # Save updated scripts
    for script in results:
        out_path = config.SCRIPTS_DIR / f"{script['id']}.json"
        out_path.write_text(json.dumps(script, indent=2))

    print(f"\n✅ Scored and improved {len(results)} scripts")


if __name__ == "__main__":
    main()
