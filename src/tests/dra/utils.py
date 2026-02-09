# Unit tests for the "markdown" UX module using Hypothesis for property-based testing.
# https://hypothesis.readthedocs.io/en/latest/

from hypothesis import given, strategies as st
import os, re
from random import sample


# Versions that filter or map in various ways and may return empty texts:

def nonempty_text(test_strategy = st.text, min_size=0, max_size=None):
    if min_size < 1:
        min_size = 1
    return test_strategy(min_size=min_size, max_size=max_size).filter(lambda s: len(s) > 0)

def no_brace_text(test_strategy = st.text, min_size=0, max_size=None):
    return test_strategy(min_size=min_size, max_size=max_size).map(lambda s: re.sub(r'[{}]+', '_', s))

def no_linefeeds_text(test_strategy = st.text, min_size=0, max_size=None):
    return test_strategy(min_size=min_size, max_size=max_size).map(lambda s: re.sub('[\n\r]', '_', s))

def no_slash_text(test_strategy = st.text, min_size=0, max_size=None):
    return test_strategy().map(lambda s: re.sub('/', '_', s))

# Versions that return non-empty texts:

def no_brace_nonempty_text(min_size=1, max_size=None):
    """Convenient wrapper around `no_brace_text(..., min_size=1, ...)`"""
    return nonempty_text(test_strategy=no_brace_text, min_size=min_size, max_size=max_size)

def no_linefeeds_nonempty_text(min_size=1, max_size=None):
    return nonempty_text(test_strategy=no_linefeeds_text, min_size=min_size, max_size=max_size)

def no_slash_nonempty_text(min_size=0, max_size=None):
    return nonempty_text(test_strategy=no_slash_text, min_size=min_size, max_size=max_size)

def parent_path_text(min_size=1, max_size=5):
    return st.lists(
        no_slash_nonempty_text(min_size=min_size, max_size=max_size), 
        min_size=min_size, max_size=max_size).map(
            lambda parents: os.path.join(*parents))

def no_leading_dots(min_size=1, max_size=5):
    """
    If the file part generated is `.` or `..`, then Path will resolve it to
    the current directory or the parent directory, respectively, which
    is not what we want.
    """
    return no_slash_nonempty_text().map(
        lambda s: f"_{s}" if s == '.' or s == '..' else s)

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

