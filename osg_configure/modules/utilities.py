""" Module to hold various utility functions """

import re
import socket
import os
import types
import sys
import glob
import stat
import tempfile
import subprocess
import platform
import ConfigParser
import errno
import logging

import rpm

__all__ = ['get_elements',
           'write_attribute_file',
           'get_set_membership',
           'get_hostname',
           'blank',
           'get_vos',
           'service_enabled',
           'fetch_crl',
           'run_script',
           'get_condor_location',
           'get_condor_config',
           'get_condor_config_val'
           'atomic_write',
           'ce_installed',
           'any_rpms_installed'
           'rpm_installed',
           'get_test_config',
           'make_directory',
           'get_os_version',
           'config_safe_get',
           'config_safe_getboolean',
           'classad_quote',
           'add_or_replace_setting',
           'NullLogger',
           'split_host_port',
]

CONFIG_DIRECTORY = "/etc/osg"


def get_elements(element=None, filename=None):
    """Get values for selected element from xml file specified in filename"""
    if filename is None or element is None:
        return []
    import xml.dom.minidom
    import xml.parsers.expat

    try:
        dom = xml.dom.minidom.parse(filename)
    except IOError:
        return []
    except xml.parsers.expat.ExpatError:
        return []
    values = dom.getElementsByTagName(element)
    return values


def _compose_attribute_file(attributes):
    """Make the contents of an osg attributes file"""

    def islist(var):
        return type(var) is types.ListType

    variable_string = ""
    export_string = ""
    # keep a list of array variables
    array_vars = {}
    keys = attributes.keys()
    keys.sort()
    for key in keys:
        value = attributes[key]
        if value is None:
            variable_string += "# " + key + " is undefined\n"
            continue
        # Special case for SOFTWARE-1567 (let user explicitly unset OSG_APP)
        if key == 'OSG_APP' and (value == 'UNSET' or (islist(value) and 'UNSET' in value)):
            variable_string += 'unset OSG_APP\n'
        elif islist(value):
            for item in value:
                variable_string += "%s=\"%s\"\n" % (key, item)
        else:
            variable_string += "%s=\"%s\"\n" % (key, value)
        if len(key.split('[')) > 1:
            real_key = key.split('[')[0]
            if real_key not in array_vars:
                export_string += "export %s\n" % key.split('[')[0]
                array_vars[real_key] = ""
        else:
            # 'OSG_APP' is a special case for SOFTWARE-1567
            if value is not None and not (key == 'OSG_APP' and value == 'UNSET'):
                export_string += "export %s\n" % key

    file_contents = """\
#!/bin/sh
#---------- This file automatically generated by osg-configure
#---------- This is periodically overwritten.  DO NOT HAND EDIT
#---------- Instead, write any environment variable customizations into
#---------- the config.ini [Local Settings] section, as documented here:
#---------- https://twiki.opensciencegrid.org/bin/view/Documentation/Release3/IniConfigurationOptions#Local_Settings
#---  variables -----
%s
#--- export variables -----
%s
""" % (variable_string, export_string)
    return file_contents


def write_attribute_file(filename=None, attributes=None):
    """
    Write attributes to osg attributes file in an atomic fashion
    """
    if filename:
        file_contents = _compose_attribute_file(attributes or {})
        atomic_write(filename, file_contents, mode=0644)


def get_set_membership(test_set, reference_set, defaults=None):
    """
    See if test_set has any elements that aren't keys of the reference_set
    or optionally defaults.  Takes lists as arguments
    """
    missing_members = []

    if defaults is None:
        defaults = []
    for member in test_set:
        if member not in reference_set and member not in defaults:
            missing_members.append(member)
    return missing_members


def get_hostname():
    """Returns the hostname of the current system"""
    try:
        return socket.getfqdn()
    # pylint: disable-msg=W0703
    except Exception:
        return None


def blank(value):
    """Check the value to check to see if it is 'UNAVAILABLE' or blank, return True
    if that's the case
    """
    if value is None:
        return True

    temp_val = str(value)

    return (temp_val.upper().startswith('UNAVAILABLE') or
            temp_val.upper() == 'DEFAULT' or
            temp_val == "None" or
            temp_val == "")


def get_vos(user_vo_file):
    """
    Returns a list of valid VO names.
    """

    if (user_vo_file is None or
            not os.path.isfile(user_vo_file)):
        user_vo_file = '/var/lib/osg/user-vo-map'
    if not os.path.isfile(user_vo_file):
        return []
    file_buffer = open(user_vo_file, 'r')
    vo_list = []
    for line in file_buffer:
        try:
            line = line.strip()
            if line.startswith("#"):
                continue
            vo = line.split()[1]
            if vo.startswith('us'):
                vo = vo[2:]
            if vo not in vo_list:
                vo_list.append(vo)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            pass
    return vo_list


def service_enabled(service_name):
    """
    Check to see if a service is enabled
    """
    if service_name is None or service_name == "":
        return False
    process = subprocess.Popen(['/sbin/service', '--list', service_name],
                               stdout=subprocess.PIPE)
    output = process.communicate()[0]
    if process.returncode != 0:
        return False

    match = re.search(service_name + r'\s*\|.*\|\s*([a-z ]*)$', output)
    if match:
        # The regex above captures trailing whitespace, so remove it
        # before we make the comparison. -Scot Kronenfeld 2010-10-08
        if match.group(1).strip() == 'enable':
            return True
        else:
            return False
    else:
        return False


def fetch_crl():
    """
    Run fetch_crl script and return a boolean indicating whether it was successful
    """

    try:
        crl_files = glob.glob('/etc/grid-security/certificates/*.r0')
        if len(crl_files) > 0:
            sys.stdout.write("CRLs exist, skipping fetch-crl invocation\n")
            sys.stdout.flush()
            return True

        crl_path = '/usr/sbin'
        if rpm_installed('fetch-crl'):
            crl_path = os.path.join(crl_path, 'fetch-crl')
        elif rpm_installed('fetch-crl3'):
            crl_path = os.path.join(crl_path, 'fetch-crl3')

        # Some CRLs are often problematic; it's better to ignore some errors than to halt configuration. (SOFTWARE-1428)
        error_message_whitelist = [  # whitelist partially taken from osg-test
                                     'CRL has lastUpdate time in the future',
                                     'CRL has nextUpdate time in the past',
                                     'CRL verification failed for',
                                     'Download error',
                                     'CRL retrieval for',
                                     r'^\s*$',
                                     ]
        try:
            fetch_crl_process = subprocess.Popen([crl_path, '-p', '10', '-T', '30'], stdout=subprocess.PIPE,
                                                 stderr=subprocess.STDOUT)
        except OSError, e:
            if e.errno == errno.ENOENT:
                sys.stdout.write("Can't find fetch-crl script, skipping fetch-crl invocation\n")
                sys.stdout.flush()
                return True
            else:
                raise
        sys.stdout.write("Running %s, this process may take " % crl_path +
                         "some time to fetch all the crl updates\n")
        sys.stdout.flush()
        outerr = fetch_crl_process.communicate()[0]
        if fetch_crl_process.returncode != 0:
            sys.stdout.write("fetch-crl script had some errors:\n" + outerr + "\n")
            sys.stdout.flush()
            for line in outerr.rstrip("\n").split("\n"):
                for msg in error_message_whitelist:
                    if re.search(msg, line):
                        break
                else:
                    return False
            sys.stdout.write("Ignoring errors and continuing\n")
            sys.stdout.flush()
    except IOError:
        return False
    return True


def run_script(script):
    """
    Arguments:
    script - a string or a list of arguments to run formatted while
             the args argument to subprocess.Popen

    Returns:
    True if script runs successfully, False otherwise
    """

    try:
        process = subprocess.Popen(script)
    except OSError, e:
        if e.errno == errno.ENOENT:
            return False
        else:
            raise
    process.communicate()
    if process.returncode != 0:
        return False

    return True


def get_condor_location(default_location='/usr'):
    """
    Check environment variables to try to get condor location
    """

    if 'CONDOR_LOCATION' in os.environ:
        return os.path.normpath(os.environ['CONDOR_LOCATION'])
    elif not blank(default_location):
        return default_location
    else:
        return ""


def get_condor_config(default_config='/etc/condor/condor_config'):
    """
    Check environment variables to try to get condor config
    """

    if 'CONDOR_CONFIG' in os.environ:
        return os.path.normpath(os.environ['CONDOR_CONFIG'])
    elif not blank(default_config):
        return os.path.normpath(default_config)
    else:
        return os.path.join(get_condor_location(), 'etc/condor_config')


def get_condor_config_val(variable, executable='condor_config_val', quiet_undefined=False):
    """
    Use condor_config_val to return the expanded value of a variable.

    Arguments:
    variable - name of the variable whose value to return
    executable - the name of the executable to use (in case we want to
                 poll condor_ce_config_val or condor_cron_config_val)
    quiet_undefined - set to True if messages from condor_config_val
                 claiming the variable is undefined should be silenced
    Returns:
    The stripped output of condor_config_val, or None if
    condor_config_val reports an error.
    """
    try:
        process = subprocess.Popen([executable, '-expand', variable],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        if error and not (error.startswith('Not defined:') and quiet_undefined):
            sys.stderr.write(error)
        if process.returncode != 0:
            return None
        return output.strip()
    except OSError:
        return None


def read_file(filename, default=None):
    """
    Read the contents of a file, returning default if the file cannot be read.

    :param filename: name of file to read
    :type filename: str
    :param default: value to return if file cannot be read
    :return: contents of the file or default
    """
    contents = default
    try:
        fh = open(filename, 'r')
        try:
            contents = fh.read()
        finally:
            fh.close()
    except EnvironmentError:
        pass
    return contents


def atomic_write(filename=None, contents=None, **kwargs):
    """
    Atomically write contents to a file

    Arguments:
    filename - name of the file that needs to be written
    contents - string with contents to write to file

    Keyword arguments:
    mode - permissions for the file, if set to None the previous
           permissions will be preserved

    Returns:
    True if file has successfully been written, False otherwise

    """

    if filename is None or contents is None:
        return True

    try:
        (config_fd, temp_name) = tempfile.mkstemp(dir=os.path.dirname(filename))
        mode = kwargs.get('mode', None)
        if mode is None:
            try:
                mode = stat.S_IMODE(os.stat(filename).st_mode)
            except OSError, e:
                if e.errno == errno.ENOENT:
                    # file doesn't exist; give it 0644 permissions by default
                    mode = 0644
                else:
                    raise
        try:
            try:
                os.write(config_fd, contents)
                # need to fsync data to make sure data is written on disk before renames
                # see ext4 documentation for more information
                os.fsync(config_fd)
            finally:
                os.close(config_fd)
        except:
            os.unlink(temp_name)
            raise
        os.rename(temp_name, filename)
        os.chmod(filename, mode)
    except EnvironmentError:
        return False
    return True


def ce_installed():
    """
    Return True if one of the base osg-ce metapackages (osg-ce or osg-htcondor-ce) is installed
    """
    return any_rpms_installed('osg-ce', 'osg-htcondor-ce')


def gateway_installed():
    """
    Check to see if a job gateway (i.e. globus-gatekeeper or htcondor-ce) is installed
    """
    return any_rpms_installed('globus-gatekeeper', 'htcondor-ce')


def any_rpms_installed(*rpm_names):
    """
    Check if any of the rpms in the list are installed
    :param rpms: One or more RPM names
    :return: True if any of the listed RPMs are installed, False otherwise
    """
    if isinstance(rpm_names[0], list) or isinstance(rpm_names[0], tuple):
        rpm_names = list(rpm_names[0])
    return (True in (rpm_installed(rpm_name) for rpm_name in rpm_names))


def rpm_installed(rpm_name):
    """
    Check to see if given rpm is installed

    Arguments:
    rpm_name - a string with rpm name to check or a Iteratable with rpms that
               should be checked

    Returns:
    True if rpms are installed, False otherwise
    """
    trans_set = rpm.TransactionSet()
    if isinstance(rpm_name, types.StringType):
        return trans_set.dbMatch('name', rpm_name).count() in (1, 2)

    # check with iterable type
    try:
        for name in rpm_name:
            if trans_set.dbMatch('name', name).count() not in (1, 2):
                return False
        return True
    # pylint: disable-msg=W0703
    except Exception:
        return False


def get_test_config(config_file=''):
    """
    Try to figure out whether where the config files for unit tests are located,
    preferring the ones in the local directory

    Arguments:
    config_file - name of config file being checked, can be an empty string or
      set to None

    Returns:
    the prefixed config file if config_file is non-empty, otherwise just the
    prefix, returns None if no path exists
    """

    config_prefix = './configs'
    sys_prefix = '/usr/share/osg-configure/tests/configs'

    if config_file == '' or config_file is None:
        return None

    test_location = os.path.join(config_prefix, config_file)
    if os.path.exists(test_location):
        return os.path.abspath(test_location)
    test_location = os.path.join(sys_prefix, config_file)
    if os.path.exists(test_location):
        return os.path.abspath(test_location)
    return None


def make_directory(dir_name, perms=0755, uid=None, gid=None):
    """
    Create a directory with specified permissions and uid/gid.  Will use the
    current user's uid and gid if not specified.

    returns True is successful
    """

    if uid is None:
        uid = os.getuid()
    if gid is None:
        gid = os.getgid()
    try:
        os.makedirs(dir_name, perms)
        os.chown(dir_name, uid, gid)
        return True
    except IOError:
        return False


def get_os_version():
    """
    Get and return OS major version
    """
    version = platform.dist()[1]
    version_list = [int(x) for x in version.split('.')]
    return version_list


def config_safe_get(configuration, section, option, default=None):
    """
    Return the value of the option `option` from the config section
    `section` or `default` if the section or the option are missing

    :type configuration: ConfigParser.ConfigParser
    :type section: str
    :type option: str
    """
    try:
        return configuration.get(section, option)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
        return default


def config_safe_getboolean(configuration, section, option, default=None):
    """
    Wrapper around RawConfigParser.getboolean the way config_safe_get is a
    wrapper around RawConfigParser.get. Note that it also returns default
    in case of a ValueError, which is raised if the value is not a valid
    boolean.

    :type configuration: ConfigParser.ConfigParser
    :type section: str
    :type option: str
    """
    try:
        return configuration.getboolean(section, option)
    except (ConfigParser.NoOptionError, ConfigParser.NoSectionError, ValueError):
        return default


def fallback_classad_quote(input_value):
    r"""Quote a Python string according to classad syntax (fallback if classad.quote is missing)

    Reference: http://pegasus.isi.edu/wms/docs/3.0/javadoc/edu/isi/pegasus/planner/code/generator/condor/CondorQuoteParser.html
    This is an implementation according to the state diagram on that page.
    """

    def A0(_):
        return ''

    def A1(inchar_):
        return inchar_

    def A2(_):
        return "'"

    def A3(_):
        return "''"

    def A4(_):
        return '""'

    S0 = 'S0'
    S1 = 'S1'
    S2 = 'S2'
    S3 = 'S3'
    BACKSLASH = "\\"
    SINGLE = "'"
    DOUBLE = '"'
    OTHER = 'other'

    STATE_TABLE = {
        S0: {BACKSLASH: (A0, S0), SINGLE: (A2, S2), DOUBLE: (A2, S3), OTHER: (A1, S0)},
        S1: {BACKSLASH: (A1, S0), SINGLE: (A3, S0), DOUBLE: (A4, S0), OTHER: (A1, S0)},
        S2: {BACKSLASH: (A1, S2), SINGLE: (A2, S0), DOUBLE: (A4, S2), OTHER: (A1, S2)},
        S3: {BACKSLASH: (A1, S3), SINGLE: (A3, S3), DOUBLE: (A2, S0), OTHER: (A1, S3)}
    }

    quoted_value = ""
    state = S0
    for inchar in str(input_value):
        if inchar in STATE_TABLE[state]:
            nextchar_fun, state = STATE_TABLE[state][inchar]
        else:
            nextchar_fun, state = STATE_TABLE[state][OTHER]
        quoted_value += nextchar_fun(inchar)

    if state == S0:
        return '"' + quoted_value + '"'
    elif state == S1:
        raise ValueError("Unexpected end of input in '%s'" % input_value)
    elif state == S2:
        raise ValueError("Unmatched single quotes in '%s'" % input_value)
    elif state == S3:
        raise ValueError("Unmatched double quotes in '%s'" % input_value)


try:
    import classad

    _classad_quote = classad.quote

    def classad_quote(input_value):
        return _classad_quote(str(input_value))
except (ImportError, AttributeError):
    classad_quote = fallback_classad_quote


def add_or_replace_setting(old_buf, variable, new_value, quote_value=True):
    """
    If there is a line setting 'variable' in 'old_buf' (in a "var=value" format),
    change it to set variable to new_value. If there is no such line, add a line
    to the end of buf setting variable to new_value. Return the modified buf.

    If quote_value is True (default), the value is double-quoted first
    """
    if quote_value:
        new_value = '"%s"' % new_value

    new_line = '%s=%s' % (variable, new_value)
    new_buf, count = re.subn(r'(?m)^\s*%s\s*=.*$' % re.escape(variable), new_line, old_buf, 1)
    if count == 0:
        new_buf += new_line + "\n"
    return new_buf


def split_host_port(host_port):
    """Return a tuple containing (host, port) of a string possibly
    containing both.  If there is no port in host_port, the port
    will be None.

    Supports the following:
    - hostnames
    - ipv4 addresses
    - ipv6 addresses
    with or without ports.  There is no validation of either the
    host or port.

    """
    colon_count = host_port.count(':')
    if colon_count == 0:
        # hostname or ipv4 address without port
        try:
            return host_port, None
        except ValueError:
            return False
    elif colon_count == 1:
        # hostname or ipv4 address with port
        return host_port.split(':', 1)
    elif colon_count >= 2:
        # ipv6 address, must be bracketed if it has a port at the end, i.e. [ADDR]:PORT
        if ']:' in host_port:
            host, port = host_port.split(']:', 1)
            if host[0] == '[':
                # for valid addresses, should always be true
                host = host[1:]
            return host, port
        else:
            # no port; may still be bracketed
            host = host_port
            if host[0] == '[':
                host = host[1:]
            if host[-1] == ']':
                host = host[:-1]
            return host, None


class NullLogger(logging.Logger):
    """A dummy Logger where the logging functions ignore all parameters
    passed to it.  They are static methods so you don't need to instantiate
    it.  Useful as a default value for functions which take a logger as an
    argument.

    """
    @staticmethod
    def info(*args, **kwargs): pass
    @staticmethod
    def warning(*args, **kwargs): pass
    @staticmethod
    def error(*args, **kwargs): pass
    @staticmethod
    def critical(*args, **kwargs): pass
    @staticmethod
    def debug(*args, **kwargs): pass
    @staticmethod
    def log(*args, **kwargs): pass
