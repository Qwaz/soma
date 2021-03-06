#!/usr/bin/python

import argparse
import os
import pwd
import re

import db
import prompt

MODE_INIT = 'init'
MODE_ADD = 'add'
MODE_LIST = 'list'
MODE_RESTART = 'restart'
MODE_RESTART_ALL = 'restart-all'
MODE_DOWNLOAD = 'download'


def check_root():
    if os.getuid() == 0:
        pass
    else:
        prompt.fail('You must be root to execute this command')
        exit(1)


def open_daemon(prob_user, prob_port, prob_entry, prob_home):
    pid = 0
    try:
        pid = os.fork()
    except OSError as e:
        exit(1)
    if pid == 0:
        os.chdir(prob_home)
        user = pwd.getpwnam(prob_user)
        os.setregid(user.pw_gid, user.pw_gid)
        os.setreuid(user.pw_uid, user.pw_uid)
        os.execv('/usr/bin/socat', ['socat', 'tcp-listen:%d,fork,reuseaddr,bind=127.0.0.1' % prob_port, 'exec:%s,PTY,CTTY,raw,echo=0' % prob_entry])
    return pid


def copy_files_with_permission(files, dir, uid, gid, permission):
    files = files.strip()
    r = 0
    for file in files.split():
        r |= os.system('cp %s %s' % (file, dir))
        abs_file = os.path.join(dir, os.path.basename(file))
        r |= os.system('chown %s:%s %s' % (uid, gid, abs_file))
        r |= os.system('chmod %s %s' % (permission, abs_file))
    return r


def show_local():
    prompt.show('[ Local Problems ]')
    prompt.info('%-20s%-24s%-15s%-15s' % ('Name', 'Source', 'ID', 'Password'))
    for prob in db.local_list():
        prompt.show('%-20s%-24s%-15s%-15s' % (prob[0], prob[1], prob[2], prob[3] if prob[4] else '**HIDDEN**'))
    prompt.show('')


def show_remote():
    prompt.show('[ Remote Problems ]')
    prompt.info('%-20s%-24s%-7s' % ('Name', 'Source', 'Port'))
    for prob in db.remote_list():
        prompt.show('%-20s%-24s%-7s' % (prob[0], prob[1], prob[2]))
    prompt.show('')


parser = argparse.ArgumentParser(prog='soma', description='PWN problem manager')
parser.add_argument('--version', '-V', action='version', version='0.3.0')
subparsers = parser.add_subparsers(help='possible command list', dest='mode')
subparsers.required = True

# initialize
parser_config = subparsers.add_parser(MODE_INIT, description='initialize soma')
parser_config.set_defaults(mode=MODE_INIT)

# add a problem
parser_add = subparsers.add_parser(MODE_ADD, description='add a problem')
parser_add.set_defaults(mode=MODE_ADD)

# list problems
parser_list = subparsers.add_parser(MODE_LIST, description='list problems')
parser_list.set_defaults(mode=MODE_LIST)

# restart remote problem
parser_restart = subparsers.add_parser(MODE_RESTART, description='restart a remote problem')
parser_restart.set_defaults(mode=MODE_RESTART)

parser_restart_all = subparsers.add_parser(MODE_RESTART_ALL, description='restart all remote problems')
parser_restart_all.set_defaults(mode=MODE_RESTART_ALL)

# download remote problem binary
parser_download = subparsers.add_parser(MODE_DOWNLOAD, description='download remote problem binary')
parser_download.set_defaults(mode=MODE_DOWNLOAD)

args = parser.parse_args()


# check db is existing
if args.mode != MODE_INIT:
    if db.get_config('initialized') is None:
        prompt.fail('Please initialize database first (soma init)')
        exit(1)


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
    # TODO: prevent injection
    # TODO: revert changes on fail
    check_root()

    # common config
    prob_source = prompt.string('Problem source: ', pattern=prompt.Validators.no_space)
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
    Problem Source: %s
    Problem Name: %s
    Problem Type: %s
    Username: %s
    Password: %s (%s)
    Username for setuid: %s
''' % (prob_source, prob_name, prob_type, prob_user, prob_password, 'public' if prob_show_password else 'private', prob_user_pwn)):
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
                soma_user = db.get_config('soma_user')
                r |= os.system('mkdir %s' % prob_home)
                r |= os.system('chown %s:%s %s' % (soma_user, prob_user, prob_home))
                r |= os.system('chmod 755 %s' % prob_home)
                if r:
                    raise Exception('Failed to create the home directory')

                prompt.info('Copying problem files')
                binaries = prompt.anything('Problem binaries (%s:%s 2555)\n' % (soma_user, prob_user_pwn))
                if copy_files_with_permission(binaries, prob_home, soma_user, prob_user_pwn, '2555'):
                    raise Exception('Failed to copy binaries')

                other_files = prompt.anything('Other readable files such as README (%s:%s 644)\n' % (soma_user, prob_user_pwn))
                if copy_files_with_permission(other_files, prob_home, soma_user, soma_user, '644'):
                    raise Exception('Failed to copy other files')

                prompt.info('Creating flag file')
                flag_content = prompt.string('Flag: ')
                flag_abspath = os.path.join(prob_home, 'flag')
                r |= os.system('printf "%s\n" > %s' % (flag_content, flag_abspath))
                r |= os.system('chown %s:%s %s' % (soma_user, prob_user_pwn, flag_abspath))
                r |= os.system('chmod 440 %s' % flag_abspath)
                if r:
                    raise Exception('Failed to create flag file')

                prompt.info('Add problem information to DB')
                db.add_local(prob_source, prob_name, prob_user, prob_password, prob_show_password, prob_user_pwn)
            except Exception as err:
                prompt.fail(str(err))
                exit(1)
        else:
            prompt.warning('Problem creation canceled')
    else:
        prob_home = os.path.join(db.get_config('soma_path'), prob_user)

        try:
            prompt.info('Creating new user')
            r = 0
            r |= os.system('adduser --quiet %s --home %s --disabled-password --shell /bin/bash --gecos "" --no-create-home' % (prob_user, prob_home))
            if r:
                raise Exception('Failed to create user')

            prompt.info('Creating the home directory')
            soma_user = db.get_config('soma_user')
            r |= os.system('mkdir %s' % prob_home)
            r |= os.system('chown %s:%s %s' % (soma_user, prob_user, prob_home))
            r |= os.system('chmod 755 %s' % prob_home)
            if r:
                raise Exception('Failed to create the home directory')

            prompt.info('Copying problem files')
            binaries = prompt.anything('Problem binaries (%s:%s 554)\n' % (soma_user, prob_user))
            if copy_files_with_permission(binaries, prob_home, soma_user, prob_user, '554'):
                raise Exception('Failed to copy binaries')

            other_files = prompt.anything('Other readable files such as README (%s:%s 644)\n' % (soma_user, soma_user))
            if copy_files_with_permission(other_files, prob_home, soma_user, soma_user, '644'):
                raise Exception('Failed to copy other files')

            prompt.info('Creating flag file')
            flag_content = prompt.string('Flag: ')
            flag_abspath = os.path.join(prob_home, 'flag')
            r |= os.system('printf "%s\n" > %s' % (flag_content, flag_abspath))
            r |= os.system('chown %s:%s %s' % (soma_user, prob_user, flag_abspath))
            r |= os.system('chmod 440 %s' % flag_abspath)
            if r:
                raise Exception('Failed to create flag file')

            prob_entry = prompt.string('Please provide entry file command: ')
            prob_port = 0
            prob_pid = 0
            while True:
                prob_port = prompt.num('Port Number: ', 0, 32767)
                if not db.empty_port(prob_port):
                    prompt.warning('Another problem uses that port')
                    continue
                try:
                    prob_pid = open_daemon(prob_user, prob_port, prob_entry, prob_home)
                    break
                except Exception:
                    prompt.fail('Cannot execute command. Try again.')

            prompt.info('Add problem information to DB')
            db.add_remote(prob_source, prob_name, prob_user, prob_entry, prob_port, prob_pid)
        except Exception as err:
            prompt.fail(str(err))
            exit(1)
        pass
elif args.mode == MODE_LIST:
    show_local()
    show_remote()
elif args.mode == MODE_RESTART:
    check_root()
    show_remote()

    prob_name = ''
    prob = None
    while not prob:
        prob_name = prompt.string('Problem Name: ')
        prob = db.get_remote_problem(prob_name)

    prob_user, prob_entry, prob_port, prob_pid = prob
    prob_home = os.path.join(db.get_config('soma_path'), prob_user)

    prompt.info('Kill existing process')
    os.system('kill -9 %d > /dev/null 2>&1' % prob_pid)

    prompt.info('Restarting process')
    prob_pid = open_daemon(prob_user, prob_port, prob_entry, prob_home)
    db.modify_remote(prob_name, prob_port, prob_pid)
elif args.mode == MODE_RESTART_ALL:
    check_root()

    for prob in db.remote_list():
        prob_name, prob_source, prob_port, prob_pid = prob
        prob_user, prob_entry, prob_port, prob_pid = db.get_remote_problem(prob_name)
        prob_home = os.path.join(db.get_config('soma_path'), prob_user)

        os.system('kill -9 %d > /dev/null 2>&1' % prob_pid)

        prompt.info('Restarting process %s' % prob_name)
        prob_pid = open_daemon(prob_user, prob_port, prob_entry, prob_home)
        db.modify_remote(prob_name, prob_port, prob_pid)
elif args.mode == MODE_DOWNLOAD:
    show_remote()

    prob_name = ''
    prob = None
    while not prob:
        prob_name = prompt.string('Problem Name: ')
        prob = db.get_remote_problem(prob_name)

    prob_user, prob_entry, prob_port, prob_pid = prob
    prob_home = os.path.join(db.get_config('soma_path'), prob_user)
    r = os.system('cp %s ./' % os.path.join(prob_home, prob_entry))

    if r == 0:
        prompt.success('Successfully copied the binary file')
    else:
        prompt.fail('Failed to copy the binary file')
