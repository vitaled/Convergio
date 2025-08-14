"""
Lightweight conflict detector for conversation histories.
Detects basic contradictions across recent agent messages using heuristics.
"""

from __future__ import annotations

from typing import List, Dict, Any

OPPOSITES = [
	("approve", "reject"),
	("increase", "decrease"),
	("allow", "deny"),
	("on", "off"),
	("yes", "no"),
	("enable", "disable"),
	("positive", "negative"),
]


def detect_conflicts(conversation_history: List[Dict[str, Any]], window: int = 6) -> List[Dict[str, Any]]:
	"""Detect simple conflicts within the last N turns.
	Returns a list of conflict records with involved turns and terms.
	"""
	conflicts: List[Dict[str, Any]] = []
	if not conversation_history:
		return conflicts
	
	recent = conversation_history[-window:]
	# Normalize
	norm = [
		{
			"turn": e.get("turn"),
			"agent": (e.get("agent") or "").lower(),
			"content": (e.get("content") or "").lower(),
		}
		for e in recent
	]
	
	# Pairwise scan for opposite terms
	for i in range(len(norm)):
		ci = norm[i]
		for j in range(i + 1, len(norm)):
			cj = norm[j]
			for a, b in OPPOSITES:
				if (a in ci["content"] and b in cj["content"]) or (b in ci["content"] and a in cj["content"]):
					conflicts.append({
						"turns": (ci["turn"], cj["turn"]),
						"agents": (ci["agent"], cj["agent"]),
						"terms": (a, b),
						"type": "opposite_terms",
					})
	return conflicts