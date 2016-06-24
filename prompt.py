from __future__ import print_function

import os
import re


class ColorEscape:
    HEADER = '\033[95m' # Magenta
    OK_BLUE = '\033[94m' # Blue
    OK_GREEN = '\033[92m' # Green
    WARNING = '\033[93m' # Yellow
    FAIL = '\033[91m' # Red
    INFO = '\033[96m' # Cyan
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Validators:
    username = '[a-z_][a-z0-9_]{0,30}'
    no_space = '[a-zA-Z0-9_-]+'

try:
    input = raw_input
except NameError:
    pass


def show(msg):
    print(msg)


def success(msg):
    print(ColorEscape.OK_GREEN + msg + ColorEscape.ENDC)


def fail(msg):
    print(ColorEscape.FAIL + msg + ColorEscape.ENDC)


def warning(msg):
    print(ColorEscape.WARNING + msg + ColorEscape.ENDC)


def info(msg):
    print(ColorEscape.INFO + msg + ColorEscape.ENDC)


def yn(question):
    while True:
        response = input(question).lower()
        if response == 'y' or response == 'yes':
            return True
        elif response == 'n' or response == 'no':
            return False


def choice(msg, choices):
    while True:
        response = input(msg)
        if response in choices:
            return response


def anything(msg):
    return input(msg)


def string(msg, default='', pattern=''):
    while True:
        response = input(msg)
        if response == '':
            if default != '':
                if re.match(pattern, default):
                    return default
        else:
            if pattern == '':
                return response
            else:
                if re.match(pattern, response):
                    return response


def directory(msg, default=''):
    while True:
        path = string(msg, default)
        if os.path.isdir(path):
            return os.path.abspath(path)
