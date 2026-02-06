# Unit tests for the "observer" module.

import unittest
from dra.common.observer import Observer, Observers 

class TestObserver(unittest.TestCase):
    """
    Test Observer and Observers.
    """

    class Counter():
        def __init__(self, observer: Observer):
            self.count: int = -1
            self.observer = observer
            self.incr()

        def incr(self, delta: int = 1) -> int:
            self.count += delta
            is_final = False
            other = {}
            if self.count >= 5:
                is_final = True
                other = {'done', True}
            self.observer.update(self, other=other, is_final=is_final)
            return self.count

    class CounterObserver(Observer[Counter]):
        def __init__(self):
            super().__init__()
            self.counts = []
            self.is_final = False
            self.others = {}

        def _do_update(self, 
            other: dict[str,any] = {},
            is_final: bool = False) -> any:
            self.counts.append(self.system.count)
            self.is_final = is_final
            self.others[self.system.count] = other

    def test_Observer_construction(self):
        obs = TestObserver.CounterObserver()
        self.assertEqual(None, obs.system)

    def test_Observer_update(self):
        obs = TestObserver.CounterObserver()
        counter = TestObserver.Counter(obs)
        expected_counts = [0]
        expected_others = {0: {}}
        for i in range(4):
            i1 = i+1
            counter.incr()
            self.assertNotEqual(None, obs.system)
            expected_counts.append(i1)
            expected_others[i1] = {}
            self.assertEqual(False, obs.is_final)
            self.assertEqual(expected_counts, obs.counts)
            self.assertEqual(expected_others, obs.others)
        
        counter.incr()
        expected_counts.append(5)
        expected_others[5] = {'done', True}
        self.assertEqual(True, obs.is_final)
        self.assertEqual(expected_counts, obs.counts)
        self.assertEqual(expected_others, obs.others)

if __name__ == "__main__":
    unittest.main()