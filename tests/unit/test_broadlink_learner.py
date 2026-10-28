"""
Unit tests for BroadlinkLearner
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

import broadlink
from broadlink_learner import BroadlinkLearner


@pytest.fixture
def learner():
    """Create an authenticated learner with a mocked device"""
    l = BroadlinkLearner(
        host="192.168.100.152",
        mac=bytes.fromhex("b4430d9bd90f"),
        device_type=10002,
    )
    l._authenticated = True
    l.device = Mock()
    return l


@pytest.mark.unit
class TestRFLearningBlockedError:
    """Regression tests for issue #54: devices whose firmware blocks
    third-party RF learning must surface a clear error instead of a
    misleading timeout"""

    def test_sweep_rejected_sets_actionable_error(self, learner):
        """errno -4 from sweep_frequency produces the firmware-blocked message"""
        learner.device.sweep_frequency.side_effect = (
            broadlink.exceptions.CommandNotSupportedError(-4, "Command not supported")
        )

        result = learner.learn_rf_command(timeout=5)

        assert result is None
        assert learner.last_error == BroadlinkLearner.RF_LEARNING_BLOCKED_MESSAGE
        assert "third-party" in learner.last_error

    def test_fixed_frequency_rejected_sets_actionable_error(self, learner):
        """errno -4 from find_rf_packet produces the firmware-blocked message"""
        learner.device.find_rf_packet.side_effect = (
            broadlink.exceptions.CommandNotSupportedError(-4, "Command not supported")
        )

        result = learner.learn_rf_command_fixed_frequency(433.92, timeout=5)

        assert result is None
        assert learner.last_error == BroadlinkLearner.RF_LEARNING_BLOCKED_MESSAGE

    def test_other_errors_get_generic_message(self, learner):
        """Unrelated failures keep the generic error message"""
        learner.device.sweep_frequency.side_effect = RuntimeError("network down")

        result = learner.learn_rf_command(timeout=5)

        assert result is None
        assert learner.last_error == "Error during RF learning: network down"
        assert learner.last_error != BroadlinkLearner.RF_LEARNING_BLOCKED_MESSAGE

    def test_timeout_leaves_last_error_none(self, learner):
        """A genuine sweep timeout does not set a device error"""
        learner.device.sweep_frequency.return_value = None
        learner.device.check_frequency.return_value = (False, 433.92)

        result = learner.learn_rf_command(timeout=3)

        assert result is None
        assert learner.last_error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
