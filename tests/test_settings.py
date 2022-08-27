from rdsline import settings

def dummy_client_provider(profile, region):
    assert profile == 'default'
    assert region == 'us-east-1'


def test_read_settings_from_file():
    connection = settings.from_file('config.yaml', client_provider=dummy_client_provider)
    assert connection.cluster_arn == 'arn:aws:rds:us-east-1:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>'
    assert connection.secret_arn == 'arn:aws:secretsmanager:us-east-1:<ACCOUNT_ID>:secret:<SECRET_ID>'
    assert connection.database == 'DATABASE_NAME'


