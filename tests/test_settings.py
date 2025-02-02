import os
from collections import namedtuple
from unittest.mock import patch
from rdsline import settings
from rdsline.connections import NoopConnection

class DummyClient:
    pass


DUMMY_CLIENT = DummyClient()
def dummy_client_provider(profile: str, region: str) -> DummyClient:
    """Dummy client provider that accepts any profile/region combination."""
    return DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_read_settings_from_file(_: None) -> None:
    connection = settings.from_file('config.yaml', client_provider=dummy_client_provider)
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'
    assert connection.client == DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_fails_for_unknown_type(_: None) -> None:
    try:
        settings.from_file('tests/configs/unknown_type.yaml')
        assert False
    except Exception as e:
        assert "fake-unknown-type" in str(e)


@patch('rdsline.settings.create_boto3_session')
def test_fails_for_missing_setting(_: None) -> None:
    try:
        settings.from_file('tests/configs/missing_cluster_arn.yaml')
        assert False
    except KeyError as e:
        pass


Args = namedtuple("Args", "config")
@patch('rdsline.settings.create_boto3_session')
def test_can_get_settings_from_args(_: None) -> None:
    args = Args("config.yaml")
    connection = settings.from_args(args, dummy_client_provider)
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'
    assert connection.client == DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_gets_from_default_file(_: None) -> None:
    assert settings.DEFAULT_CONFIG_FILE == os.path.expanduser("~/.rdsline")
    args = Args(None)
    connection = settings.from_args(args, dummy_client_provider, default_config_file="config.yaml")
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'
    assert connection.client == DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_gets_noop_if_else_fails(_: None) -> None:
    args = Args(None)
    connection = settings.from_args(args, dummy_client_provider, default_config_file="unexistant_file.yaml")
    assert type(connection) == NoopConnection


# New tests for multi-profile feature
@patch('rdsline.settings.create_boto3_session')
def test_multi_profile_settings(_: None) -> None:
    """Test the new Settings class with multiple profiles."""
    s = settings.Settings(client_provider=dummy_client_provider)
    s.load_from_file('tests/configs/multi_profile.yaml')
    
    # Check initial state
    assert s.get_current_profile() == 'default'
    assert len(s.get_profile_names()) == 2
    assert set(s.get_profile_names()) == {'default', 'staging'}
    
    # Check default profile connection
    assert s.connection.cluster_arn == 'arn:aws:rds:us-east-1:123456789012:cluster:default-cluster'
    assert s.connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:123456789012:secret:default-secret'
    assert s.connection.database == 'default_db'
    assert s.connection.client == DUMMY_CLIENT
    
    # Switch to staging profile
    s.switch_profile('staging')
    assert s.get_current_profile() == 'staging'
    assert s.connection.cluster_arn == 'arn:aws:rds:us-west-2:123456789012:cluster:staging-cluster'
    assert s.connection.secret_arn == 'arn:aws:secretsmanager:us-west-2:123456789012:secret:staging-secret'
    assert s.connection.database == 'staging_db'
    assert s.connection.client == DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_multi_profile_invalid_profile(_: None) -> None:
    """Test handling of invalid profile names."""
    s = settings.Settings(client_provider=dummy_client_provider)
    s.load_from_file('tests/configs/multi_profile.yaml')
    
    try:
        s.switch_profile('nonexistent')
        assert False, "Should have raised an exception for nonexistent profile"
    except Exception as e:
        assert "Profile 'nonexistent' not found" in str(e)


@patch('rdsline.settings.create_boto3_session')
def test_backward_compatibility(_: None) -> None:
    """Test that old single-profile config files still work."""
    s = settings.Settings(client_provider=dummy_client_provider)
    s.load_from_file('tests/configs/old_format.yaml')
    
    # Should convert old format to new format under 'default' profile
    assert s.get_current_profile() == 'default'
    assert len(s.get_profile_names()) == 1
    assert s.get_profile_names() == ['default']
    
    # Check connection details
    assert s.connection.cluster_arn == 'arn:aws:rds:us-east-1:123456789012:cluster:old-cluster'
    assert s.connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:123456789012:secret:old-secret'
    assert s.connection.database == 'old_db'
    assert s.connection.client == DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_missing_default_profile(_: None) -> None:
    """Test that loading a config without a default profile uses the first available profile."""
    s = settings.Settings(client_provider=dummy_client_provider, initial_profile='staging')
    
    s.load_from_file('tests/configs/missing_default.yaml')
    
    # Should use 'staging' profile since it was specified
    assert s.get_current_profile() == 'staging'
    assert s.connection.cluster_arn == 'arn:aws:rds:us-west-2:123456789012:cluster:staging-cluster'
    assert s.connection.secret_arn == 'arn:aws:secretsmanager:us-west-2:123456789012:secret:staging-secret'
    assert s.connection.database == 'staging_db'
    assert s.connection.client == DUMMY_CLIENT


@patch('rdsline.settings.create_boto3_session')
def test_missing_specified_profile(_: None) -> None:
    """Test that loading a config without the specified profile uses the first available profile."""
    s = settings.Settings(client_provider=dummy_client_provider, initial_profile='nonexistent')
    
    s.load_from_file('tests/configs/missing_default.yaml')
    
    # Should use 'staging' profile since it's the only one available
    assert s.get_current_profile() == 'staging'
    assert s.connection.cluster_arn == 'arn:aws:rds:us-west-2:123456789012:cluster:staging-cluster'
    assert s.connection.secret_arn == 'arn:aws:secretsmanager:us-west-2:123456789012:secret:staging-secret'
    assert s.connection.database == 'staging_db'
    assert s.connection.client == DUMMY_CLIENT


def test_add_profile() -> None:
    """Test adding a new profile."""
    s = settings.Settings(client_provider=dummy_client_provider)
    
    new_profile = {
        "type": "rds-secretsmanager",
        "cluster_arn": "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",
        "secret_arn": "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",
        "database": "test_db",
        "credentials": {
            "profile": "test"
        }
    }
    
    s.add_profile("test", new_profile)
    assert "test" in s.profiles
    assert s.profiles["test"] == new_profile


def test_add_profile_duplicate() -> None:
    """Test that adding a duplicate profile raises an exception."""
    s = settings.Settings(client_provider=dummy_client_provider)
    
    profile = {
        "type": "rds-secretsmanager",
        "cluster_arn": "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",
        "secret_arn": "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",
        "database": "test_db"
    }
    
    s.add_profile("test", profile)
    try:
        s.add_profile("test", profile)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "already exists" in str(e)


def test_add_profile_missing_fields() -> None:
    """Test that adding a profile with missing fields raises an exception."""
    s = settings.Settings(client_provider=dummy_client_provider)
    
    profile = {
        "type": "rds-secretsmanager",
        "cluster_arn": "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",
        # missing secret_arn and database
    }
    
    try:
        s.add_profile("test", profile)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "Missing required fields" in str(e)
        assert "secret_arn" in str(e)
        assert "database" in str(e)


def test_add_profile_invalid_type() -> None:
    """Test that adding a profile with an invalid type raises an exception."""
    s = settings.Settings(client_provider=dummy_client_provider)
    
    profile = {
        "type": "invalid-type",
        "cluster_arn": "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",
        "secret_arn": "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",
        "database": "test_db"
    }
    
    try:
        s.add_profile("test", profile)
        assert False, "Should have raised an exception"
    except Exception as e:
        assert "Unsupported database connection type" in str(e)


@patch("builtins.open")
@patch("yaml.safe_dump")
def test_save_to_file(mock_safe_dump, mock_open) -> None:
    """Test saving profiles to a file."""
    s = settings.Settings(client_provider=dummy_client_provider)
    
    profile = {
        "type": "rds-secretsmanager",
        "cluster_arn": "arn:aws:rds:us-west-2:123456789012:cluster:test-cluster",
        "secret_arn": "arn:aws:secretsmanager:us-west-2:123456789012:secret:test-secret",
        "database": "test_db"
    }
    
    s.add_profile("test", profile)
    s.save_to_file("test_config.yaml")
    
    mock_open.assert_called_once_with("test_config.yaml", "w", encoding="utf-8")
    mock_safe_dump.assert_called_once()
    dumped_config = mock_safe_dump.call_args[0][0]
    assert "profiles" in dumped_config
    assert "test" in dumped_config["profiles"]
    assert dumped_config["profiles"]["test"] == profile