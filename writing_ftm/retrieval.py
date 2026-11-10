"""Deterministic lexical baseline over user-supplied evidence documents."""
import math
import re
from collections import Counter


def retrieve(query: str, sources: dict[str, str], k: int = 3) -> list[dict]:
    if k < 1: raise ValueError('k must be positive')
    tokenize = lambda text: re.findall(r"[a-z0-9]+", text.lower())
    terms = set(tokenize(query))
    docs = {key: Counter(tokenize(value)) for key,value in sources.items()}
    scores=[]
    for key, counts in docs.items():
        score=sum((1+math.log(counts[t])) * math.log(1+len(docs)/(1+sum(t in d for d in docs.values())))
                  for t in terms if counts[t]) / math.sqrt(max(1,sum(counts.values())))
        if score > 0: scores.append({'source_id':key,'score':score,'text':sources[key]})
    return sorted(scores,key=lambda r:(-r['score'],r['source_id']))[:k]
