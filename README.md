[![Coverage Status](https://coveralls.io/repos/github/hpolloni/rdsline/badge.svg?branch=master)](https://coveralls.io/github/hpolloni/rdsline?branch=master)
[![PyPI version](https://badge.fury.io/py/rdsline.svg)](https://badge.fury.io/py/rdsline)

# rdsline

A powerful and interactive REPL (Read-Eval-Print Loop) for Amazon RDS Data API that simplifies database interactions and query execution. This tool enables seamless interaction with your RDS databases through a convenient command-line interface.

## Features

- 🚀 Interactive REPL environment for RDS Data API
- 🔄 Pipe redirection support with TSV output format
- ⚙️ Flexible configuration through YAML files
- 📊 Pretty-printed table output for query results
- 🔌 Easy connection management and switching
- 🔄 Multiple profile support with easy switching
- 🐛 Enhanced debugging capabilities
- ✨ Support for Python 3.8 through 3.12

## Prerequisites

- Python 3.8 or higher
- AWS credentials configured (`~/.aws/credentials` or environment variables)
- Access to an Amazon RDS database
- Required permissions for RDS Data API

## Install

### Homebrew
```bash
$ brew tap hpolloni/rdsline
$ brew install rdsline
```

### Pip
```bash
$ pip install rdsline
```

## Configuration

The default configuration file location is `~/.rdsline`. You can specify a different configuration file using the `--config` flag.

### Configuration File Example

```yaml
# Example config.yaml
default:
  resource_arn: "arn:aws:rds:region:account:cluster:database-name"
  secret_arn: "arn:aws:secretsmanager:region:account:secret:secret-name"
  database: "your_database_name"
  region: "your-region"

# Additional profiles can be added
staging:
  resource_arn: "arn:aws:rds:region:account:cluster:staging-database"
  secret_arn: "arn:aws:secretsmanager:region:account:secret:staging-secret"
  database: "staging_db"
  region: "your-region"
```

## Usage

### Basic Commands

Inside the REPL, you have access to several dot commands:

```
.help    - Display available commands
.quit    - Exit the REPL
.profile - Manage and switch between different connection profiles
.debug   - Toggle debug mode for troubleshooting
```

### Query Examples

1. Simple query with automatic formatting:
```sql
> select current_date;
+---------------+
| current_date  |
|---------------|
| 2025-02-01    |
+---------------+
```

2. Multi-line queries (end with semicolon or empty line):
```sql
> select 
    user_id,
    username
  from users
  where active = true;
+----------+----------+
| user_id  | username |
|----------|----------|
| 1        | hpolloni |
| 2        | alice    |
+----------+----------+
```

3. Pipe usage for scripting:
```bash
$ echo "select count(*) from users;" | rdsline
42
```

## Troubleshooting

### Common Issues

1. **Connection Issues**
   - Verify AWS credentials are properly configured
   - Ensure resource and secret ARNs are correct
   - Check VPC and security group settings

2. **Permission Errors**
   - Verify IAM roles have necessary permissions for RDS Data API
   - Ensure Secret Manager access is properly configured

3. **Configuration Issues**
   - Validate YAML syntax in config file
   - Confirm all required fields are present
   - Check file permissions on config file

### Debug Mode

Run rdsline with debug logging enabled:
```bash
rdsline --debug
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/hpolloni/rdsline/blob/master/CONTRIBUTING.md) for details on how to:
- Submit bug reports
- Request features
- Submit pull requests
- Set up development environment

## License

This project is licensed under the [MIT License](https://github.com/hpolloni/rdsline/blob/master/LICENSE.txt).
