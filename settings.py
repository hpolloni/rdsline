import argparse
import yaml
import boto3
import os

class ConnectionSettings:
    def __init__(self, cluster_arn, secret_arn, database, client):
        self.cluster_arn = cluster_arn
        self.secret_arn = secret_arn
        self.database = database
        self.client = client

    def execute(self, sql):
        response = self.client.execute_statement(
            resourceArn = self.cluster_arn,
            database = self.database,
            secretArn = self.secret_arn,
            includeResultMetadata = True,
            sql=sql
        )
        return response

    def is_executable(self):
        return self.cluster_arn is not None and self.secret_arn is not None and self.database is not None

    def print(self):
        print("Type: rds-secretsmanager")
        print("Cluster arn: %s" % self.cluster_arn)
        print("Secret arn: %s" % self.secret_arn)
        print("Database: %s" % self.database)

def _get_region(cluster_arn):
    arn_parts = cluster_arn.split(':')
    return arn_parts[3]

def from_file(file):
    settings = yaml.safe_load(open(file, 'r'))
    if settings['type'] != 'rds-secretsmanager':
        raise Exception("Unsupported database connection type: %s" % settings['type'])
    region = _get_region(settings['cluster_arn'])
    client = boto3.Session(profile_name=settings['credentials']['profile']).client('rds-data', region_name=region)
    return ConnectionSettings(settings['cluster_arn'], settings['secret_arn'], settings['database'], client)

def from_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, required=False, help="Config file to read settings from")
    args = parser.parse_args()
    if args.config is not None:
        return from_file(args.config)
    return ConnectionSettings(None, None, None, boto3.client('rds-data'))
