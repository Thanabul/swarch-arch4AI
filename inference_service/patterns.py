"""Solutions for Task 2 (cascade) and Task 3 (cached predictions). Try the tasks yourself first.

Copy cascade() and the methods of PredictionCache into inference_service/patterns.py.
"""
from collections import OrderedDict


# ---------------------------------------------------------------- Task 2
async def cascade(text, small, large, threshold):
    """Two-phase prediction: ask the small model first, and the large model only
    when the small one is not confident enough.

    small.predict(text)        -> Prediction, fast, call it normally
    await large.predict(text)  -> Prediction, slow, limited capacity
    A Prediction is a dict: {"label": ..., "confidence": 0.5-1.0, "model": ...}

    Return the small model's prediction if its confidence >= threshold,
    otherwise return the large model's prediction.
    """
    first = small.predict(text)
    # >= because confidence equal to the threshold counts as confident.
    if first["confidence"] >= threshold:
        return first  # no large call, so no large-model cost for this review
    # large.predict is async: without await you get a coroutine, not a Prediction.
    return await large.predict(text)


# ---------------------------------------------------------------- Task 3
class PredictionCache:
    """Cached predictions: remember answers for texts we have already seen.

    - Two texts that differ only in upper/lower case or extra spaces are the
      same entry ("Delicious!" and "  delicious! ").
    - Keep at most max_size entries; when full, evict the least recently used.
    - Count hits and misses (the service reports them in /metrics).

    self._data is kept in order from least recently used (front) to most
    recently used (back).
    """

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        self._data = OrderedDict()

    @staticmethod
    def key(text):
        # split() drops spaces at the ends and splits on any run of spaces;
        # join() puts the words back with exactly one space between them.
        return " ".join(text.lower().split())

    def get(self, text):
        """Return the cached Prediction for text, or None. Count a hit or a miss."""
        key = self.key(text)
        if key in self._data:
            self._data.move_to_end(key)  # just used, so it moves to the back
            self.hits += 1
            return self._data[key]
        self.misses += 1
        return None

    def put(self, text, prediction):
        """Store prediction for text; evict the least recently used entry when over max_size."""
        key = self.key(text)
        self._data[key] = prediction
        self._data.move_to_end(key)  # needed when the key was already in the cache
        if len(self._data) > self.max_size:
            self._data.popitem(last=False)  # the front is the least recently used
