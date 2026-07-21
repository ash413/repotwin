"""Turns a natural-language question into a graph query, runs impact analysis,
and (if ANTHROPIC_API_KEY is set) asks Claude to narrate the findings in plain
English. Falls back to a template-based narrative if no key is configured,
so the tool works with zero external dependencies for the hackathon demo.
"""

import os
import re
import json
from typing import Optional

from investigator.impact_analysis import find_node, analyze_impact, ImpactReport

REMOVAL_PATTERNS = [
    r"what (?:breaks|happens) if i (?:remove|drop|delete|kill|disable) (.+?)\??$",
    r"what depends on (?:the )?(.+?)\??$",
    r"can i replace (.+?) with (.+?)\??$",
    r"which components are affected if (.+?) changes\??$",
    r"where could this (?:application|app|system) fail if (.+?) goes down\??$",
]


def extract_target_entity(question: str) -> Optional[str]:
    q = question.lower().strip()
    for pattern in REMOVAL_PATTERNS:
        m = re.search(pattern, q)
        if m:
            return m.group(1).strip()
    # fallback: strip common question words and hope the remainder is an entity
    stripped = re.sub(r"^(what|which|where|can|does|is)\b.*?\b(if|is|are)\b", "", q).strip()
    return stripped or None


def _template_narrative(report: ImpactReport) -> str:
    direct_labels = ", ".join(m.label for m in report.directly_affected[:6]) or "none found"
    lines = [
        f"Removing/changing **{report.target}** directly affects {len(report.directly_affected)} "
        f"module(s): {direct_labels}.",
    ]
    if report.transitively_affected:
        lines.append(
            f"Transitively, {len(report.transitively_affected)} more module(s) are reachable "
            f"downstream of those."
        )
    if report.affected_routes:
        route_list = ", ".join(f"{r['method']} {r.get('path') or '(unknown path)'}" for r in report.affected_routes[:5])
        lines.append(f"{len(report.affected_routes)} API route(s) are impacted: {route_list}.")
    lines.append(f"Risk level: {report.risk_level.upper()} — " + "; ".join(report.risk_reasons))
    lines.append(f"Recommendation: {report.recommendation}")
    return "\n\n".join(lines)


def _claude_narrative(report: ImpactReport, question: str) -> Optional[str]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        payload = {
            "target": report.target,
            "target_type": report.target_type,
            "direct": [{"module": m.node_id, "evidence_count": len(m.evidence)} for m in report.directly_affected],
            "transitive": [{"module": m.node_id} for m in report.transitively_affected],
            "affected_routes": report.affected_routes,
            "risk_level": report.risk_level,
            "risk_reasons": report.risk_reasons,
        }
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": (
                    f"An engineer asked: \"{question}\"\n\n"
                    f"Here is the graph-derived impact data (ground truth, do not contradict it):\n"
                    f"{json.dumps(payload, indent=2)}\n\n"
                    "Write a concise, engineer-facing explanation (under 180 words) of what breaks, "
                    "why, and what to do about it. Do not invent modules or evidence not listed above."
                ),
            }],
        )
        return "".join(b.text for b in msg.content if b.type == "text")
    except Exception:
        return None


def answer_question(g, question: str) -> dict:
    entity = extract_target_entity(question)
    if not entity:
        return {"error": "Could not identify a target component in the question.", "question": question}

    node_id = find_node(g, entity)
    if not node_id:
        return {"error": f"No component matching '{entity}' was found in the scanned repository.",
                "question": question, "extracted_entity": entity}

    report = analyze_impact(g, node_id)
    narrative = _claude_narrative(report, question) or _template_narrative(report)

    return {
        "question": question,
        "extracted_entity": entity,
        "resolved_node": node_id,
        "narrative": narrative,
        "report": {
            "target": report.target,
            "target_type": report.target_type,
            "risk_level": report.risk_level,
            "risk_reasons": report.risk_reasons,
            "recommendation": report.recommendation,
            "directly_affected": [
                {"node_id": m.node_id, "label": m.label, "distance": m.distance, "evidence": m.evidence}
                for m in report.directly_affected
            ],
            "transitively_affected": [
                {"node_id": m.node_id, "label": m.label, "distance": m.distance}
                for m in report.transitively_affected
            ],
            "affected_routes": report.affected_routes,
        },
    }
