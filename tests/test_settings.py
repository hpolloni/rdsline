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