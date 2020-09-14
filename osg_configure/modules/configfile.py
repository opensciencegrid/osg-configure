""" Module to hold various utility functions """

import glob
import configparser
import os
import sys

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation

__all__ = ['get_option_location',
           'get_file_list',
           'read_config_files',
           'get_option',
           'jobmanager_enabled',
           'Option']

CONFIG_DIRECTORY = '/etc/osg/config.d'


def read_config_files(**kwargs):
    """
    Read config files located in /etc/osg/config.d and return a config parser
    object for it

    Keyword arguments:
    config_directory -- indicates which directory holds the config files
    case_sensitive -- indicates whether the ConfigParser should be case
      sensitive when parsing the config file, this is needed for Local Options
      section

    Raises:
    IOError -- error when parsing files
    """

    config_dir = kwargs.get('config_directory', CONFIG_DIRECTORY)
    case_sensitive = kwargs.get('case_sensitive', False)
    if not validation.valid_directory(config_dir):
        raise IOError("%s does not exist" % config_dir)
    file_list = get_file_list(config_directory=config_dir)
    for filename in file_list:
        if not validation.valid_ini_file(filename):
            sys.stderr.write("Error found in %s\n" % filename)
            sys.exit(1)
    try:
        config = configparser.SafeConfigParser()
        if case_sensitive:
            config.optionxform = str
    except configparser.Error as e:
        raise IOError("Can't read and parse config files:\n%s" % e)
    read_files = config.read(file_list, encoding="latin-1")
    read_files.sort()
    if file_list != read_files:
        unread_files = set(file_list).difference(read_files)
        msg = "Can't read following config files:\n %s" % ("\n".join(unread_files))
        raise IOError(msg)
    return config


def get_option_location(option, section, **kwargs):
    """
    Check for and returns the filename that sets the value of the given option
    Returns None if option or section is not defined.  NOTE: does not handle
    variable interpolation

    Formal arguments:
    option -- option name to look for
    section -- section that the option is located in

    Keyword arguments:
    config_directory -- indicates which directory holds the config files

    Raises:
    IOError -- Can't read a given file
    Exception -- Can't parse a config file in the config directory
    """
    config_dir = kwargs.get('config_directory', CONFIG_DIRECTORY)
    file_list = get_file_list(config_directory=config_dir)
    file_list.reverse()
    for fn in file_list:
        try:
            config = configparser.SafeConfigParser()
            config.readfp(open(fn, "r", encoding="latin-1"))
            if config.has_option(section, option):
                return fn
        except configparser.Error as e:
            raise Exception("Can't parse %s:\n%s" % (fn, e))

    return None


def get_file_list(**kwargs):
    """
    Get the list of files in the sequence that the config parser object will read them

    Keyword arguments:
    config_directory -- indicates which directory holds the config files
    """
    config_dir = kwargs.get('config_directory', CONFIG_DIRECTORY)
    file_list = glob.glob(os.path.join(config_dir, '[!.]*.ini'))
    file_list.sort()
    return file_list


def get_option(config, section, option):
    """
    Get an option from a config file with optional defaults and mandatory
    options.

    Arguments
    config  -- a ConfigParser object to query
    section --  the ini section the option is located in
    option  --  an Option object to information on the option to retrieve

    """
    is_required_option = (option.required == Option.MANDATORY
                          or (option.required == Option.MANDATORY_ON_CE and utilities.ce_installed()))
    if config.has_option(section, option.name):
        try:

            if not utilities.blank(config.get(section, option.name)):
                if option.opt_type == bool:
                    option.value = config.getboolean(section, option.name)
                elif option.opt_type == int:
                    option.value = config.getint(section, option.name)
                elif option.opt_type == float:
                    option.value = config.getfloat(section, option.name)
                else:
                    option.value = config.get(section, option.name)
            else:
                # if option is blank and there's a default for the option
                # return the default if possible, otherwise raise an exception
                # if the option is mandatory

                if option.default_value is not None:
                    option.value = option.default_value
                elif is_required_option:
                    raise exceptions.SettingError("Can't get value for %s in %s " \
                                                  "section and no default given" % \
                                                  (option.name, section))
        except ValueError:
            error_mesg = "%s  in %s section is of the wrong type" % (option.name, section)
            raise exceptions.SettingError(error_mesg)
    elif is_required_option:
        err_mesg = "Can't get value for %s in %s section" % (option.name, section)
        raise exceptions.SettingError(err_mesg)
    else:
        option.value = option.default_value


def jobmanager_enabled(configuration):
    """
    Check the configuration file and enable this module if the configuration
    is for a ce. A configuration is for a ce if it enables one of the job manager
    sections

    Keyword arguments:
    configuration -- ConfigParser object to check
    """

    jobmanagers = ['PBS', 'Condor', 'SGE', 'LSF', 'SLURM', 'BOSCO']
    for jobmanager in jobmanagers:
        if (configuration.has_section(jobmanager) and
                configuration.has_option(jobmanager, 'enabled') and
                configuration.getboolean(jobmanager, 'enabled')):
            return True

    return False


class Option:
    """
    Class to encapsulate options as used by osg_configure
    """
    MANDATORY = 1
    OPTIONAL = 2
    MANDATORY_ON_CE = 3

    def __init__(self, **kwargs):
        """
        Initialize class members

        Keyword args:
        value - option value
        opt_type - option type from types module or built-in type, use None if not given
        default_value - option's default value
        mapping - option's mapping in osg attributes file, None if option should
                  not be written to file
        required - whether file should is required to be in config file or not
                   use Option.MANDATORY, Option.OPTIONAL, or Option.MANDATORY_ON_CE
        name - option name
        """

        self.opt_type = kwargs.get('opt_type', str)
        if self.opt_type == str:
            self.value = kwargs.get('value', '')
        elif self.opt_type == int or self.opt_type == float:
            self.value = kwargs.get('value', 0)
        else:
            self.value = None
        self.default_value = kwargs.get('default_value', None)
        self.required = kwargs.get('required', Option.MANDATORY)
        self.name = kwargs.get('name', 'option')
        self.mapping = kwargs.get('mapping', None)

    def __setattr__(self, name, value):
        """
        Check type when setting value and enforce requirements for self.value if
        self.opt_type is specified
        """
        if name == 'value' and value is not None and self.opt_type is not None:
            if type(value) == self.opt_type:
                self.__dict__[name] = value
            else:
                # raises ValueError if conversion can't be done
                self.__dict__[name] = self.opt_type(value)
        else:
            self.__dict__[name] = value

    def is_mappable(self):
        """
        Returns True if there is a mapping from option name to attribute
        in osg attributes file
        """
        return self.mapping is not None
