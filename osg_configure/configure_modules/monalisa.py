""" Module to handle attributes related to the monalisa configuration
and setup """

import logging

from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['MonalisaConfiguration']

def convert_values(value):
  """
  Convert values to a string representation that can go into 
  osg-attributes.conf
  
  arguments:
  value - item to convert
  """
  
  if type(value) == bool:
    if value:
      return 'Y'
    else:
      return 'N'
  return str(value)


class MonalisaConfiguration(BaseConfiguration):
  """Class to handle attributes related to MonaLisa configuration and setup"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(MonalisaConfiguration, self).__init__(*args, **kwargs)    
    self.log('MonalisaConfiguration.__init__ started')
    self.options = {'enabled' : 
                      configfile.Option(name = 'enabled',
                                        default_value = False,
                                        opt_type = bool,
                                        mapping = 'OSG_MONALISA_SERVICE'),
                    'use_vo_modules' : 
                      configfile.Option(name = 'use_vo_modules',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = True,
                                        opt_type = bool,
                                        mapping = 'OSG_VO_MODULES'),
                    'ganglia_support' : 
                      configfile.Option(name = 'ganglia_support',
                                        opt_type = bool,
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_GANGLIA_SUPPORT'),
                    'ganglia_host' : 
                      configfile.Option(name = 'ganglia_host',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_GANGLIA_HOST'),
                    'ganglia_port' : 
                      configfile.Option(name = 'ganglia_port',
                                        default_value = 8649,
                                        opt_type = int,
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_GANGLIA_PORT'),
                    'monitor_group' : 
                      configfile.Option(name = 'monitor_group',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL),
                    'user' : 
                      configfile.Option(name = 'user',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = 'daemon'),
                    'auto_update' : 
                      configfile.Option(name = 'auto_update',
                                        required = configfile.Option.OPTIONAL,
                                        opt_type = bool,
                                        default_value = False)}
    self.config_section = "MonaLisa"
    self.log('MonalisaConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('MonalisaConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.log("%s section not in config file" % self.config_section)
      self.log('MonalisaConfiguration.parseConfiguration completed')
      self.enabled = False
      return
    
    if not self.setStatus(configuration):
      self.options['enabled'].value = False
      self.log('MonalisaConfiguration.parseConfiguration completed')
      return True

    self.enabled = True
    self.getOptions(configuration)
    self.log('MonalisaConfiguration.parseConfiguration completed')
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('MonalisaConfiguration.checkAttributes started')
    attributes_ok = True
    
    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('MonalisaConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.log('Ignored, returning True')
      self.log('MonalisaConfiguration.checkAttributes completed')
      return attributes_ok

    if self.options['ganglia_support'].value:
      if not validation.valid_domain(self.options['ganglia_host'].value):
        self.log("Setting is not a valid host/domain",
                 option = 'ganglia_host',
                 section = self.config_section,
                 level = logging.ERROR)
        attributes_ok = False
                    
    self.log('MonalisaConfiguration.checkAttributes completed')
    return attributes_ok 
  
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('MonalisaConfiguration.configure started')
    
    # disable configuration for now
    self.log('Not enabled, exiting.')
    self.log('MonalisaConfiguration.configure completed')
    return True
    
#    if not self.enabled:
#      self.log('Not enabled, exiting.')
#      self.log('MonalisaConfiguration.configure completed')
#      return True

#    if self.ignored:
#      self.log("%s configuration ignored" % self.config_section)
#      return True
#
#    arguments = ['--server', 'y']
#  
#    if self.options['ganglia_support']:
#      arguments.append('--ganglia-used')
#      arguments.append('y')
#      arguments.append("--ganglia-host")
#      arguments.append(self.options['ganglia_host'])
#      arguments.append("--ganglia-port") 
#      arguments.append(self.options['ganglia_port'])
#    else:
#      arguments.append('--ganglia-used')
#      arguments.append('n')
#    arguments.append('--farm')
#    arguments.append(attributes['OSG_SITE_NAME'])
#    arguments.append('--monitor-group')
#    if self.options['monitor_group'].value is None:
#      arguments.append(attributes['OSG_GROUP'])
#    else:
#      arguments.append(self.options['monitor_group'])
#    arguments.append('--contact-name')
#    arguments.append(attributes['OSG_CONTACT_NAME'])
#    arguments.append('--contact-email')
#    arguments.append(attributes['OSG_CONTACT_EMAIL'])
#    arguments.append('--city')
#    arguments.append(attributes['OSG_SITE_CITY'])
#    arguments.append('--country')
#    arguments.append(attributes['OSG_SITE_COUNTRY'])
#    arguments.append('--latitude')
#    arguments.append(attributes['OSG_SITE_LATITUDE'])
#    arguments.append('--longitude')
#    arguments.append(attributes['OSG_SITE_LONGITUDE'])
#    arguments.append('--vo-modules')
#    arguments.append(self.options['use_vo_modules'].value)
#    arguments.append('--vdt-install')
#    arguments.append('/usr')
#    if attributes['OSG_JOB_MANAGER'].upper() == 'PBS':
#      arguments.append('--pbs-location')
#      arguments.append(attributes['OSG_PBS_LOCATION'])
#    elif attributes['OSG_JOB_MANAGER'].upper() == 'LSF':
#      arguments.append('--lsf-location')
#      arguments.append(attributes['OSG_LSF_LOCATION'])
#    elif attributes['OSG_JOB_MANAGER'].upper() == 'SGE':
#      arguments.append('--sge-location')
#      arguments.append(attributes['OSG_SGE_LOCATION'])
#    elif attributes['OSG_JOB_MANAGER'].upper() == 'CONDOR':
#      arguments.append('--condor-location')
#      arguments.append(attributes['OSG_CONDOR_LOCATION'])
#      arguments.append('--condor-config')
#      arguments.append(attributes['OSG_CONDOR_CONFIG'])
#    
#      
#    arguments.append('--user')
#    arguments.append(self.options['user'])
#    arguments.append('--auto-update')
#    if self.options['auto_update']:
#      arguments.append('y')
#    else:    
#      arguments.append('n')    
#    arguments.append('--noprompt')
#    self.log("Running configure_monalisa with: %s" % (" ".join(arguments)))
#    if not utilities.configure_service('configure_monalisa', arguments):
#      self.log("Error while configuring monalisa", level = logging.ERROR)
#      raise exceptions.ConfigureError("Error configuring MonaLisa")
#    self.log('MonalisaConfiguration.configure completed')
#    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "MonaLisa"
  
  def separatelyConfigurable(self):
    """
    Return a boolean that indicates whether this module can be configured separately
    """
    return True
  
  def parseSections(self):
    """
    Returns the sections from the configuration file that this module handles
    """
    return [self.config_section]

  def getAttributes(self, converter = str):
    """
    Get attributes for the osg attributes file using the dict in self.options

    Returns a dictionary of ATTRIBUTE => value mappings
    
    Need to override parent class method since OSG_MONALISA_SERVICE is bool 
    and needs to be mapped to Y/N
    """

    self.log("%s.getAttributes started" % self.__class__)
    attributes = BaseConfiguration.getAttributes(self, converter = convert_values)
    if attributes == {}:
      attributes['OSG_MONALISA_SERVICE'] = 'N'
    self.log("%s.getAttributes completed" % self.__class__)
    return attributes


