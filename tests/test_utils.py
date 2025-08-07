import sys
from pathlib import Path

# Add repository root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from streamline.utils import get_config_value, find_free_port


def test_get_config_value_returns_default_when_key_missing():
    config = {"existing_key": "value"}
    result = get_config_value(config, "missing_key", "default")
    assert result == "default"


def test_get_config_value_returns_existing_value_when_key_present():
    config = {"existing_key": "value"}
    result = get_config_value(config, "existing_key", "default")
    assert result == "value"


def test_find_free_port_returns_int():
    port = find_free_port()
    assert isinstance(port, int) and 0 < port < 65536
