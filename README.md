### RDS REPL
This is a REPL for the RDS data API. 

### Install
Python3 is needed. We currently only support running it as a Python script.

```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
```

### Usage
```
$ python3 rdsline.py --help
usage: rdsline.py [-h] [--config CONFIG]

optional arguments:
  -h, --help       show this help message and exit
  --config CONFIG  Config file to read settings from
```

### Config file format
You can see a template of the config file format in config.yaml. 

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

### Inside the REPL
You can type `.help` to show what commands are available inside the REPL.
```
python3 rdsline.py
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


### TODO
* Wishlist: an actual CLI with setuptools. 
* Wishlist: `brew install rdsline`
* Testing
* Static analysis
* Other databases?