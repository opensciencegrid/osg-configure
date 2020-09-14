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
                        'sponsor':
                            configfile.Option(name='sponsor',
                                              required=OPTIONAL,
                                              default_value='',
                                              mapping='OSG_SPONSOR'),
                        'site_policy':
                            configfile.Option(name='site_policy',
                                              required=OPTIONAL,
                                              default_value='',
                                              mapping='OSG_SITE_INFO'),
                        'contact':
                            configfile.Option(name='contact',
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_CONTACT_NAME'),
                        'email':
                            configfile.Option(name='email',
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_CONTACT_EMAIL'),
                        'city':
                            configfile.Option(name='city',
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_SITE_CITY'),
                        'country':
                            configfile.Option(name='country',
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_SITE_COUNTRY'),
                        'longitude':
                            configfile.Option(name='longitude',
                                              opt_type=float,
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_SITE_LONGITUDE'),
                        'latitude':
                            configfile.Option(name='latitude',
                                              opt_type=float,
                                              required=MANDATORY_ON_CE,
                                              mapping='OSG_SITE_LATITUDE'),
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

        self.get_options(configuration)
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

        latitude = self.opt_val("latitude")
        if not utilities.blank(latitude) and not -90 <= latitude <= 90:
            self.log("Latitude must be between -90 and 90, got %s" %
                     latitude,
                     section=self.config_section,
                     option='latitude',
                     level=logging.ERROR)
            attributes_ok = False

        longitude = self.opt_val("longitude")
        if not utilities.blank(longitude) and not -180 <= longitude <= 180:
            self.log("Longitude must be between -180 and 180, got %s" %
                     longitude,
                     section=self.config_section,
                     option='longitude',
                     level=logging.ERROR)
            attributes_ok = False

        email = self.opt_val("email")
        # make sure the email address has the correct format
        if not utilities.blank(email) and not validation.valid_email(email):
            self.log("Invalid email address in site information: %s" %
                     email,
                     section=self.config_section,
                     option='email',
                     level=logging.ERROR)
            attributes_ok = False

        sponsor = self.opt_val("sponsor")
        if not utilities.blank(sponsor):
            attributes_ok &= self.check_sponsor(sponsor)

        self.log('SiteInformation.check_attributes completed')
        return attributes_ok

    def check_sponsor(self, sponsor):
        attributes_ok = True
        percentage = 0
        for vo in re.split(r'\s*,?\s*', sponsor):
            vo_split = vo.split(':')
            if len(vo_split) == 1:
                percentage += 100
            elif len(vo_split) == 2:
                vo_percentage = vo_split[1]
                try:
                    percentage += int(vo_percentage)
                except ValueError:
                    self.log("VO percentage (%s) in sponsor field (%s) not an integer"
                             % (vo_percentage, vo),
                             section=self.config_section,
                             option='sponsor',
                             level=logging.ERROR,
                             exception=True)
                    attributes_ok = False
            else:
                self.log("VO sponsor field is not formated correctly: %s" % vo,
                         section=self.config_section,
                         option='sponsor',
                         level=logging.ERROR)
                self.log("Sponsors should be given as sponsor:percentage "
                         "separated by a space or comma")
                attributes_ok = False

        if percentage != 100:
            self.log("VO percentages in sponsor field do not add up to 100, got %s"
                     % percentage,
                     section=self.config_section,
                     option='sponsor',
                     level=logging.ERROR)
            attributes_ok = False

        return attributes_ok

    def module_name(self):
        """Return a string with the name of the module"""
        return "SiteInformation"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True
