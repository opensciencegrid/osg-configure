""" Module to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
"""
import logging

from osg_configure.modules import configfile
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['GatewayConfiguration']


class GatewayConfiguration(BaseConfiguration):
  """ Class to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
  """

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(GatewayConfiguration, self).__init__(*args, **kwargs)
    self.log('GatewayConfiguration.__init__ started')
    self.options = {'gram_gateway_enabled':
                      configfile.Option(name='gram_gateway_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=True),
                    'htcondor_gateway_enabled':
                      configfile.Option(name='htcondor_gateway_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=False),
                    'job_envvar_path' :
                      configfile.Option(name='job_envvar_path',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=str,
                                        default_value='/bin:/usr/bin:/sbin:/usr/sbin',
                                        mapping='PATH')}
    self.gram_gateway_enabled = True
    self.htcondor_gateway_enabled = False
    self.config_section = "Gateway"

    # Some bits of configuration are skipped if enabled is False (which is the default in BaseConfiguration)
    self.enabled = True # XXX This needs to be True for mappings to work
    self.log('GatewayConfiguration.__init__ completed')

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or
    SafeConfigParser object given by configuration and write recognized settings
    to attributes dict
    """
    self.log('GatewayConfiguration.parseConfiguration started')
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('GatewayConfiguration.parseConfiguration completed')
      return

    self.getOptions(configuration)

    self.gram_gateway_enabled = self.options['gram_gateway_enabled'].value
    self.htcondor_gateway_enabled = self.options['htcondor_gateway_enabled'].value

    self.log('GatewayConfiguration.parseConfiguration completed')

  # Not overriding enabledServices -- only job manager modules need the gateways enabled
  #def enabledServices(self):

  # Not overriding checkAttributes -- all attributes are independent.
  #def checkAttributes(self, attributes):

  # Not overriding configure -- all configuration in other modules
  #def configure(self, attributes):

  def moduleName(self):
    """A string with the name of the module"""
    return self.config_section

  def separatelyConfigurable(self):
    """A boolean that indicates whether this module can be configured separately"""
    return False
