# rdsline
This is a REPL for the RDS data API. 

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

## Usage
`rdsline` reads configuration from a file. The default configuration file is `~/.rdsline`. You can also pass in a config file using the `--config` command line argument. 

You can use [config.yaml](https://github.com/hpolloni/rdsline/blob/master/config.yaml) as a template.

### Inside the REPL
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

### Pipe redirection
`rdsline` will automatically detect when its input is a pipe. In this mode, headers are ommitted and the output is changed to `TSV`. 

For example:

A costly way to ouput `hello`:
```bash
$ echo "select 'hello';" | rdsline
hello
```

Or most complex queries:
```bash
$ echo "select * from users;" | rdsline
1 hpolloni
2 alice
3 bob
```

* [Contributing](https://github.com/hpolloni/rdsline/blob/master/CONTRIBUTING.md)
* [MIT License](https://github.com/hpolloni/rdsline/blob/master/LICENSE.txt)

