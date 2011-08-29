#!/usr/bin/python

""" Module to handle attributes related to the monalisa configuration
and setup """

from configure_osg.modules import exceptions
from configure_osg.modules import utilities
from configure_osg.modules import configfile
from configure_osg.modules import validation
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['MonalisaConfiguration']


class MonalisaConfiguration(BaseConfiguration):
  """Class to handle attributes related to MonaLisa configuration and setup"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(MonalisaConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('MonalisaConfiguration.__init__ started')
    self.__mappings = {'enabled': 'OSG_MONALISA_SERVICE', 
                       'use_vo_modules': 'OSG_VO_MODULES',
                       'ganglia_support': 'OSG_GANGLIA_SUPPORT',
                       'ganglia_host': 'OSG_GANGLIA_HOST',
                       'ganglia_port': 'OSG_GANGLIA_PORT',
                       'monitor_group': 'monitor_group',
                       'user': 'user',
                       'auto_update': 'auto_update'}
    self.__defaults = {'use_vo_modules': 'Y',
                       'ganglia_port': '8649',
                       'auto_update': 'N',
                       'user': 'daemon',
                       'monitor_group': None}
    self.__optional = ['use_vo_modules',
                       'ganglia_support',
                       'ganglia_host',
                       'ganglia_port',
                       'monitor_group',
                       'user',
                       'auto_update']
    self.__booleans = ['enabled',
                       'use_vo_modules',
                       'ganglia_support',
                       'auto_update']
    self.config_section = "MonaLisa"
    self.logger.debug('MonalisaConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('MonalisaConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('MonalisaConfiguration.parseConfiguration completed')
      self.enabled = False
      return
    
    if not self.setStatus(configuration):
      self.attributes[self.__mappings['enabled']] = 'N'
      self.logger.debug('MonalisaConfiguration.parseConfiguration completed')
      return True

    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional, 
                                   self.__defaults)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)


    # set boolean options
    self.logger.debug("Setting boolean options")    
    for option in self.__booleans:
      if not configuration.has_option(self.config_section, option):
        continue
      if (option in self.__defaults and 
          utilities.blank(configuration.get(self.config_section,
                                            option))):
        continue
      if not validation.valid_boolean(configuration, 
                                     self.config_section, 
                                     option):
        mesg = "In %s section, %s needs to be set to True or False" \
                          % (self.config_section, option)
        self.logger.error(mesg)
        raise exceptions.ConfigureError(mesg)
        
      if configuration.getboolean(self.config_section, option):
        self.attributes[self.__mappings[option]] = 'Y'
      else:
        self.attributes[self.__mappings[option]] = 'N'
        
    
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('MonalisaConfiguration.parseConfiguration completed')
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('MonalisaConfiguration.checkAttributes started')
    attributes_ok = True
    
    if not self.enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('MonalisaConfiguration.checkAttributes completed')
      return attributes_ok
    
    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('MonalisaConfiguration.checkAttributes completed')
      return attributes_ok

    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        self.logger.error("Missing setting for %s in %s section" % 
                          (setting, self.config_section))
        attributes_ok = False

    if self.attributes[self.__mappings['enabled']] not in ('Y','N'):
      self.logger.error("enabled setting in MonaLisa section must be " + 
                        "either True or False")
      attributes_ok = False
      
    if self.attributes[self.__mappings['use_vo_modules']] not in ('Y','N'):
      self.logger.error("use_vo_modules setting in MonaLisa section must " +
                        "be either True or False")
      attributes_ok = False

    if self.attributes[self.__mappings['ganglia_support']] not in ('Y','N'):
      self.logger.error("ganglia_support setting in MonaLisa section must " + 
                        "be either True or False")
      attributes_ok = False
      
    if self.attributes[self.__mappings['ganglia_support']] == 'Y':
      if not validation.valid_domain(self.attributes[self.__mappings['ganglia_host']]):
        self.logger.error("ganglia_host setting is not a valid host/domain")
        attributes_ok = False

      # make sure the port is an integer
      try:
        int(self.attributes[self.__mappings['ganglia_port']])
      except ValueError:
        self.logger.error("ganglia_port setting must be an integer in MonaLisa section")
        attributes_ok = False
                    
    self.logger.debug('MonalisaConfiguration.checkAttributes completed')
    return attributes_ok 
  
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('MonalisaConfiguration.configure started')
    
    # disable configuration for now
    self.logger.debug('Not enabled, exiting.')
    self.logger.debug('MonalisaConfiguration.configure completed')
    return True
    
    if not self.enabled:
      self.logger.debug('Not enabled, exiting.')
      self.logger.debug('MonalisaConfiguration.configure completed')
      return True

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      return True

    arguments = ['--server', 'y']
  
    if self.attributes['OSG_GANGLIA_SUPPORT'] == 'Y':
      arguments.append('--ganglia-used')
      arguments.append('y')
      arguments.append("--ganglia-host")
      arguments.append(self.attributes['OSG_GANGLIA_HOST'])
      arguments.append("--ganglia-port") 
      arguments.append(self.attributes['OSG_GANGLIA_PORT'])
    else:
      arguments.append('--ganglia-used')
      arguments.append('n')
    arguments.append('--farm')
    arguments.append(attributes['OSG_SITE_NAME'])
    arguments.append('--monitor-group')
    if self.attributes['monitor_group'] is None:
      arguments.append(attributes['OSG_GROUP'])
    else:
      arguments.append(self.attributes['monitor_group'])
    arguments.append('--contact-name')
    arguments.append(attributes['OSG_CONTACT_NAME'])
    arguments.append('--contact-email')
    arguments.append(attributes['OSG_CONTACT_EMAIL'])
    arguments.append('--city')
    arguments.append(attributes['OSG_SITE_CITY'])
    arguments.append('--country')
    arguments.append(attributes['OSG_SITE_COUNTRY'])
    arguments.append('--latitude')
    arguments.append(attributes['OSG_SITE_LATITUDE'])
    arguments.append('--longitude')
    arguments.append(attributes['OSG_SITE_LONGITUDE'])
    arguments.append('--vo-modules')
    arguments.append(self.attributes[self.__mappings['use_vo_modules']])
    arguments.append('--vdt-install')
    arguments.append(utilities.get_vdt_location())
    if attributes['OSG_JOB_MANAGER'].upper() == 'PBS':
      arguments.append('--pbs-location')
      arguments.append(attributes['OSG_PBS_LOCATION'])
    elif attributes['OSG_JOB_MANAGER'].upper() == 'LSF':
      arguments.append('--lsf-location')
      arguments.append(attributes['OSG_LSF_LOCATION'])
    elif attributes['OSG_JOB_MANAGER'].upper() == 'SGE':
      arguments.append('--sge-location')
      arguments.append(attributes['OSG_SGE_LOCATION'])
    elif attributes['OSG_JOB_MANAGER'].upper() == 'CONDOR':
      arguments.append('--condor-location')
      arguments.append(attributes['OSG_CONDOR_LOCATION'])
      arguments.append('--condor-config')
      arguments.append(attributes['OSG_CONDOR_CONFIG'])
    
      
    arguments.append('--user')
    arguments.append(self.attributes['user'])
    arguments.append('--auto-update')
    if self.attributes['auto_update']:
      arguments.append('y')
    else:    
      arguments.append('n')    
    arguments.append('--noprompt')
    self.logger.info("Running configure_monalisa with: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_monalisa', arguments):
      self.logger.error("Error while configuring monalisa")
      raise exceptions.ConfigureError("Error configuring MonaLisa")
    self.logger.debug('MonalisaConfiguration.configure completed')
    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "MonaLisa"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]

