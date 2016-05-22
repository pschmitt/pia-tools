#!/usr/bin/env python
# coding: utf-8


from __future__ import print_function
from __future__ import unicode_literals
from requests.packages.urllib3.util import Retry
from systemd import journal
from systemd_dbus.exceptions import SystemdError
from systemd_dbus.manager import Manager
from termcolor import cprint
import StringIO
import argparse
import emoji
import fcntl
import getpass
import hashlib
import logging
import os
import random
import re
import requests
import socket
import string
import struct
import sys
import time
import transmissionrpc
import zipfile


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

try:
    input = raw_input
except NameError:
    input = input

PIA_CONFIG_DIR = '/etc/openvpn/pia'
PIA_PASSWD_FILE = os.path.join(PIA_CONFIG_DIR, 'passwd')
PIA_CLIENTID_FILE = os.path.join(PIA_CONFIG_DIR, 'clientid')
PIA_OPEN_PORT_FILE = os.path.join(PIA_CONFIG_DIR, 'portfwd')
SYSTEMD_MANAGER = None


def negative_message(text):
    cprint(
        emoji.emojize(':negative_squared_cross_mark: ' + text),
        'red', file=sys.stderr
    )


def positive_message(text):
    cprint(
        emoji.emojize(':white_heavy_check_mark: ' + text),
        'green'
    )


def flag_for_exit_point(exit_point):
    if exit_point.startswith('US'):
        return ':flag_for_United_States:'
    elif exit_point.startswith('CA'):
        return ':flag_for_Canada:'
    elif exit_point.startswith('UK'):
        return ':flag_for_United_Kingdom:'
    elif exit_point.startswith('AU'):
        return ':flag_for_Australia:'
    return ':flag_for_{}:'.format(exit_point)

def download_config_files(path):
    url = 'https://www.privateinternetaccess.com/openvpn/openvpn.zip'
    r = requests.get(url, stream=True)
    z = zipfile.ZipFile(StringIO.StringIO(r.content))
    z.extractall(path=path)


def download_file(url, path):
    logger.info('Downloading {} to {}'.format(url, path))
    r = requests.get(url)
    assert r.ok, 'Download failed'
    with open(path, 'w') as common_file:
        common_file.write(r.content)


def download_common_config(path):
    url = 'https://raw.githubusercontent.com/pschmitt/pia-tools/master/pia_common'
    return download_file(url, os.path.join(path, 'pia_common'))


def download_up_down_configs(path):
    url = 'https://raw.githubusercontent.com/pschmitt/pia-tools/master/pia-up'
    r_up = download_file(url, os.path.join(path, 'pia-up'))
    r_down = download_file(url, os.path.join(path, 'pia-down'))
    return r_up, r_down


def __get_ovpn_files(path):
    return [f for f in os.listdir(path) if f.endswith('.ovpn')]


def __remove_spaces_from_config_filenames(path):
    for f in __get_ovpn_files(path):
        filename = os.path.join(path, f)
        new_name = os.path.join(path, f.replace(' ', '_'))
        if filename != new_name:
            logger.debug('Rename {} to {}'.format(filename, new_name))
            os.rename(filename, new_name)


def __append_common_config(path):
    common_file_path = os.path.join(path, 'pia_common')
    up_file_path = os.path.join(path, 'pia-up')
    if not os.path.isfile(common_file_path):
        download_common_config(path)
    if not os.path.isfile(up_file_path):
        download_up_down_configs(path)
    with open(common_file_path, 'r') as common_file:
        common_content = common_file.read()
    for f in __get_ovpn_files(path):
        with open(os.path.join(path, f), 'a+') as config_file:
            if common_content not in config_file.read():
                logger.debug('Append common section to {}'.format(f))
                config_file.write(common_content)


def create_passwd_file(path, username, password):
    global PIA_PASSWD_FILE, PIA_CONFIG_DIR
    if not os.path.exists(PIA_CONFIG_DIR):
        os.makedirs(PIA_CONFIG_DIR)
    with open(PIA_PASSWD_FILE, 'w') as f:
        f.writelines(username + '\n' + password + '\n')
    os.chmod(PIA_PASSWD_FILE, 0600)


def edit_config_files(path):
    __remove_spaces_from_config_filenames(path)
    __append_common_config(path)


def __determine_credentials(args):
    if args.username:
        username = args.username
    else:
        username = input('Username: ')
    password = args.password if args.password else getpass.getpass()
    return username, password


def __read_credentials():
    global PIA_PASSWD_FILE
    with open(PIA_PASSWD_FILE, 'r') as f:
        credentials = f.read().splitlines()
    return credentials[0], credentials[1]


def setup(args):
    username, password = __determine_credentials(args)
    create_passwd_file(PIA_CONFIG_DIR, username, password)
    download_config_files(PIA_CONFIG_DIR)
    edit_config_files(PIA_CONFIG_DIR)


def __get_systemd_manager():
    global SYSTEMD_MANAGER
    if not SYSTEMD_MANAGER:
        SYSTEMD_MANAGER = Manager()
    return SYSTEMD_MANAGER


def get_unit(name):
    manager = __get_systemd_manager()
    for u in manager.list_units():
        if u.properties.Id.startswith(name):
            return u


def __get_pia_unit():
    return get_unit('pia@')


def pia_active():
    return __daemon_active('pia@')
    # pia_unit = __get_pia_unit()
    # if pia_unit:
    #     return pia_unit.properties.ActiveState == 'active'
    # return False


def pia_connect(exit_point, reconnect=False, blocking=False):
    if valid_exit_point(exit_point):
        pia_service = 'pia@{}.service'.format(exit_point)
        if pia_active():
            if exit_point == __get_current_exit_point():
                logger.info(
                    'Alredy connected to exit point {}.'.format(exit_point)
                )
                if reconnect:
                    stop()
            else:
                stop()
        job = __start_daemon(pia_service)
        return pia_wait() if blocking else job
    else:
        available_exit_points = __get_available_exit_points()
        msg = 'No such exit point. Available exit points: {}'.format(
                ', '.join(available_exit_points)
        )
        negative_message(msg)
        logger.error(msg)
        return 1


def __get_current_exit_point():
    u = __get_pia_unit()
    if u:
        m = re.search(
            'pia@(.*).service',
            u.properties.Id
        )
        return m.group(1) if m else None


def status(args):
    if pia_active():
        exit_point = __get_current_exit_point()
        positive_message(
            'PIA is running fine. Exit point: {}{}'.format(
                flag_for_exit_point(exit_point),
                exit_point
            )
        )
        if not internet():
            negative_message('No internet connectivity')
            return 3
        else:
            positive_message('Connectivity is up')
    else:
        negative_message('VPN connection is down')
        return 4


def __get_daemon(daemon):
    manager = __get_systemd_manager()
    try:
        return manager.get_unit(daemon)
    except SystemdError:
        pass


def __start_daemon(daemon, blocking=False):
    if not daemon.endswith('.service'):
        daemon += '.service'
    if __daemon_active(daemon):
        logger.info('Daemon {} is already up'.format(daemon))
        return
    logger.info('Starting {}'.format(daemon))
    manager = __get_systemd_manager()
    try:
        manager.start_unit(daemon, 'fail')
    except SystemdError as e:
        logger.error(e.message)


def __stop_daemon(daemon):
    if not daemon.endswith('.service'):
        daemon += '.service'
    logger.info('Stopping {}'.format(daemon))
    manager = __get_systemd_manager()
    try:
        manager.stop_unit(daemon, 'fail')
    except SystemdError as e:
        logger.error(e.message)


def __restart_daemon(daemon):
    if not daemon.endswith('.service'):
        daemon += '.service'
    logger.info('Restarting {}'.format(daemon))
    manager = __get_systemd_manager()
    try:
        manager.start_unit(daemon, 'fail')
    except SystemdError as e:
        logger.debug(e.message)


def __daemon_active(daemon):
    u = get_unit(daemon)
    if not u:
        return False
    return u.properties.ActiveState == 'active'


def reconnect(blocking=False):
    exit_point = __get_current_exit_point()
    stop()
    return pia_connect(exit_point, blocking=blocking)


def __get_journal(unit, reverse=False):
    logger.debug('Retrieving journal of {}'.format(unit.properties.Id))
    pid = str(__get_main_pid(str(unit.properties.Id)))
    logger.debug('PID: {}'.format(pid))
    j = journal.Reader()
    j.add_match(_SYSTEMD_UNIT=unit.properties.Id)
    j.add_match(_PID=pid)
    entries = []
    for e in j:
        entries.append(e)
    return entries if not reverse else reversed(entries)


def __get_vpn_device():
    unit = __get_pia_unit()
    j = __get_journal(unit, reverse=True)
    for e in j:
        m = re.search(r'TUN/TAP device (.*) opened', e['MESSAGE'])
        if m:
            return str(m.group(1))


def __wait_for_journal_entry(unit, entry):
    # j = __get_journal(unit, reverse=True)
    pass


def pia_wait():
    unit = __get_pia_unit()
    pid = str(__get_main_pid(str(unit.properties.Id)))
    j = journal.Reader()
    j.add_match(_SYSTEMD_UNIT=unit.properties.Id)
    j.add_match(_PID=pid)
    while True:
        for e in reversed([e for e in j]):
            if e['MESSAGE'] == 'Initialization Sequence Completed':
                logger.info('Connection established')
                return
    # return __wait_for_journal_entry('pia@*', 'Initialization Sequence Completed')


def __get_main_pid(service):
    manager = __get_systemd_manager()
    return manager.get_service(service).properties.MainPID


def internet(url='https://httpbin.org/status/200', retries=2, timeout=2):
    s = requests.Session()
    s.mount(
        'https://', requests.adapters.HTTPAdapter(
            max_retries=Retry(total=retries)
        )
    )
    try:
        r = s.get(url, timeout=timeout)
    except:
        return False
    return r.status_code == 200


def update_daemons(daemons):
    active = pia_active()
    logger.info(
        'Ensuring daemons are up...' if active else \
        'PIA not running. Stopping daemons...'
    )
    map(__start_daemon if active else __stop_daemon, daemons)


def check(args):
    active = pia_active()
    exit_point = __get_current_exit_point()
    assert valid_exit_point(args.exit_point), \
        'Invalid exit point. Available exit points: {}'.format(
            ', '.join(
                __get_available_exit_points()
            )
        )
    if not active or exit_point != args.exit_point:
        pia_connect(args.exit_point, blocking=True)
        update_daemons(args.DAEMON)
    if not internet():
        logger.info('Internet connectivity lost. Attempting to reconnect')
        reconnect(blocking=True)
        update_daemons(args.DAEMON)
    if args.port_fwd:
        request_port_fwd(False, args.update_transmission_port)
    return active


def watch(args):
    interval = args.interval if args.interval else 60
    while True:
        check(args)
        logger.info('Done. Sleep {}'.format(interval))
        time.sleep(interval)


def __get_interface_ip(interface):
    '''
    Source: http://code.activestate.com/recipes/439094-get-the-ip-address-associated-with-a-network-inter/

    Alternative implementation using netifaces:
    return netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', interface[:15])
    )[20:24])


def __read_client_id():
    if os.path.isfile(PIA_CLIENTID_FILE):
        with open(PIA_CLIENTID_FILE, 'r') as f:
            # FIXME check file content and if it is not compliant generate
            # a new client ID
            return f.read()


def __get_client_id(force_renewal=False):
    if not force_renewal:
        client_id = __read_client_id()
        if client_id:
            return client_id
    logger.info('Generating a new client ID')
    # No client ID on disk, generate a new one
    rnd_str = ''.join(random.choice(string.printable) for _ in range(100))
    sha = hashlib.sha512()
    sha.update(rnd_str)
    client_id = sha.hexdigest()
    logger.debug('Generated client ID: {}'.format(client_id))
    with open(PIA_CLIENTID_FILE, 'w') as f:
        f.write(client_id)
    return client_id


def __request_port_forwarding(username, password, local_ip, client_id):
    data = {
        'user': username,
        'pass': password,
        'local_ip': local_ip,
        'client_id': client_id
    }
    r = requests.post(
        'https://www.privateinternetaccess.com/vpninfo/port_forward_assignment',
        data=data
    )
    assert r.ok, 'Port forwarding request failed'
    logger.debug('Port forward response: {}'.format(r.json()))
    return r.json()


def port_fwd(args):
    return request_port_fwd(
        new_port=args.new_port, update_transmission=args.update_transmission_port
    )

def request_port_fwd(new_port, update_transmission):
    '''
    https://www.privateinternetaccess.com/forum/discussion/180/port-forwarding-without-the-application-advanced-users
    '''
    assert pia_active(), 'PIA service is NOT running'
    vpn_device = __get_vpn_device()
    assert vpn_device, 'Could not determine VPN device'
    local_ip = __get_interface_ip(vpn_device)
    client_id = __get_client_id(new_port)
    username, password = __read_credentials()
    response = __request_port_forwarding(username, password, local_ip, client_id)
    port = response['port']
    assert port, 'Could not determine port from response'
    logger.debug('Assigned port: {}'.format(port))
    with open(PIA_OPEN_PORT_FILE, 'w') as f:
        f.write(str(port))
    if update_transmission:
        update_transmission_port(port)

def update_transmission_port(peer_port, host='127.0.0.1', port=9091):
    client = transmissionrpc.Client(host, port)
    session = transmissionrpc.session.Session(client)
    session.peer_port = peer_port


def __get_available_exit_points():
    exit_points = []
    files = __get_ovpn_files(PIA_CONFIG_DIR)
    for f in files:
        exit_points.append(f.split('.ovpn')[0])
    return exit_points


def valid_exit_point(exit_point):
    return exit_point in __get_available_exit_points()


def start(args):
    c = pia_connect(args.EXIT_POINT)
    return pia_wait() if args.wait else c


def stop(args=None):
    if pia_active():
        exit_point = __get_current_exit_point()
        logger.info('PIA is running. Exit point: {}'.format(exit_point))
        return __stop_daemon('pia@{}.service'.format(exit_point))
    else:
        print('PIA NOT RUNNING', file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        dest='requested_action',
        help='Available commands'
    )

    setup_parser = subparsers.add_parser(
        'setup',
        help='Download the config files and setup'
    )
    setup_parser.add_argument(
        '-u', '--username'
    )
    setup_parser.add_argument(
        '-p', '--password'
    )
    setup_parser.set_defaults(func=setup)

    status_parser = subparsers.add_parser(
        'status',
        help='Get status information'
    )
    status_parser.set_defaults(func=status)

    start_parser = subparsers.add_parser(
        'start',
        help='Start VPN'
    )
    start_parser.add_argument(
        '-w', '--wait',
        action='store_true',
        required=False,
        help='Wait for connection to be established'
    )
    start_parser.add_argument(
        'EXIT_POINT',
        help='Exit point to connect to'
    )
    start_parser.set_defaults(func=start)

    stop_parser = subparsers.add_parser(
        'stop',
        help='Stop VPN'
    )
    stop_parser.set_defaults(func=stop)

    port_fwd_parser = subparsers.add_parser(
        'port-fwd',
        help='Port forwarding setup'
    )
    port_fwd_parser.add_argument(
        '-n', '--new-port',
        action='store_true',
        help='Request a new port'
    )
    port_fwd_parser.add_argument(
        '-t', '--update-transmission-port',
        action='store_true',
        required=False,
        help='Update transmission\'s peer port'
    )
    port_fwd_parser.set_defaults(func=port_fwd)

    check_parser = subparsers.add_parser(
        'check',
        help='Check the state of the VPN'
    )
    check_parser.add_argument(
        '-e', '--exit-point',
        required=True,
        help='Exit point to connect to (when -r is set)'
    )
    check_parser.add_argument(
        '-p', '--port-fwd',
        action='store_true',
        help='Request port forwarding'
    )
    check_parser.add_argument(
        '-t', '--update-transmission-port',
        action='store_true',
        required=False,
        help='Update transmission\'s peer port'
    )
    check_parser.add_argument(
        'DAEMON',
        nargs='*',
        help='Daemon(s) to stop in case the VPN connection went down'
    )
    check_parser.set_defaults(func=check)

    watch_parser = subparsers.add_parser(
        'watch',
        help='Watch the state of the VPN'
    )
    watch_parser.add_argument(
        '-e', '--exit-point',
        required=True,
        help='Exit point to connect to (when -r is set)'
    )
    watch_parser.add_argument(
        '-p', '--port-fwd',
        action='store_true',
        help='Request port forwarding'
    )
    watch_parser.add_argument(
        '-t', '--update-transmission-port',
        action='store_true',
        required=False,
        help='Update transmission\'s peer port'
    )
    watch_parser.add_argument(
        '-i', '--interval',
        type=int,
        required=False,
        help='Watch interval (in seconds)'
    )
    watch_parser.add_argument(
        'DAEMON',
        nargs='*',
        help='Daemon(s) to stop in case the VPN connection went down'
    )
    watch_parser.set_defaults(func=watch)

    args = parser.parse_args()
    if args.requested_action == None:
        parser.print_usage()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
