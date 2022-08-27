### RDS REPL
This is a REPL for the RDS data API. 

### Install
This is a Python 3 only package. Support for Python 2 is a non goal.

```
$ pip install rdsline

$ rdsline --help
usage: rdsline [-h] [--config CONFIG]

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  Config file to read settings from
```

### Config file format
You can see a template of the config file format in [config.yaml](https://github.com/hpolloni/rdsline/blob/master/config.yaml). 

```yaml
# This is the only database type we support (currently)
type: rds-secretsmanager

# This is usually of the form: arn:aws:rds:<REGION>:<ACCOUNT_ID>:cluster:<CLUSTER_NAME>
cluster_arn: CLUSTER_ARN

# This is usually of the form: arn:aws:secretsmanager:<REGION>:<ACCOUNT_ID>:secret:<SECRET_ID>
secret_arn: SECRET_ARN

# The database name. Hopefully self-explanatory
database: DATABASE_NAME

# AWS credentials (only profile settings for now)
credentials:
  profile: default
```

### Usage
You can type `.help` to show what commands are available inside the REPL.
```
RDS-REPL -- Type .help for help
> .help
.quit - quits the REPL
.config <config_file> - sets new connection settings from a file
.show - displays current connection settings
> select 'hello';
+------------+
| ?column?   |
|------------|
| hello      |
+------------+
```

This is a multi-line REPL. The end of command character is a semicolon `;` or an empty line.
```
> select 'hello'
|
+------------+
| ?column?   |
|------------|
| hello      |
+------------+
```

* [Contributing](https://github.com/hpolloni/rdsline/blob/master/CONTRIBUTING.md)
* [MIT License](https://github.com/hpolloni/rdsline/blob/master/LICENSE.txt)

