# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import pytest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_agent(message: str) -> subprocess.CompletedProcess:
    """Helper to run the agent with a single prompt using agents-cli."""
    cmd = ["uv", "run", "agents-cli", "run", message]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=PROJECT_DIR,
    )


@pytest.fixture(scope="session", autouse=True)
def manage_agents_server() -> None:
    """Fixture to start and manage the agents-cli background server.

    Ensures that the server is running during the test suite to preserve in-memory
    state across multiple commands, and stops it cleanly at the end.
    """
    # Force stop any lingering server before starting
    subprocess.run(
        ["uv", "run", "agents-cli", "run", "--stop-server"],
        cwd=PROJECT_DIR,
        capture_output=True,
    )

    # Start persistent server with a dummy command
    subprocess.run(
        ["uv", "run", "agents-cli", "run", "Hello", "--start-server"],
        cwd=PROJECT_DIR,
        capture_output=True,
    )

    yield

    # Clean up and stop server at the end of session
    subprocess.run(
        ["uv", "run", "agents-cli", "run", "--stop-server"],
        cwd=PROJECT_DIR,
        capture_output=True,
    )


def test_redeem_discount_success() -> None:
    """Test that a registered user can successfully redeem a valid discount code."""
    res = run_agent("Please redeem discount code WELCOME50 for user user_123")
    assert res.returncode == 0
    # Assert tool-call execution in stdout logs
    assert "redeem_discount" in res.stdout
    assert "WELCOME50" in res.stdout
    assert "user_123" in res.stdout
    # Assert successful agent response outcome
    assert "Success" in res.stdout or "succeeded" in res.stdout or "redeemed" in res.stdout


def test_redeem_discount_guest_denied() -> None:
    """Test that guest accounts (starting with guest_) are blocked from redeeming discounts."""
    res = run_agent("Please redeem discount code WELCOME50 for user guest_abc")
    assert res.returncode == 0
    assert "redeem_discount" in res.stdout
    # Assert the outcome specifies the permission error
    assert "registered user account required" in res.stdout.lower() or "guest" in res.stdout.lower()


def test_redeem_discount_invalid_code() -> None:
    """Test that invalid discount codes are rejected."""
    res = run_agent("Please redeem discount code INVALID123 for user user_123")
    assert res.returncode == 0
    assert "redeem_discount" in res.stdout
    # Assert the outcome specifies that the code is invalid
    assert "invalid" in res.stdout.lower() or "error" in res.stdout.lower()


def test_redeem_discount_double_redemption() -> None:
    """Test that a single-use discount code cannot be redeemed twice."""
    # First redemption for user_123 should succeed
    res1 = run_agent("Please redeem discount code SUMMER20 for user user_123")
    assert res1.returncode == 0
    assert "redeem_discount" in res1.stdout
    assert "Success" in res1.stdout or "succeeded" in res1.stdout or "redeemed" in res1.stdout

    # Second redemption of same code for user_456 should fail
    res2 = run_agent("Please redeem discount code SUMMER20 for user user_456")
    assert res2.returncode == 0
    assert "redeem_discount" in res2.stdout
    # Assert that the outcome specifies the code was already redeemed
    assert "already" in res2.stdout.lower() or "redeemed" in res2.stdout.lower()
