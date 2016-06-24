from __future__ import print_function

import re

try:
    input = raw_input
except NameError:
    pass


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def show(msg):
    print(msg)


def success(msg):
    print(bcolors.OKGREEN + msg + bcolors.ENDC)


def fail(msg):
    print(bcolors.FAIL + msg + bcolors.ENDC)


def yn(question):
    while True:
        r = input(question + ' (y/n)').lower()
        if r == 'y' or r == 'yes':
            return True
        elif r == 'n' or r == 'no':
            return False


def string(msg, default='', pattern=''):
    while True:
        r = input(msg)
        if r == '':
            if default != '':
                return default
        else:
            if pattern == '':
                return msg
            else:
                if re.match(pattern, r):
                    return msg
