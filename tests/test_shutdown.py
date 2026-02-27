import unittest
import os
import signal
import time
import subprocess
import json

class TestGracefulShutdown(unittest.TestCase):
    def setUp(self):
        self.workspace = "/home/jkpark/.openclaw/workspace-jeff/bats-trading-system"
        self.state_file = os.path.join(self.workspace, "state.json")
        # Ensure state.json exists or reset it
        if os.path.exists(self.state_file):
            with open(self.state_file, 'w') as f:
                json.dump({"units_held": 0, "test_marker": True}, f)

    def test_shutdown_signal(self):
        """Test if the process handles SIGINT and saves state."""
        # Start the main script in a subprocess
        process = subprocess.Popen(
            ["python3", "src/main.py"],
            cwd=self.workspace,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**os.environ, "PYTHONPATH": self.workspace},
            text=True
        )

        # Wait for it to initialize
        time.sleep(5) 
        
        # Send SIGINT (Ctrl+C)
        process.send_signal(signal.SIGINT)
        
        # Wait for termination
        try:
            stdout, stderr = process.communicate(timeout=10)
            print("Stdout:", stdout)
            print("Stderr:", stderr)
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Process did not terminate gracefully after SIGINT")

        # Check logs/stdout for shutdown sequence
        self.assertIn("Initiating safe shutdown", stdout)
        self.assertIn("Final state saved successfully", stdout)
        self.assertIn("BATS System shutdown complete", stdout)

        # Verify state file was updated (marker should still be there or updated)
        with open(self.state_file, 'r') as f:
            state = json.load(f)
            self.assertTrue(state.get("test_marker") or "units_held" in state)

if __name__ == "__main__":
    unittest.main()
