#!/usr/bin/python

import argparse
import os
import pwd

import db
import prompt

MODE_INIT = 'init'

parser = argparse.ArgumentParser(prog='soma', description='PWN problem manager')
parser.add_argument('--version', '-V', action='version', version='0.1.0')
subparsers = parser.add_subparsers(help='possible command list', dest='mode')
subparsers.required = True

# config mode
parser_config = subparsers.add_parser(MODE_INIT, description='initialize soma')
parser_config.set_defaults(mode=MODE_INIT)

args = parser.parse_args()

if args.mode == MODE_INIT:
    if db.initialized():
        prompt.fail('Database is already initialized!')
        exit(1)
    else:
        try:
            current_user = pwd.getpwuid(os.getuid()).pw_name
            soma_user = prompt.string('Please provide soma master username (blank to use `%s`): ' % current_user, default=current_user, pattern='[a-z_][a-z0-9_]{0,30}')
            db.create_db(soma_user)
            prompt.success('Database is successfully initialized')
        except Exception as err:
            prompt.fail('Failed to create database')
            prompt.show(err)
            exit(1)
