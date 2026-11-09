# SPDX-License-Identifier: Apache-2.0
# Experimental TV navigation work; see PROVENANCE.md.
"""Regression tests: no real device calls, fake clock/transport only."""
import pathlib
import copy
import subprocess
import unittest
from unittest.mock import patch
import runner
from runner import Stop, execute
from adb_adapter import Adb
from test_runner import M, Device

class Clock:
    def __init__(self): self.now = 0.0
    def monotonic(self): return self.now
    def sleep(self, seconds): self.now += seconds

class Adapter(Adb):
    def __init__(self, clock):
        super().__init__(M, pathlib.Path('/tmp/tv-regression-unused-stop'))
        self.clock = clock
        self.sent = []
        self.state_delay = 0
        self.cancel = False
    def cancelled(self): return self.cancel
    def state(self):
        self.clock.now += self.state_delay
        return M['package'], M['activity'], M['version']
    def call(self, *args, timeout=5):
        self.sent.append((self.clock.now, args))
        return b''

class DeadlineTests(unittest.TestCase):
    def test_runner_rechecks_deadline_after_blocking_state(self):
        c = Clock()
        class Slow(Device):
            def state(self):
                c.now += 31
                return super().state()
            def keys(self, *args, **kwargs): self.calls.append(args[0])
        d = Slow()
        with patch.object(runner.time, 'monotonic', c.monotonic):
            with self.assertRaises(Stop): execute(M, d)
        self.assertEqual(d.calls, [], 'No navigation after admission state exceeded deadline')

    def test_runner_passes_absolute_deadlines_including_select_age(self):
        c = Clock()
        class Capture(Device):
            def keys(self, keys, spacing_ms, settle_ms, *, valid_until):
                self.calls.append((keys, valid_until))
        d = Capture()
        with patch.object(runner.time, 'monotonic', c.monotonic):
            self.assertTrue(execute(M, d)['verified'])
        self.assertEqual(d.calls[0][1], 30.0)
        self.assertEqual(d.calls[1][1], 1.0)

    def test_adapter_rechecks_select_age_after_blocking_state(self):
        c = Clock(); d = Adapter(c); d.state_delay = 2
        with patch.object(runner.time, 'monotonic', c.monotonic), patch.object(runner.time, 'sleep', c.sleep):
            with self.assertRaises(Stop): d.keys([23], 0, 200, valid_until=1.0)
        self.assertEqual(d.sent, [], 'Stale focus must not lead to SELECT')

    def test_adapter_rechecks_each_navigation_key(self):
        c = Clock(); d = Adapter(c); d.state_delay = 0.6
        with patch.object(runner.time, 'monotonic', c.monotonic), patch.object(runner.time, 'sleep', c.sleep):
            with self.assertRaises(Stop): d.keys([19, 19], 200, 200, valid_until=1.0)
        self.assertEqual(len(d.sent), 1, 'First key fits; second exceeds deadline')

    def test_adapter_expired_before_state_sends_nothing(self):
        c = Clock(); c.now = 2; d = Adapter(c)
        with patch.object(runner.time, 'monotonic', c.monotonic):
            with self.assertRaises(Stop): d.keys([19], 200, 200, valid_until=1.0)
        self.assertEqual(d.sent, [])

class ObservationAdapter(Adb):
    def __init__(self, fail_marker=False, fail_read=False):
        super().__init__(M, pathlib.Path('/tmp/tv-regression-unused-stop'))
        self.calls = []; self.fail_marker = fail_marker; self.fail_read = fail_read
    def call(self, *args, timeout=5):
        self.calls.append(args)
        if args[:3] == ('shell', 'uiautomator', 'dump'):
            if self.fail_marker: return b'ERROR: null root node returned by UiTestAutomationBridge.'
            return ('UI hierchary dumped to: ' + args[3]).encode()
        if args[:2] == ('shell', 'cat'):
            if self.fail_read: raise subprocess.CalledProcessError(1, args)
            return b'<hierarchy/>'
        return b''

class ObservationTests(unittest.TestCase):
    def test_observe_uses_unique_paths_and_removes_each(self):
        d = ObservationAdapter()
        self.assertEqual(d.observe(), b'<hierarchy/>')
        self.assertEqual(d.observe(), b'<hierarchy/>')
        paths = [a[3] for a in d.calls if a[:3] == ('shell','uiautomator','dump')]
        self.assertEqual(len(set(paths)), 2)
        for p in paths: self.assertIn(('shell','rm','-f',p), d.calls)

    def test_error_marker_does_not_read_stale_file(self):
        d = ObservationAdapter(fail_marker=True)
        with self.assertRaises(Stop): d.observe()
        self.assertFalse(any(a[:2] == ('shell','cat') for a in d.calls))

    def test_read_failure_cleans_snapshot(self):
        d = ObservationAdapter(fail_read=True)
        with self.assertRaises(subprocess.CalledProcessError): d.observe()
        p = next(a[3] for a in d.calls if a[:3] == ('shell','uiautomator','dump'))
        self.assertIn(('shell','rm','-f',p), d.calls)

class IdentityTests(unittest.TestCase):
    def test_package_rejects_shell_metacharacters(self):
        for value in ['com.example;id','com.example evil','com.example$(id)']:
            with self.subTest(value=value):
                m = copy.deepcopy(M); m['package'] = value
                with self.assertRaises(ValueError): runner.validate_mapping(m)

    def test_activity_rejects_shell_metacharacters(self):
        for value in ['com.example.Player;id','com.example Player','com.example.$(id)']:
            with self.subTest(value=value):
                m = copy.deepcopy(M); m['activity'] = value
                with self.assertRaises(ValueError): runner.validate_mapping(m)

if __name__ == '__main__': unittest.main()
