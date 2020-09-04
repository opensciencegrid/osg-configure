""" Module to handle squid configuration and setup """

import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['SquidConfiguration']


class SquidConfiguration(BaseConfiguration):
    """Class to handle attributes related to squid configuration and setup"""

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('SquidConfiguration.__init__ started')
        self.options = {'location':
                            configfile.Option(name='location',
                                              default_value='None',
                                              mapping='OSG_SQUID_LOCATION')}
        self.config_section = 'Squid'
        self.log('SquidConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        self.log('SquidConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('SquidConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('SquidConfiguration.parse_configuration completed')
            if not self.ignored and not self.enabled:
                return True

        self.get_options(configuration, ignore_options=['enabled', 'policy', 'cache_size', 'memory_size'])

        if not (utilities.blank(self.options['location'].value) or
                        self.options['location'].value == 'None'):
            if ":" not in self.options['location'].value:
                self.options['location'].value += ":3128"

        if configuration.get(self.config_section, 'location').upper() == 'UNAVAILABLE':
            self.options['location'].value = 'UNAVAILABLE'
        self.log('SquidConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('SquidConfiguration.check_attributes started')
        attributes_ok = True
        if not (utilities.gateway_installed() and utilities.rpm_installed('frontier-squid')):
            return attributes_ok

        if not self.enabled:
            self.log("Squid is not enabled, sites must enable this \n" +
                     "section, location can be set to UNAVAILABLE if squid is \n" +
                     "not present",
                     level=logging.WARNING)
            self.log('squid not enabled')
            self.log('SquidConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('SquidConfiguration.check_attributes completed')
            return attributes_ok

        if (self.options['location'].value == 'None'):
            self.log("location setting must be set, if site does not provide " +
                     "squid, please use UNAVAILABLE",
                     section=self.config_section,
                     option='location',
                     level=logging.WARNING)
            return attributes_ok

        if (self.options['location'].value.upper() == 'UNAVAILABLE'):
            self.log("Squid location is set to UNAVAILABLE.  Although this is \n" +
                     "allowed, most jobs function better and use less bandwidth \n" +
                     "when a squid proxy is available",
                     level=logging.WARN)
            self.options['location'].value = 'None'
            return attributes_ok

        if len(self.options['location'].value.split(':')) != 2:
            self.log("Bad host specification, got %s expected hostname:port " \
                     "(e.g. localhost:3128)" % self.options['location'].value,
                     section=self.config_section,
                     option='location',
                     level=logging.ERROR)
            attributes_ok = False
            return attributes_ok
        (hostname, port) = self.options['location'].value.split(':')
        if not validation.valid_domain(hostname, True):
            self.log("Invalid hostname for squid location: %s" % \
                     self.options['location'].value,
                     section=self.config_section,
                     option='location',
                     level=logging.ERROR)
            attributes_ok = False
        try:
            int(port)
        except ValueError:
            self.log("The port must be a number(e.g. host:3128) for squid " \
                     "location: %s" % self.options['location'].value,
                     section=self.config_section,
                     option='location',
                     level=logging.ERROR,
                     exception=True)
            attributes_ok = False

        self.log('SquidConfiguration.check_attributes completed')
        return attributes_ok

    # pylint: disable-msg=W0613
    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('SquidConfiguration.configure started')

        if not self.enabled:
            self.log('squid not enabled')
            self.log('SquidConfiguration.configure completed')
            return True

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('SquidConfiguration.configure completed')
            return True

        self.log('SquidConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "Squid"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def get_attributes(self, converter=str):
        """
        Get attributes for the osg attributes file using the dict in self.options

        Returns a dictionary of ATTRIBUTE => value mappings

        Need to override parent class method since two options may map to OSG_SITE_NAME
        """

        self.log("%s.get_attributes started" % self.__class__)

        attributes = BaseConfiguration.get_attributes(self)
        if self.ignored:
            self.log("%s.get_attributes completed" % self.__class__)
            return dict(zip([item.mapping for item in self.options.values() if item.is_mappable()],
                            [str(item.value) for item in self.options.values() if item.is_mappable()]))
        elif not self.enabled:
            self.log("%s.get_attributes completed" % self.__class__)
            return attributes
        elif self.options['location'].value in ('None', 'UNAVAILABLE'):
            del attributes['OSG_SQUID_LOCATION']
            self.log("Blank location or location set to UNAVAILABLE, " +
                     "not setting environment variable")
            self.log("%s.get_attributes completed" % self.__class__)
            return attributes

        self.log("%s.get_attributes completed" % self.__class__)
        return attributes
