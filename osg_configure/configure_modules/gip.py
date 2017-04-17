"""Class for verifying gip information"""

import os
import re
import pwd
import logging

from osg_configure.modules import subcluster
from osg_configure.modules import exceptions
from osg_configure.modules.baseconfiguration import BaseConfiguration
from osg_configure.modules import utilities
from osg_configure.modules import validation

__all__ = ['GipConfiguration']

from osg_configure.modules.subcluster import REQUIRED, OPTIONAL, STRING, POSITIVE_INT, POSITIVE_FLOAT, LIST, BOOLEAN

OSG_ENTRIES = {
    "Site Information": ["host_name", "site_name", "sponsor", "site_policy",
                         "contact", "email", "city", "longitude", "latitude"],
    "Storage": ["app_dir", "data_dir", "worker_node_temp"],
}


class GipConfiguration(BaseConfiguration):
    """
    Class to handle attributes related to GIP.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(GipConfiguration, self).__init__(*args, **kwargs)
        self.log('GipConfiguration.__init__ started')
        self.config_section = "GIP"
        self.vo_dir = "VONAME"  # default to allowing substitution in vo_dir
        self._valid_batch_opt = ['pbs',
                                 'lsf',
                                 'condor',
                                 'sge',
                                 'slurm',
                                 'forwarding',
                                 'bosco']

        self.gip_user = None
        self.log('GipConfiguration.__init__ completed')

    _check_entry = staticmethod(subcluster.check_entry)

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or SafeConfigParser
        object given by configuration and write recognized settings to attributes
        dict
        """
        self.log('GipConfiguration.parse_configuration started')

        if not utilities.rpm_installed('gip'):
            self.log('GIP not installed, disabling GIP')
            self.log('GipConfiguration.parse_configuration completed')
            self.enabled = False
            return
        else:
            self.enabled = True

        # TODO Do we want to force the user to have a GIP section? Uncomment the following if not.
        # if not configuration.has_section(self.config_section):
        #   self.log("%s section not in config file" % self.config_section)
        #   self.log('GipConfiguration.parse_configuration completed')
        #   self.enabled = False
        #   return

        self.check_config(configuration)

        self._parse_configuration(configuration)

        self.log('GipConfiguration.parse_configuration completed')

    check_subclusters = staticmethod(subcluster.check_config)

    def _parse_configuration(self, configuration):
        """
        The meat of parse_configuration, runs after we've checked that GIP is
        enabled and we have the right RPMs installed.
        """
        # The following is to set the user that gip files need to belong to
        # This can be overridden by setting the 'user' option in the [GIP] section
        self.gip_user = 'tomcat'
        if configuration.has_option(self.config_section, 'batch'):
            batch_opt = configuration.get(self.config_section, 'batch').lower()
            if (not utilities.blank(batch_opt) and
                        batch_opt not in self._valid_batch_opt):
                msg = "The batch setting in %s must be a valid option " \
                      "(e.g. %s), %s was given" % (self.config_section,
                                                   ",".join(self._valid_batch_opt),
                                                   batch_opt)
                self.log(msg, level=logging.ERROR)
                raise exceptions.SettingError(msg)

        if utilities.ce_installed():
            self._parse_configuration_ce(configuration)

    def _parse_configuration_ce(self, configuration):
        # All CEs must advertise subclusters
        has_sc = self.check_subclusters(configuration)
        if not has_sc:
            try:
                self._check_entry(configuration, "GIP", "sc_number", REQUIRED,
                                  POSITIVE_INT)
            except (TypeError, ValueError, exceptions.SettingError):
                msg = "There is no `subcluster` section and the old-style subcluster" + \
                      "setup in GIP is not configured. " + \
                      " Please see the configuration documentation."
                raise exceptions.SettingError(msg)

    check_sc = staticmethod(subcluster.check_section)

    # pylint: disable-msg=W0613
    def configure(self, attributes):
        """
        Configure installation using attributes.
        """
        self.log('GipConfiguration.configure started')

        if not self.enabled:
            self.log('Not enabled, exiting...')
            self.log('GipConfiguration.configure completed')
            return

        self.log('GipConfiguration.configure completed')

    def module_name(self):
        """
        Return a string with the name of the module
        """
        return "GIP"

    def separately_configurable(self):
        """
        Return a boolean that indicates whether this module can be configured
        separately
        """
        return True
