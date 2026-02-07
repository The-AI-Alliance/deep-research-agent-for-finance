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
        def __init__(self, disallow_system_change:bool=False):
            super().__init__(disallow_system_change=disallow_system_change)
            self.counts = []
            self.is_final = False
            self.others = {}

        def _do_update(self, 
            other: dict[str,any] = {},
            is_final: bool = False) -> any:
            self.counts.append(self.system.count)
            self.is_final = is_final
            self.others[self.system.count] = other

        def _after_set_system(self):
            self.counts = []
            self.is_final = False
            self.others = {}

    def test_Observer_construction(self):
        obs = TestObserver.CounterObserver()
        self.assertEqual(None, obs.system)

    def check_observation(self, obs: CounterObserver, counter: Counter, disallow_system_change: bool=False):
        expected_counts = [0]
        expected_others = {0: {}}
        for i in range(4):
            i1 = i+1
            counter.incr()
            self.assertNotEqual(None, obs.system)
            expected_counts.append(i1)
            expected_others[i1] = {}

            self.assertEqual(disallow_system_change, obs.disallow_system_change)
            self.assertEqual(False, obs.is_final)
            self.assertEqual(expected_counts, obs.counts)
            self.assertEqual(expected_others, obs.others)
        
        counter.incr()
        expected_counts.append(5)
        expected_others[5] = {'done', True}
        self.assertEqual(True, obs.is_final)
        self.assertEqual(expected_counts, obs.counts)
        self.assertEqual(expected_others, obs.others)

    def test_Observer_update(self):
        obs = TestObserver.CounterObserver()
        counter = TestObserver.Counter(obs)
        self.check_observation(obs, counter)

    def test_Observer_update_changes_system_when_allowed(self):
        obs = TestObserver.CounterObserver()
        counter1 = TestObserver.Counter(obs)
        self.check_observation(obs, counter1)
        counter2 = TestObserver.Counter(obs)
        self.check_observation(obs, counter2)

    def test_Observer_update_changes_system_when_disallowed(self):
        obs = TestObserver.CounterObserver(disallow_system_change=True)
        counter1 = TestObserver.Counter(obs)
        self.check_observation(obs, counter1, disallow_system_change=True)
        with self.assertRaises(ValueError):
            TestObserver.Counter(obs)

    def test_Observer_update_changes_system_when_disallowed_multiple_updates_with_None_allowed(self):
        obs = TestObserver.CounterObserver(disallow_system_change=True)
        for i in range(3):
            obs.update(None)
        self.assertEqual(None, obs.system)
        self.assertEqual(True, obs.disallow_system_change)
        self.assertEqual(False, obs.is_final)
        self.assertEqual([], obs.counts)
        self.assertEqual({}, obs.others)

if __name__ == "__main__":
    unittest.main()