""" Module to handle configuration of the CE Daemons (globus-gatekeeper and condor-ce)
"""
from osg_configure.modules import configfile
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['CEConfiguration']


class CEConfiguration(BaseConfiguration):
  """ Class to handle configuration of the CE Daemons (globus-gatekeeper and condor-ce)
  """

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(CEConfiguration, self).__init__(*args, **kwargs)
    self.log('CEConfiguration.__init__ started')
    self.options = {'gram_ce_enabled':
                      configfile.Option(name='gram_ce_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=True),
                    'htcondor_ce_enabled':
                      configfile.Option(name='htcondor_ce_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=False)}
    self.__gram_ce_enabled = True
    self.__htcondor_ce_enabled = False
    self.config_section = "CE"
    self.log('CEConfiguration.__init__ completed')

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or
    SafeConfigParser object given by configuration and write recognized settings
    to attributes dict
    """
    self.log('CEConfiguration.parseConfiguration started')
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('CEConfiguration.parseConfiguration completed')
      return

    self.getOptions(configuration)

    self.__gram_ce_enabled = self.options['gram_ce_enabled'].value
    self.__htcondor_ce_enabled = self.options['htcondor_ce_enabled'].value
    self.log('CEConfiguration.parseConfiguration completed')

  def enabledServices(self):
    """Return set of services for module to work"""
    services = set()
    if self.__gram_ce_enabled:
      services.add('globus-gatekeeper')
    if self.__htcondor_ce_enabled:
      services.add('condor-ce')
    return services

  # Not overriding checkAttributes -- all attributes are independent.
  #def checkAttributes(self, attributes):

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('CEConfiguration.configure started')
    # This is a placeholder. Right now there isn't any configuration to do:
    # all the configuration for globus-gatekeeper is done in the batch system-
    # specific modules, and the only config step for condor-ce should be done
    # manually since according to the installation guide it reduces the
    # security of the site.
    self.log('CEConfiguration.configure completed')
    return True

  def moduleName(self):
    """A string with the name of the module"""
    return "CE"

  def separatelyConfigurable(self):
    """A boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """A list of the sections from the configuration file that this module handles"""
    return [self.config_section]
