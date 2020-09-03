""" Module to hold various validation functions """

from __future__ import absolute_import, print_function
import logging
import re
import socket
import os
import pwd
import sys
try:
    from cStringIO import StringIO
    import ConfigParser
except ImportError:
    from io import StringIO
    import configparser as ConfigParser


__all__ = ['valid_domain',
           'valid_email',
           'valid_location',
           'valid_file',
           'valid_directory',
           'valid_user',
           'valid_user_vo_file',
           'valid_vo_name',
           'valid_boolean',
           'valid_executable',
           'valid_ini_file',
           'valid_integer',
           'valid_ipv4_address',
           'valid_ipv6_address',
           ]

log = logging.getLogger(__name__)


def valid_ipv4_address(addr):
    """Return True if the address is a valid IPv4 address, False otherwise.

    """
    try:
        return bool(socket.inet_pton(socket.AF_INET, addr))
    except socket.error:
        return False


def valid_ipv6_address(addr):
    """Return True if the address is a valid IPv6 address, False otherwise.

    """
    try:
        return bool(socket.inet_pton(socket.AF_INET6, addr))
    except socket.error:
        return False


def valid_domain(host, resolve=False):
    """Return True if the string passed in is a valid domain or IP address.

    If resolve=True, also check that it resolves (according to gethostbyname).

    """
    if not host:
        return False
    host = str(host)
    if valid_ipv4_address(host):
        log.debug("%s is a v4 address", host)
        return True
    if valid_ipv6_address(host):
        log.debug("%s is a v6 address", host)
        return True
    if not valid_hostname(host):
        log.debug("%s is not a valid hostname", host)
        return False
    if not resolve:
        return True
    try:
        ip = socket.gethostbyname(host)
        log.debug("%s resolves to %s", host, ip)
    except (socket.herror, socket.gaierror):
        log.debug("%s does not resolve", host)
        return False
    return True


def valid_hostname(hostname):
    """Return if a hostname is valid according to the standard"""
    # from https://stackoverflow.com/a/2532344
    if len(hostname) > 255:
        return False
    try:
        # technically, '80' is a valid hostname (and apparently it resolves
        # too!) but it's usually a mistake so reject it
        int(hostname)
        return False
    except ValueError:
        pass
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def valid_email(address):
    """Check an email address and make sure that it fits the correct format"""
    if not address:
        return False
    match = re.match(r'(?:[a-zA-Z\-_+0-9.]+)@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)+)',
                     address)
    if not match:
        return False
    return True


def valid_location(location):
    """Returns True if location points to an existing directory or file"""
    if location and os.path.exists(location):
        return os.path.isdir(location) or os.path.isfile(location)

    return False


def valid_file(location):
    """Returns True if location points to an existing file"""
    if location and os.path.exists(location):
        return os.path.isfile(location)

    return False


def valid_directory(location):
    """Returns True if location points to an existing file"""
    if location and os.path.exists(location):
        return os.path.isdir(location)

    return False


def valid_user(username):
    """
    Returns True if the username given is a valid username on the system
    """
    try:
        if username and pwd.getpwnam(username):
            return True
    except KeyError:
        # getpwnam returns a key error if entry isn't present
        return False

    return False


def valid_user_vo_file(map_file=None, return_invalid_lines=False):
    """
    Check an osg-user-vo-file and make sure that it's valid.
    """
    if map_file is None or map_file == "":
        if return_invalid_lines:
            return (False, [])
        else:
            return False

    if not valid_file(map_file):
        if return_invalid_lines:
            return (False, [])
        else:
            return False

    if os.path.getsize(map_file) == 0:
        if return_invalid_lines:
            return (False, [])
        else:
            return False

    valid = True
    comment = re.compile(r'^\s*#')
    java = re.compile(r'(java|exception)', re.I)
    account_regex = re.compile(r'^[a-z0-9-._]+$', re.IGNORECASE)
    invalid_lines = []
    for line in [x.strip() for x in open(map_file)]:
        if line == "":
            # skip blank lines
            continue

        if java.search(line):
            # found java exception
            invalid_lines.append(line)
            valid = False
            continue

        if not comment.match(line):
            if len(line.strip().split()) != 2:
                invalid_lines.append(line)
                valid = False
                continue

            (account, vo) = line.strip().split()
            if not (account_regex.match(account) and valid_vo_name(vo)):
                # not a comment or entry
                invalid_lines.append(line)
                valid = False
                continue

    if return_invalid_lines:
        return (valid, invalid_lines)
    else:
        return valid


def valid_vo_name(vo_name):
    """
    Check to see if a vo_name is "valid"

    returns True / False
    """

    if vo_name is None:
        return False

    if valid_domain(vo_name):
        return True

    name_re = re.compile(r'[a-z0-9-]+', re.IGNORECASE)
    if name_re.match(vo_name):
        return True

    return False


def valid_boolean(config, section, option):
    """
    Check an option to make sure that it's a valid boolean option
    """
    try:
        if not config.has_option(section, option):
            return False
        config.getboolean(section, option)
        return True
    except ValueError:
        return False


def valid_executable(file_name):
    """
    Check to make sure that a file is present and a valid executable
    """
    try:
        if (not valid_file(file_name) or
                not os.access(file_name, os.X_OK)):
            return False
    except IOError:
        return False
    return True


def valid_ini_file(filename):
    """
    Check an ini file to make sure that it's conforms to our requirements
    E.g. no repeated sections, no newlines in options

    returns True/False
    """
    if filename == "" or filename is None:
        return False

    config_file = os.path.abspath(filename)
    configuration = ConfigParser.ConfigParser()
    file_buffer = StringIO()
    temp = open(config_file).read()
    temp = temp.replace('%(', '-')
    file_buffer.write(temp)
    file_buffer.seek(0)
    try:
        configuration.readfp(file_buffer)
    except ConfigParser.ParsingError as e:
        print("Error while parsing: %s\n%s" % (filename, e), file=sys.stderr)
        print("Lines with options should not start with a space", file=sys.stderr)
        return False

    sections = configuration.sections()
    for section in sections:
        for option in configuration.options(section):
            try:
                value = configuration.get(section, option)
                if "\n" in value:
                    # pylint: disable-msg=E1103
                    error_line = value.split('\n')[1]
                    print("INI syntax error in section %s: " % section, file=sys.stderr)
                    print("The following line starts with a space: %s" % error_line, file=sys.stderr)
                    print("Please removing the leading space", file=sys.stderr)
                    return False
            except ValueError:
                print("syntax error in section %s with option %s" % (section, option), file=sys.stderr)
                return False

    return True


# Quick function to check if configuration value is an integer
def valid_integer(to_check):
    """
    Check if the value in to_check is actually an integer.  to_check can be a 
    string or already an integer.
    returns True or False
    """
    try: 
        int(to_check)
        return True
    except ValueError:
        return False
