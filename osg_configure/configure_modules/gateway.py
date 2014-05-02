""" Module to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
"""
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
                    'htcondor_ce_gateway_enabled':
                      configfile.Option(name='htcondor_ce_gateway_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=False)}
    self.__gram_gateway_enabled = True
    self.__htcondor_ce_gateway_enabled = False
    self.config_section = "Gateway"
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

    self.__gram_gateway_enabled = self.options['gram_gateway_enabled'].value
    self.__htcondor_ce_gateway_enabled = self.options['htcondor_ce_gateway_enabled'].value
    self.log('GatewayConfiguration.parseConfiguration completed')

  def enabledServices(self):
    """Return set of services for module to work"""
    services = set()
    if self.__gram_gateway_enabled:
      services.add('globus-gatekeeper')
    if self.__htcondor_ce_gateway_enabled:
      services.add('condor-ce')
    return services

  # Not overriding checkAttributes -- all attributes are independent.
  #def checkAttributes(self, attributes):

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('GatewayConfiguration.configure started')
    # This is a placeholder. All the configuration for globus-gatekeeper or
    # htcondor-ce is handled in the batch-system-specific modules, and the
    # configuration for rsv is handled in the rsv module.
    self.log('GatewayConfiguration.configure completed')
    return True

  def moduleName(self):
    """A string with the name of the module"""
    return self.config_section

  def separatelyConfigurable(self):
    """A boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """A list of the sections from the configuration file that this module handles"""
    return [self.config_section]
