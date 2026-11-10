"""Constrained tone controls: substantive fields are never rewritten."""
from dataclasses import asdict
from .engine import Critique


def present(critique: Critique, warmth: str = 'neutral', directness: str = 'explanation-first') -> dict:
    if warmth not in ('neutral', 'warm') or directness not in ('explanation-first', 'action-first'):
        raise ValueError('Unsupported presentation setting')
    sections = []
    for issue in critique.issues:
        parts = [issue.diagnosis, issue.recommendation]
        if directness == 'action-first': parts.reverse()
        sections.append({'issue_id': issue.issue_id, 'text': '\n'.join(parts),
                         'severity': issue.severity, 'uncertainty': issue.uncertainty,
                         'evidence': [asdict(e) for e in issue.evidence]})
    return {'intro': "Let's work through the evidence together." if warmth == 'warm' else 'Evidence review',
            'verdict': critique.verdict, 'rationale': critique.rationale,
            'sections': sections, 'evidence': [asdict(e) for e in critique.evidence],
            'controls': {'warmth': warmth, 'directness': directness},
            'method': 'fixed framing and field ordering; no generative rewrite'}


def from_record(record: dict) -> Critique:
    """Read an engine event's already-validated record for display, not assessment."""
    from .engine import Evidence, Issue
    issues=[]
    for issue in record['issues']:
        issues.append(Issue(**{**issue, 'evidence':tuple(Evidence(**e) for e in issue['evidence'])}))
    return Critique(**{**record,'evidence':tuple(Evidence(**e) for e in record['evidence']), 'issues':tuple(issues)})
