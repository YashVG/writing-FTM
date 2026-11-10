"""Diagnostic repetition measures; not a semantic-quality score."""
from collections import Counter
import re


def repetition_metrics(text, n=8):
    words=re.findall(r"\w+",text.lower())
    grams=[tuple(words[i:i+n]) for i in range(max(0,len(words)-n+1))]
    repeated=sum(count-1 for count in Counter(grams).values())
    fraction=repeated/len(grams) if grams else 0.0
    return {'repeated_8gram_fraction':fraction,'repetition_flag':len(grams)>=16 and fraction>=.2}
