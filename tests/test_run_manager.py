import subprocess
import threading
import time
import unittest

from src.run_manager import RunManager


def wait_finished(manager):
    deadline = time.monotonic() + 3
    while manager.status()['status'] == 'running' and time.monotonic() < deadline:
        time.sleep(0.01)
    return manager.status()


class RunManagerTests(unittest.TestCase):
    def test_rejects_unknown_actions(self):
        with self.assertRaises(ValueError):
            RunManager().start('powershell -command anything')

    def test_tests_capture_summary(self):
        def fake_run(command, **kwargs):
            self.assertEqual(command[1:3], ['-m', 'unittest'])
            self.assertEqual(kwargs['env']['PYTHONIOENCODING'], 'utf-8')
            return subprocess.CompletedProcess(command, 0, 'Ran 34 tests in 0.1s\n\nOK\n')

        manager = RunManager(fake_run)
        self.assertIsNotNone(manager.start('tests'))
        status = wait_finished(manager)
        self.assertEqual(status['status'], 'completed')
        self.assertEqual(status['tests_summary'], {'count': 34, 'ok': True})

    def test_only_one_job_at_a_time(self):
        entered, release = threading.Event(), threading.Event()

        def fake_run(command, **kwargs):
            entered.set()
            release.wait(timeout=3)
            return subprocess.CompletedProcess(command, 0, 'OK')

        manager = RunManager(fake_run)
        manager.start('fixed_gui')
        self.assertTrue(entered.wait(2))
        self.assertIsNone(manager.start('tests'))
        release.set()
        self.assertEqual(wait_finished(manager)['status'], 'completed')

    def test_failure_stops_comparison(self):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 1, 'Falha simulada')

        manager = RunManager(fake_run)
        manager.start('compare')
        status = wait_finished(manager)
        self.assertEqual(status['status'], 'failed')
        self.assertEqual(len(calls), 1)
        self.assertEqual(status['results'][0]['exit_code'], 1)


if __name__ == '__main__':
    unittest.main()
