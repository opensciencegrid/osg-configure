""" Module to handle attributes related to the site location and details """

import re
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['SiteInformation']

# convenience
MANDATORY = configfile.Option.MANDATORY
MANDATORY_ON_CE = configfile.Option.MANDATORY_ON_CE
OPTIONAL = configfile.Option.OPTIONAL

class SiteInformation(BaseConfiguration):
    """Class to handle attributes related to site information such as location and
    contact information
    """
    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('SiteInformation.__init__ started')
        self.options = {'group':
                            configfile.Option(name='group',
                                              required=MANDATORY,
                                              default_value='OSG',
                                              mapping='OSG_GROUP'),
                        'host_name':
                            configfile.Option(name='host_name',
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_HOSTNAME'),
                        'resource':
                            configfile.Option(name='resource',
                                              required=MANDATORY,
                                              mapping='OSG_SITE_NAME'),
                        'resource_group':
                            configfile.Option(name='resource_group',
                                              default_value='',
                                              required=OPTIONAL)}

        self.config_section = "Site Information"
        self.enabled = True
        self.log('SiteInformation.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        self.log('SiteInformation.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('SiteInformation.parse_configuration completed')
            return

        self.get_options(configuration,
                         ignore_options=[
                             "city",
                             "contact",
                             "country",
                             "email",
                             "latitude",
                             "longitude",
                             "site_policy",
                             "sponsor",
                         ])
        self.log('SiteInformation.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('SiteInformation.check_attributes started')
        attributes_ok = True

        if not self.enabled:
            self.log('Not enabled, returning True')
            self.log('SiteInformation.check_attributes completed')
            return attributes_ok

        # OSG_GROUP must be either OSG or OSG-ITB
        group = self.opt_val("group")
        if group not in ('OSG', 'OSG-ITB'):
            self.log("The group setting must be either OSG or OSG-ITB, got: %s" %
                     group,
                     option='group',
                     section=self.config_section,
                     level=logging.ERROR)
            attributes_ok = False

        host_name = self.opt_val("host_name")
        if not utilities.blank(host_name):
            if not validation.valid_domain(host_name, resolve=False):
                self.log("%s is not a valid domain", host_name,
                         option="host_name",
                         section=self.config_section,
                         level=logging.ERROR)
                attributes_ok = False
            elif not validation.valid_domain(host_name, resolve=True):
                self.log("%s is a valid domain but can't be resolved", host_name,
                         option="host_name",
                         section=self.config_section,
                         level=logging.WARNING)

        self.log('SiteInformation.check_attributes completed')
        return attributes_ok

    def module_name(self):
        """Return a string with the name of the module"""
        return "SiteInformation"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True
