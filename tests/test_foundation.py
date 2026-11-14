"""Regression tests for process lifetime, signals, and metadata rejection."""

from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_metadata import validate  # noqa: E402


class MetadataTests(unittest.TestCase):
    def test_valid_checkout(self):
        validate(ROOT)

    def test_invalid_manifests_fail_cli(self):
        for key, value in (("arch", ["amd64"]), ("version", 0.1),
                           ("homeassistant_api", True), ("options", {"mode": "active"})):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                shutil.copytree(ROOT / "adaptive_heating_controller", root / "adaptive_heating_controller")
                shutil.copyfile(ROOT / "repository.yaml", root / "repository.yaml")
                path = root / "adaptive_heating_controller/config.yaml"
                manifest = yaml.safe_load(path.read_text())
                manifest[key] = value
                path.write_text(yaml.safe_dump(manifest))
                result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_metadata.py"),
                                         str(root)], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("ValidationError", result.stderr)


class LifecycleTests(unittest.TestCase):
    def test_start_stop_and_restart_for_both_signals(self):
        for stop_signal in (signal.SIGTERM, signal.SIGINT):
            for _ in range(2):
                with self.subTest(signal=stop_signal):
                    process = subprocess.Popen([sys.executable, "-m", "app"],
                                               cwd=ROOT / "adaptive_heating_controller",
                                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               text=True)
                    try:
                        self.assertTrue(select.select([process.stdout], [], [], 5)[0], "No startup log")
                        startup = process.stdout.readline().strip()
                        self.assertEqual(startup, "Adaptive Heating Controller 0.1.0 started (mode=read-only)")
                        with self.assertRaises(subprocess.TimeoutExpired):
                            process.wait(timeout=0.25)
                        process.send_signal(stop_signal)
                        output, _ = process.communicate(timeout=5)
                        self.assertEqual(process.returncode, 0)
                        self.assertEqual(output.strip(), "Adaptive Heating Controller 0.1.0 stopped gracefully (mode=read-only)")
                    finally:
                        if process.poll() is None:
                            process.kill()
                            process.communicate()


if __name__ == "__main__":
    unittest.main()
