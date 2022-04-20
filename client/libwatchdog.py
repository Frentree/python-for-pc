import logging
import os
import os.path
import sys
import time
from argparse import ArgumentParser
from textwrap import dedent
from watchdog.utils import WatchdogShutdown, load_class
from watchdog.version import VERSION_STRING

logging.basicConfig(level=logging.INFO)

CONFIG_KEY_TRICKS = 'tricks'
CONFIG_KEY_PYTHON_PATH = 'python-path'

cli = ArgumentParser()
subparsers = cli.add_subparsers(dest='command')

def argument(*name_or_flags, **kwargs):
    """Convenience function to properly format arguments to pass to the
      command decorator.
    """
    return list(name_or_flags), kwargs

def command(args=[], parent=subparsers, cmd_aliases=[]):
    """Decorator to define a new command in a sanity-preserving way.
      The function will be stored in the ``func`` variable when the parser
      parses arguments so that it can be called directly like so::

        >>> args = cli.parse_args()
        >>> args.func(args)

    """
    def decorator(func):
        name = func.__name__.replace('_', '-')
        desc = dedent(func.__doc__)
        parser = parent.add_parser(name,
                                   description=desc,
                                   aliases=cmd_aliases)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
            parser.set_defaults(func=func)
        return func
    return decorator

def path_split(pathname_spec, separator=os.pathsep):
    """
    Splits a pathname specification separated by an OS-dependent separator.

    :param pathname_spec:
        The pathname specification.
    :param separator:
        (OS Dependent) `:` on Unix and `;` on Windows or user-specified.
    """
    return list(pathname_spec.split(separator))

def add_to_sys_path(pathnames, index=0):
    """
    Adds specified paths at specified index into the sys.path list.

    :param paths:
        A list of paths to add to the sys.path
    :param index:
        (Default 0) The index in the sys.path list where the paths will be
        added.
    """
    for pathname in pathnames[::-1]:
        sys.path.insert(index, pathname)

def parse_patterns(patterns_spec, ignore_patterns_spec, separator=';'):
    """
    Parses pattern argument specs and returns a two-tuple of
    (patterns, ignore_patterns).
    """
    patterns = patterns_spec.split(separator)
    ignore_patterns = ignore_patterns_spec.split(separator)
    if ignore_patterns == ['']:
        ignore_patterns = []
    return (patterns, ignore_patterns)


def observe_with(observer, event_handler, pathnames, recursive):
    """
    Single observer thread with a scheduled path and event handler.

    :param observer:
        The observer thread.
    :param event_handler:
        Event handler which will be called in response to file system events.
    :param pathnames:
        A list of pathnames to monitor.
    :param recursive:
        ``True`` if recursive; ``False`` otherwise.
    """
    for pathname in set(pathnames):
        observer.schedule(event_handler, pathname, recursive)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except WatchdogShutdown:
        observer.stop()
    observer.join()

def schedule_tricks(observer, tricks, pathname, recursive):
    """
    Schedules tricks with the specified observer and for the given watch
    path.

    :param observer:
        The observer thread into which to schedule the trick and watch.
    :param tricks:
        A list of tricks.
    :param pathname:
        A path name which should be watched.
    :param recursive:
        ``True`` if recursive; ``False`` otherwise.
    """
    for trick in tricks:
        for name, value in list(trick.items()):
            TrickClass = load_class(name)
            handler = TrickClass(**value)
            trick_pathname = getattr(handler, 'source_directory', None) or pathname
            observer.schedule(handler, trick_pathname, recursive)

def main():
    """Entry-point function."""
    args = cli.parse_args()
    if args.command is None:
        cli.print_help()
    else:
        args.func(args)

if __name__ == '__main__':
    print("MAIN")
    myargs = None
    myargs = [
        'log',
        '--patterns=*.txt',
        '--ignore-patterns=*.tmp;*.log;*Program files*',
        '--recursive',
        '--ignore-directories',
        '/'
    ]
    args = cli.parse_args(myargs)
    if args.command is None:
        cli.print_help()
    else:
        args.func(args)