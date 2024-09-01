# Harness

Harness that wraps any command line program to parse the
log output of the application. It looks for keywords within
the output, and colors a slice of the output according to
the color associated with a given keyword.

## Operating System Support

This application should work on the *big three*
(i.e., Linux, MacOS, Windows).

> [!NOTE]
> This is a simple script and by no means robust.
> It uses basic ANSI escape sequences to modify
> output. Ensure your terminal supports ANSI
> escape sequences.

## Build Requirements
python >= v3.10.x

## Usage

```sh
usage: harness.py [-h] [-f FILE] [-m MODE] [-s STYLE] [-i] command

Capture and colorize log output

positional arguments:
  command               Command to spawn harnessed application

options:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  Configuration file (defaults to 'harness.conf')
  -m MODE, --mode MODE  Colorization method: 'line' or 'word' (defaults to 'line')
  -s STYLE, --style STYLE
                        Color style: '4bit' or '8bit' (defaults to '8bit')
  -i, --ignore          Ignore case of matched word (no value expected)
```

It is recommended to add call-function to terminal config (i.e., `.bashrc`, `powershell profile`)

Example for `.bashrc`:
```sh
harness() { python3 <PROJECT PATH>/harness.py "$@" ;}
```

>[!NOTE]
> Using `word` mode allows coloring of different words on the same line

>[!NOTE]
> Using the `-i` flag will lowercase the matched words

### Config file

The config file can be named anything, if the
file flag is passed to specify the path/name.

The expected format for the configuration file is:<br/>
    [KEY]=[COLOR]

Comments are supported, so long as the first character is `#` and the
`base` keyword can be used to specify a color that all non-matched
output should default to.

>[!NOTE]
> A sample config file is provided with this repository `harness.conf`
