""" Base class for all configuration classes """

import configparser
import errno
import logging
import os
import pwd

from osg_configure.modules import configfile
from osg_configure.modules import utilities
from osg_configure.modules import exceptions

__all__ = ['BaseConfiguration']

HOSTCERT_PATH = "/etc/grid-security/hostcert.pem"
HOSTKEY_PATH = "/etc/grid-security/hostkey.pem"


class BaseConfiguration:
    """Base class for inheritance by configuration"""

    # pylint: disable-msg=W0613
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.ignored = False
        self.enabled = False
        self.options = {}
        self.config_section = ""

    def set_status(self, configuration):
        """
        Check the enable option and then set the appropriate attributes based on that.

        Returns False if the section is not enabled or set to ignore
        """

        try:
            if not configuration.has_option(self.config_section, 'enabled'):
                self.logger.debug("%s not enabled" % self.config_section)
                self.enabled = False
                return False
            elif configuration.get(self.config_section, 'enabled').lower() == 'ignore':
                self.logger.debug("%s will be ignored" % self.config_section)
                self.ignored = True
                self.enabled = False
                return False
            elif not configuration.getboolean(self.config_section, 'enabled'):
                self.logger.debug("%s not enabled" % self.config_section)
                self.enabled = False
                return False
            else:
                self.enabled = True
                return True
        except configparser.NoOptionError:
            raise exceptions.SettingError("Can't get value for enable option "
                                          "in %s section" % self.config_section)

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        pass

    # pylint: disable-msg=W0613
    # pylint: disable-msg=R0201
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        attributes_ok = True
        return attributes_ok

    # pylint: disable-msg=W0613
    def configure(self, attributes):
        """Configure installation using attributes"""
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "BaseConfiguration"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return False

    def log(self, mesg, *args, **kwargs):
        """
        Generate a log message if option and section are given then the file
        that generated the error is added to log message

        Arguments:
        mesg - message to add to default log message
        args - arguments to substitute into mesg

        Keyword Arguments:
        option - option that caused the log message to be created
        section - the section that the option given above is location in
        level - optional log level for message, should be a level from
                logging, defaults to logging.DEBUG if none given
        exception - if True, adds exception information to log file
        """

        log_level = kwargs.get('level', logging.DEBUG)
        exception = kwargs.get('exception', False)
        message = ""
        if 'option' in kwargs and 'section' in kwargs:
            file_location = configfile.get_option_location(kwargs['option'],
                                                           kwargs['section'])
            if file_location is not None:
                message = "Option '%s' in section '%s' located in %s: " % (kwargs['option'],
                                                                           kwargs['section'],
                                                                           file_location)
                message += "\n" + " " * 9 + ("\n" + " " * 9).join(mesg.split("\n"))
            else:
                message += mesg
        else:
            message += mesg
        self.logger.log(log_level, message, *args, exc_info=exception)

    @staticmethod
    def check_config(configuration):
        """
        Make sure config argument is of the correct type
        """

        if not isinstance(configuration, configparser.ConfigParser):
            raise TypeError('Invalid type for configuration, must be a '
                            'ConfigParser or subclass')

    def get_options(self, configuration, **kwargs):
        """
        Populate self.options based on contents of ConfigParser object,
        warns if unknown options are found

        arguments:
        configuration - a ConfigParser object

        keyword arguments:
        ignore_options - a list of option names that should be ignored
                         when checking for unknown options
        """

        self.check_config(configuration)
        for option in self.options.values():
            self.log("Getting value for %s" % option.name)
            try:
                configfile.get_option(configuration,
                                      self.config_section,
                                      option)
                self.log("Got %s" % option.value)
            except configparser.Error as err:
                self.log("Syntax error in configuration: %s" % err,
                         option=option.name,
                         section=self.config_section,
                         level=logging.ERROR,
                         exception=False)
                raise exceptions.SettingError(str(err))
            except Exception:
                self.log("Received exception when parsing option",
                         option=option.name,
                         section=self.config_section,
                         level=logging.ERROR,
                         exception=False)
                raise

        # check and warn if unknown options found
        known_options = list(self.options.keys())
        known_options.extend(kwargs.get('ignore_options', []))
        temp = utilities.get_set_membership(configuration.options(self.config_section),
                                            known_options,
                                            configuration.defaults().keys())
        for option in temp:
            self.log("Found unknown option",
                     option=option,
                     section=self.config_section,
                     level=logging.WARNING)

    def opt_val(self, opt_name):
        """Return the value of an option by name."""
        return self.options[opt_name].value

    def get_attributes(self, converter=str):
        """
        Get attributes for the osg attributes file using the dict in self.options

        Arguments:
        converter -- function that converts various types to strings
        Returns a dictionary of ATTRIBUTE => value mappings
        """

        self.log("%s.get_attributes started" % self.__class__)
        if not self.enabled:
            self.log("Not enabled, returning {}")
            self.log("%s.get_attributes completed" % self.__class__)
            return {}

        if self.options == {} or self.options is None:
            self.log("self.options empty or None, returning {}")
            self.log("%s.get_attributes completed" % self.__class__)
            return {}

        mappings = {}
        for item in self.options.values():
            if not item.is_mappable():
                continue
            if item.value is None:
                mappings[item.mapping] = None
            else:
                mappings[item.mapping] = converter(item.value)

        self.log("%s.get_attributes completed" % self.__class__)
        return mappings

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """
        return set()

    @staticmethod
    def section_disabled(configuration, section):
        """
        Check the enable option for a specified section

        Returns False if the section is not enabled or set to ignore
        """

        try:
            if not configuration.has_option(section, 'enabled'):
                return True
            elif configuration.get(section, 'enabled').lower() == 'ignore':
                return True
            elif not configuration.getboolean(section, 'enabled'):
                return True
            else:
                return False
        except configparser.NoOptionError:
            raise exceptions.SettingError("Can't get value for enable option "
                                          "in %s section" % section)

    def create_missing_service_cert_key(self, service_cert, service_key, user):
        """Copy the host cert and key to a service cert and key with the
        appropriate permissions if the service cert and key do not already
        exist. If they already exist, nothing is done. If only one of them
        exists, this method returns with an error. Parent directories are
        created as needed.

        :param service_cert: Path to the service certificate to create
        :type service_cert: str
        :param service_key: Path to the service private key to create
        :type service_key: str
        :param user: The name of the user that will own the cert and key
        :type user: str

        :return: True if service_cert and service_key are both created or already present, False otherwise

        """
        user_pwd = pwd.getpwnam(user)
        if not user_pwd:
            self.log("%r user not found, cannot create service cert/key with correct permissions" % user,
                     level=logging.ERROR)
            return False

        if os.path.isfile(service_cert) and os.path.isfile(service_key):
            self.log("%s and %s both exist; not creating them" % (service_cert, service_key),
                     level=logging.INFO)
        elif os.path.isfile(service_cert) and not os.path.isfile(service_key):
            self.log("%s exists but %s does not! Either remove the cert or copy the matching key" % (service_cert,
                                                                                                     service_key),
                     level=logging.ERROR)
            return False
        elif os.path.isfile(service_key) and not os.path.isfile(service_cert):
            self.log("%s exists but %s does not! Either remove the key or copy the matching cert" % (service_key,
                                                                                                     service_cert),
                     level=logging.ERROR)
            return False
        else:
            for from_path, to_path, mode in [[HOSTCERT_PATH, service_cert, int('644', 8)],
                                             [HOSTKEY_PATH, service_key, int('600', 8)]]:
                # Create dirs for the cert/key if they don't exist
                parent_dir = os.path.abspath(os.path.dirname(to_path))
                try:
                    os.makedirs(parent_dir)
                except OSError as err:
                    if err.errno != errno.EEXIST:
                        self.log("Could not create directory %s" % parent_dir, exception=err, level=logging.ERROR)
                        return False
                try:
                    os.chown(parent_dir, user_pwd.pw_uid, user_pwd.pw_gid)
                except EnvironmentError as err:
                    self.log("Could not set ownership of %s" % parent_dir, exception=err, level=logging.ERROR)
                    return False
                from_fh = open(from_path, 'rb')
                success = utilities.atomic_write(to_path, from_fh.read(), mode=mode)
                from_fh.close()
                if not success:
                    self.log("Could not copy %s to %s" % (from_path, to_path), level=logging.ERROR)
                    return False
                try:
                    os.chown(to_path, user_pwd.pw_uid, user_pwd.pw_gid)
                except EnvironmentError as err:
                    self.log("Could not set ownership of %s" % to_path, exception=err, level=logging.ERROR)
                    return False

        return True
