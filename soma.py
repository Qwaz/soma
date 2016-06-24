#!/usr/bin/python

import argparse
import getpass
import os
import pwd
import re

import db
import prompt

MODE_INIT = 'init'
MODE_ADD = 'add'

parser = argparse.ArgumentParser(prog='soma', description='PWN problem manager')
parser.add_argument('--version', '-V', action='version', version='0.1.0')
subparsers = parser.add_subparsers(help='possible command list', dest='mode')
subparsers.required = True

# initialize
parser_config = subparsers.add_parser(MODE_INIT, description='initialize soma')
parser_config.set_defaults(mode=MODE_INIT)

# add a problem
parser_add = subparsers.add_parser(MODE_ADD, description='add a problem')
parser_add.set_defaults(mode=MODE_ADD)

args = parser.parse_args()

if args.mode == MODE_INIT:
    if db.get_config('initialized') is not None:
        prompt.fail('Database is already initialized!')
        exit(1)
    else:
        try:
            current_user = pwd.getpwuid(os.getuid()).pw_name
            soma_user = prompt.string('Please provide soma master username (blank to use `%s`): ' % current_user, default=current_user, pattern=prompt.Validators.username)
            soma_path = prompt.directory('Directory to create problems (blank to use `/home`): ', default='/home')
            db.create_db(soma_user, soma_path)
            prompt.success('Database is successfully initialized')
        except Exception as err:
            prompt.fail('Failed to create database')
            prompt.show(err)
            exit(1)

elif args.mode == MODE_ADD:
    prompt.warning('Make sure you have root privilege')

    # common config
    prob_name = prompt.string('Problem name: ', pattern=prompt.Validators.no_space)
    prob_type = prompt.choice('Problem type (local / remote): ', ('local', 'remote'))

    if re.match(prompt.Validators.username, prob_name):
        prob_user = prompt.string('Username (blank to use `%s`): ' % prob_name, default=prob_name, pattern=prompt.Validators.username)
    else:
        prob_user = prompt.string('Username: ', pattern=prompt.Validators.username)

    if prob_type == 'local':
        # local problem config
        prob_password = prompt.string('Password: ')
        prob_show_password = prompt.yn('Is the password public? ')
        prob_user_pwn = prompt.string('Username for setuid (blank to use `%s`): ' % (prob_user + '_pwn'), default=prob_user + '_pwn', pattern=prompt.Validators.username)
        if prompt.yn('''
Is this correct?
    Problem Name: %s
    Problem Type: %s
    Username: %s
    Password: %s (%s)
    Username for setuid: %s
''' % (prob_name, prob_type, prob_user, prob_password, 'public' if prob_show_password else 'private', prob_user_pwn)):
            prob_home = os.path.join(db.get_config('soma_path'), prob_user)

            try:
                prompt.info('Creating new user')
                r = 0
                r |= os.system('adduser --quiet %s --home %s --disabled-password --shell /bin/bash --gecos "" --no-create-home' % (prob_user_pwn, prob_home))
                r |= os.system('adduser --quiet %s --home %s --disabled-password --shell /bin/bash --gecos "" --no-create-home' % (prob_user, prob_home))
                r |= os.system('echo "%s:%s" | chpasswd' % (prob_user, prob_password))
                r |= os.system('usermod %s -a -G %s' % (prob_user_pwn, prob_user))
                if r:
                    raise Exception('Failed to create user')

                prompt.info('Creating the home directory')
                soma_user  = db.get_config('soma_user')
                r |= os.system('mkdir %s' % prob_home)
                r |= os.system('chown %s:%s %s' % (soma_user, prob_user, prob_home))
                r |= os.system('chmod 750 %s' % prob_home)
                if r:
                    raise Exception('Failed to create the home directory')

                def copy_files_with_permission(files, dir, uid, gid, permission):
                    files = files.strip()
                    r = 0
                    for file in files.split():
                        r |= os.system('cp %s %s' % (file, dir))
                        abs_file = os.path.join(dir, os.path.basename(file))
                        r |= os.system('chown %s:%s %s' % (uid, gid, abs_file))
                        r |= os.system('chmod %s %s' % (permission, abs_file))
                    return r

                # TODO: prevent injection
                prompt.info('Copying problem files')
                binaries = prompt.anything('Problem binaries (%s:%s 4550)\n' % (prob_user_pwn, prob_user))
                if copy_files_with_permission(binaries, prob_home, prob_user_pwn, prob_user, '4550'):
                    raise Exception('Failed to copy binaries')

                other_files = prompt.anything('Other readable files such as README (%s:%s 644)\n' % (soma_user, soma_user))
                if copy_files_with_permission(other_files, prob_home, soma_user, soma_user, '644'):
                    raise Exception('Failed to copy other files')

                prompt.info('Creating flag file')
                flag_name = prompt.string('Flag file name (blank to use `flag`): ', default='flag')
                flag_content = prompt.string('Flag: ')
                flag_abspath = os.path.join(prob_home, flag_name)
                r |= os.system('printf "%s\n" > %s' % (flag_content, flag_abspath))
                r |= os.system('chown %s:%s %s' % (soma_user, prob_user_pwn, flag_abspath))
                r |= os.system('chmod 440 %s' % flag_abspath)
                if r:
                    raise Exception('Failed to create flag file')

                prompt.info('Add problem information to DB')
                db.add_local(prob_name, prob_user, prob_password, prob_show_password, prob_user_pwn)
            except Exception as err:
                prompt.fail(str(err))
                exit(1)
        else:
            prompt.warning('Problem creation canceled')
    else:
        # TODO: remote problem config
        pass
