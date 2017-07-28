""" Module to handle attributes related to the pbs jobmanager 
configuration """

import os
import logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.jobmanagerconfiguration import JobManagerConfiguration

__all__ = ['PBSConfiguration']


class PBSConfiguration(JobManagerConfiguration):
    """Class to handle attributes related to pbs job manager configuration"""

    PBS_CONFIG_FILE = '/etc/grid-services/available/jobmanager-pbs-seg'
    GRAM_CONFIG_FILE = '/etc/globus/globus-pbs.conf'

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super(PBSConfiguration, self).__init__(*args, **kwargs)
        self.log('PBSConfiguration.__init__ started')
        # dictionary to hold information about options
        self.options = {'pbs_location':
                            configfile.Option(name='pbs_location',
                                              default_value='/usr',
                                              mapping='OSG_PBS_LOCATION'),
                        'accounting_log_directory':
                            configfile.Option(name='accounting_log_directory',
                                              required=configfile.Option.OPTIONAL,
                                              default_value=''),
                        'pbs_server':
                            configfile.Option(name='pbs_server',
                                              required=configfile.Option.OPTIONAL,
                                              default_value='')}
        self.config_section = "PBS"
        self.pbs_bin_location = None
        self.log('PBSConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """Try to get configuration information from ConfigParser or SafeConfigParser object given
        by configuration and write recognized settings to attributes dict
        """
        super(PBSConfiguration, self).parse_configuration(configuration)

        self.log('PBSConfiguration.parse_configuration started')

        self.check_config(configuration)

        if not configuration.has_section(self.config_section):
            self.log('PBS section not found in config file')
            self.log('PBSConfiguration.parse_configuration completed')
            return

        if not self.set_status(configuration):
            self.log('PBSConfiguration.parse_configuration completed')
            return True

        self.get_options(configuration, ignore_options=['enabled', 'job_contact', 'util_contact', 'accept_limited',
                                                        'seg_enabled', 'log_directory'])

        # set OSG_JOB_MANAGER and OSG_JOB_MANAGER_HOME
        self.options['job_manager'] = configfile.Option(name='job_manager',
                                                        value='PBS',
                                                        mapping='OSG_JOB_MANAGER')
        self.options['home'] = configfile.Option(name='job_manager_home',
                                                 value=self.options['pbs_location'].value,
                                                 mapping='OSG_JOB_MANAGER_HOME')

        self.pbs_bin_location = os.path.join(self.options['pbs_location'].value, 'bin')

        self.log('PBSConfiguration.parse_configuration completed')

    # pylint: disable-msg=W0613
    def check_attributes(self, attributes):
        """Check attributes currently stored and make sure that they are consistent"""
        self.log('PBSConfiguration.check_attributes started')

        attributes_ok = True

        if not self.enabled:
            self.log('PBS not enabled, returning True')
            self.log('PBSConfiguration.check_attributes completed')
            return attributes_ok

        if self.ignored:
            self.log('Ignored, returning True')
            self.log('PBSConfiguration.check_attributes completed')
            return attributes_ok

        # make sure locations exist
        if not validation.valid_location(self.options['pbs_location'].value):
            attributes_ok = False
            self.log("Non-existent location given: %s" %
                     (self.options['pbs_location'].value),
                     option='pbs_location',
                     section=self.config_section,
                     level=logging.ERROR)

        if not validation.valid_directory(self.pbs_bin_location):
            attributes_ok = False
            self.log("Given pbs_location %r has no bin/ directory" % self.options['pbs_location'].value,
                     option='pbs_location',
                     section=self.config_section,
                     level=logging.ERROR)

        self.log('PBSConfiguration.check_attributes completed')
        return attributes_ok

    def configure(self, attributes):
        """Configure installation using attributes"""
        self.log('PBSConfiguration.configure started')

        if not self.enabled:
            self.log('PBS not enabled, returning True')
            self.log('PBSConfiguration.configure completed')
            return True

        if self.ignored:
            self.log("%s configuration ignored" % self.config_section,
                     level=logging.WARNING)
            self.log('PBSConfiguration.configure completed')
            return True

        if self.htcondor_gateway_enabled:
            self.write_binpaths_to_blah_config('pbs', self.pbs_bin_location)
            self.write_blah_disable_wn_proxy_renewal_to_blah_config()
            self.write_htcondor_ce_sentinel()

        self.log('PBSConfiguration.configure completed')
        return True

    def module_name(self):
        """Return a string with the name of the module"""
        return "PBS"

    def separately_configurable(self):
        """Return a boolean that indicates whether this module can be configured separately"""
        return True

    def enabled_services(self):
        """Return a list of  system services needed for module to work
        """

        if not self.enabled or self.ignored:
            return set()

        services = set(['globus-gridftp-server'])
        services.update(self.gateway_services())
        return services
