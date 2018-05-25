#!/usr/bin/python
from __future__ import print_function
from argparse import ArgumentParser
from requests import get
from requests import ConnectionError
from requests import HTTPError
from json import loads as json_loads
from collections import Iterable
from os import getenv as os_getenv
from sys import exit
import socket

MY_FQDN = socket.getaddrinfo(socket.gethostname(), 0, 0, 0, 0, socket.AI_CANONNAME)[0][3]
THRUK_SERVER = None
COLOR = False


def __color(text, colors):
    text = str(text)
    if COLOR is True:
        my_colors = {"BLUE": '\033[94m',
                     "GREEN":  '\033[92m',
                     "WARN": '\033[93m',
                     "CRITICAL": '\033[91m',
                     "ENDC": '\033[0m',
                     "BOLD": '\033[1m',
                     "OK": '\033[92m'}
        if isinstance(colors, Iterable):
            for color in colors:
                if color in my_colors:
                    text = my_colors[color]+text
            text = text+my_colors['ENDC']
            return text
        else:
            if color in my_colors:
                text = my_colors[color]+text
            text = text+my_colors['EDNC']
            return text
    else:
        return text


class Config():
    server = os_getenv('THRUK_SERVER', THRUK_SERVER)
    protocol = os_getenv('THRUK_PROTOCOL', "https")
    valid_protocols = ["http", "https"]
    port = os_getenv("THRUK_PORT", "443")
    version = 0.1
    user = os_getenv("THRUK_USER", "admin")
    password = os_getenv("THRUK_PASSWORD", "admin")
    uri = os_getenv("THRUK_URI", "thruk/cgi-bin/status.cgi?")
    method = "GET"
    details = False
    host = MY_FQDN
    color = True


def __parse_args(default_config):
    args = ArgumentParser()
    help_server = "thruk server address. default: {}".format(default_config.server)
    help_port = "thruk port default: {}".format(default_config.port)
    help_protocol = "protocol. options: {}. default: {}".format(default_config.valid_protocols, default_config.protocol)
    help_hostgroup = "hostgroup summary"
    help_user = "thruk user. deafult: {}".format(default_config.user)
    help_password = "thruk password. default: {}".format(default_config.password)
    help_details = "print details on WARN and CRITICAL errors. default {}".format(default_config.details)
    help_host = "print NAGIO status details for host. default hostname -f value"
    help_color = "disable decorate output with chearfull colors. default {}".format(default_config.color)
    help_server = "hostname or ip of thruk server, defaults to ENV THRUK_SERVER"
    args.add_argument("-s", "--server", default=default_config.server, help=help_server)
    args.add_argument("-p", "--port", default=default_config.port, help=help_port)
    args.add_argument("-P", "--protocol", default=default_config.protocol, help=help_protocol,
                      choices=default_config.valid_protocols)
    args.add_argument("-u", "--user", default=default_config.user, help=help_user)
    args.add_argument("-S", "--password", default=default_config.password, help=help_password)
    args.add_argument("-d", "--details", default=default_config.details, action="store_true", help=help_details)
    args.add_argument("-H", "--host", default=default_config.host, help=help_host)
    args.add_argument("-G", "--hostgroup",  default=None, help=help_hostgroup)
    args.add_argument("-n", "--no-color", default=default_config.color, action="store_false", help=help_color)
    params = args.parse_args()
    if params.hostgroup is None:
        params.action = "get_host"
    else:
        params.action = "get_hostgroup"
    params.method = default_config.method
    params.uri = default_config.uri
    return params


def __base_url(args):
    format_args = (args.protocol, args.server, args.port, args.uri)
    return "{}://{}:{}/{}".format(*format_args)


def __prepare_params(args):
    if args.action == "get_hostgroup":
        return {"style": "detail", "hostgroup": args.hostgroup, "view_mode": "json"}
    else:
        return {"style": "detail", "host": args.host, "view_mode": "json"}


def __fetch_thruk_sumary_page(args):
    url = __base_url(args)
    params = __prepare_params(args)
    auth = (args.user, args.password)
    try:
        request = get(url, params=params, auth=auth)
    except HTTPError:
        print("HTTP request for {}".format(args.server))
        exit(1)
    except ConnectionError:
        print("Connection for {}  server failed. Is Thruk server configured?".format(args.server))
        exit(1)
    return request


def __serialize_thruk_summary(args):
    pass


def __print_details(args, data):
    count = {0: 0, 1: 0, 2: 0}
    for item in data:
        count[item['state']] += 1
        if item['state'] in [1, 2] and args.details is True:
            state_list = {1: "WARN", 2: "CRITICAL"}
            state = state_list[item['state']]
            state = __color(state, [state, "BOLD"])
            host = __color(item['host_name'], ["BLUE", "BOLD"])
            service = __color(item['display_name'], ["BLUE", "BOLD"])
            message = __color(item['plugin_output'], ["GREEN", "BOLD"])
            print("{} host: {}, service: {}, message: {}".format(state, host, service, message))
    OK = __color(count[0], ["OK", "BOLD"])
    WARN = __color(count[1], ["WARN", "BOLD"])
    CRITICAL = __color(count[2], ["CRITICAL", "BOLD"])
    print("CRITICAL: {}, WARN: {}, OK: {}".format(CRITICAL, WARN, OK))


def main(args):
    request = __fetch_thruk_sumary_page(args)
    if request.ok:
        data = json_loads(request.text)
        __print_details(args, data)
    else:
        print("{} returned {} with {} reason".format(request.url, request.status_code, request.reason))

if __name__ == "__main__":
    args = __parse_args(Config)
    COLOR = args.no_color
    main(args)
