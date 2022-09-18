import os
from collections import namedtuple
from rdsline import settings
from rdsline.connections import NoopConnection

class DummyClient:
    pass


DUMMY_CLIENT = DummyClient()
def dummy_client_provider(profile, region):
    assert profile == 'default'
    assert region == 'us-east-1'
    return DUMMY_CLIENT


def test_read_settings_from_file():
    connection = settings.from_file('config.yaml', client_provider=dummy_client_provider)
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'
    assert connection.client == DUMMY_CLIENT


def test_fails_for_unknown_type():
    try:
        settings.from_file('tests/configs/unknown_type.yaml')
        assert False
    except Exception as e:
        assert "fake-unknown-type" in str(e)


def test_fails_for_missing_setting():
    try:
        settings.from_file('tests/configs/missing_cluster_arn.yaml')
        assert False
    except KeyError as e:
        pass


Args = namedtuple("Args", "config")
def test_can_get_settings_from_args():
    args = Args("config.yaml")
    connection = settings.from_args(args, dummy_client_provider)
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'
    assert connection.client == DUMMY_CLIENT


def test_gets_from_default_file():
    assert settings.DEFAULT_CONFIG_FILE == os.path.expanduser("~/.rdsline")
    args = Args(None)
    connection = settings.from_args(args, dummy_client_provider, default_config_file="config.yaml")
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'
    assert connection.client == DUMMY_CLIENT


def test_gets_noop_if_else_fails():
    args = Args(None)
    connection = settings.from_args(args, dummy_client_provider, default_config_file="unexistant_file.yaml")
    assert type(connection) == NoopConnection