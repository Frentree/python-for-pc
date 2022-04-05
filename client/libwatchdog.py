import logging
import os
import os.path
import sys
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from textwrap import dedent
from watchdog.utils import WatchdogShutdown, load_class
from watchdog.version import VERSION_STRING

logging.basicConfig(level=logging.INFO)

CONFIG_KEY_TRICKS = 'tricks'
CONFIG_KEY_PYTHON_PATH = 'python-path'

from watchdog.tricks import LoggerTrick
from libsqlite3 import *

class MyLoggerTrick(LoggerTrick):

    def do_log(self, event):
        print("DO_LOG")
        MINIMUM_FILESIZE = 5

        if event.is_directory:
            return
        try:
            filesize = os.path.getsize(event.src_path)
        except FileNotFoundError as e:
            # print('[DEBUG] ' + e)
            return
        except PermissionError as e:
            return

        if filesize < MINIMUM_FILESIZE:
            return

        included_patterns = [
            "*.txt",
        ]
        excluded_patterns = [
            "/Program files*",
        ]
        included_patterns = {pattern.lower() for pattern in included_patterns}
        excluded_patterns = {pattern.lower() for pattern in excluded_patterns}
        from pathlib import PureWindowsPath, PurePosixPath
        path = event.src_path
        path = PureWindowsPath(path)
        match_exclude_result = any(path.match(p) for p in excluded_patterns)
        if match_exclude_result:
            print("######################## Exclude match : true " + event.src_path)
            return

        if any(path.match(p) for p in excluded_patterns) or \
            not any(path.match(p) for p in included_patterns):
            return

        from datetime import datetime
        #print(datetime.now().strftime("%Y%m%d_%H%M%S"))

        workdir_path = "."
        params = {
            "project_name": "prj1",
        }
        sqlite3 = csqlite3(workdir_path + '/' + params["project_name"] + ".db")
        sqlite3.fileinfo_insert(event.src_path, filesize)

        #import sys, traceback
        #traceback.print_stack()
        #traceback.print_exc(file=sys.stdout)

    def on_modified(self, event):
        self.do_log(event)

    def on_moved(self, event):
        self.do_log(event)

epilog = """Copyright 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>.
Copyright 2012 Google, Inc & contributors.

Licensed under the terms of the Apache license, version 2.0. Please see
LICENSE in the source code for more information."""

cli = ArgumentParser(epilog=epilog)#, formatter_class=HelpFormatter)
cli.add_argument('--version', action='version', version=VERSION_STRING)
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


def load_config(tricks_file_pathname):
    """
    Loads the YAML configuration from the specified file.

    :param tricks_file_path:
        The path to the tricks configuration file.
    :returns:
        A dictionary of configuration information.
    """
    import yaml

    with open(tricks_file_pathname, 'rb') as f:
        return yaml.safe_load(f.read())

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

@command([argument('directories',
                   nargs='*',
                   default='.',
                   help='Directories to watch. (default: \'.\').'),
          argument('-p',
                   '--pattern',
                   '--patterns',
                   dest='patterns',
                   default='*',
                   help='Matches event paths with these patterns (separated by ;).'),
          argument('-i',
                   '--ignore-pattern',
                   '--ignore-patterns',
                   dest='ignore_patterns',
                   default='',
                   help='Ignores event paths with these patterns (separated by ;).'),
          argument('-D',
                   '--ignore-directories',
                   dest='ignore_directories',
                   default=False,
                   action='store_true',
                   help='Ignores events for directories.'),
          argument('-R',
                   '--recursive',
                   dest='recursive',
                   default=False,
                   action='store_true',
                   help='Monitors the directories recursively.'),
          argument('--interval',
                   '--timeout',
                   dest='timeout',
                   default=1.0,
                   type=float,
                   help='Use this as the polling interval/blocking timeout.'),
          argument('--trace',
                   default=False,
                   help='Dumps complete dispatching trace.'),
          argument('--debug-force-polling',
                   default=False,
                   help='[debug] Forces polling.'),
          argument('--debug-force-kqueue',
                   default=False,
                   help='[debug] Forces BSD kqueue(2).'),
          argument('--debug-force-winapi',
                   default=False,
                   help='[debug] Forces Windows API.'),
          argument('--debug-force-fsevents',
                   default=False,
                   help='[debug] Forces macOS FSEvents.'),
          argument('--debug-force-inotify',
                   default=False,
                   help='[debug] Forces Linux inotify(7).')])
def log(args):
    """
    Command to log file system events to the console.
    """
    from watchdog.tricks import LoggerTrick

    patterns, ignore_patterns =\
        parse_patterns(args.patterns, args.ignore_patterns)
    print(patterns)
    print(ignore_patterns)
    handler = MyLoggerTrick(patterns=patterns,
                          ignore_patterns=ignore_patterns,
                          ignore_directories=args.ignore_directories)

    # Automatically picks the most appropriate observer for the platform
    # on which it is running.
    from watchdog.observers import Observer
    observer = Observer(timeout=args.timeout)
    observe_with(observer, handler, args.directories, args.recursive)

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
        '--ignore-patterns=*.tmp;*.log',
        '--recursive',
        '--ignore-directories',
        '/'
    ]
    args = cli.parse_args(myargs)
    if args.command is None:
        cli.print_help()
    else:
        args.func(args)