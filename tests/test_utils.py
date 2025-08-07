import sys
from pathlib import Path

# Add the Utils directory to the Python path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent / 'Utils'))

from utils import get_config_value


def test_get_config_value_returns_default_when_key_missing():
    config = {'existing_key': 'value'}
    result = get_config_value(config, 'missing_key', 'default')
    assert result == 'default'


def test_get_config_value_returns_existing_value_when_key_present():
    config = {'existing_key': 'value'}
    result = get_config_value(config, 'existing_key', 'default')
    assert result == 'value'
