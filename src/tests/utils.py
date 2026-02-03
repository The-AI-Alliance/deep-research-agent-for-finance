# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import os, re
from random import sample

nonempty_text = st.text().filter(lambda s: len(s) > 0)
no_brace_text = st.text().map(lambda s: re.sub(r'[{}]+', '_', s))
no_brace_non_empty_text = no_brace_text.filter(lambda s: len(s) > 0)
no_linefeeds_text = st.text().map(lambda s: re.sub('[\n\r]', '_', s))
nonempty_no_linefeeds_text = nonempty_text.map(lambda s: re.sub('[\n\r]', '_', s))
nonempty_no_slash_text = nonempty_text.map(lambda s: re.sub('/', '_', s))
parent_path_text = st.lists(nonempty_no_slash_text, min_size=1, max_size=5).map(
    lambda parents: os.path.join(*parents))

def make_n_samples(samples: list[any], n: int) -> list[str]:
    """
    Return a n-length list taken randomly from the samples list,
    which can be shorter than n.
    """
    slen = len(samples)
    passes = int(n/slen)+1
    ss = []
    for _ in range(passes):
        ss.extend(sample(samples, slen))
    ssn = ss[:n]
    assert len(ssn) == n
    return ssn

