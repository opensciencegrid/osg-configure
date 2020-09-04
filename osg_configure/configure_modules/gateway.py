""" Module to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
"""

import logging

from osg_configure.modules import configfile
from osg_configure.modules import exceptions
from osg_configure.modules.baseconfiguration import BaseConfiguration

__all__ = ['GatewayConfiguration']


class GatewayConfiguration(BaseConfiguration):
    """ Class to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=W0142
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.log('GatewayConfiguration.__init__ started')
        self.options = {'htcondor_gateway_enabled':
                            configfile.Option(name='htcondor_gateway_enabled',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=bool,
                                              default_value=True),
                        'job_envvar_path':
                            configfile.Option(name='job_envvar_path',
                                              required=configfile.Option.OPTIONAL,
                                              opt_type=str,
                                              default_value='/bin:/usr/bin:/sbin:/usr/sbin',
                                              mapping='PATH')}
        self.htcondor_gateway_enabled = True
        self.config_section = "Gateway"

        # Some bits of configuration are skipped if enabled is False (which is the default in BaseConfiguration)
        self.enabled = True  # XXX This needs to be True for mappings to work
        self.log('GatewayConfiguration.__init__ completed')

    def parse_configuration(self, configuration):
        """
        Try to get configuration information from ConfigParser or
        SafeConfigParser object given by configuration and write recognized settings
        to attributes dict
        """
        self.log('GatewayConfiguration.parse_configuration started')
        if not configuration.has_section(self.config_section):
            self.enabled = False
            self.log("%s section not in config file" % self.config_section)
            self.log('GatewayConfiguration.parse_configuration completed')
            return

        self.get_options(configuration)

        self.htcondor_gateway_enabled = self.options['htcondor_gateway_enabled'].value

        self.log('GatewayConfiguration.parse_configuration completed')

    # Not overriding enabled_services -- only job manager modules need the gateways enabled
    # def enabled_services(self):

    # Not overriding check_attributes -- nothing to check
    # def check_attributes(self, attributes):

    # Not overriding configure -- all configuration in other modules
    # def configure(self, attributes):

    def module_name(self):
        """A string with the name of the module"""
        return self.config_section

    def separately_configurable(self):
        """A boolean that indicates whether this module can be configured separately"""
        return False
