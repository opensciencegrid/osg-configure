#!/usr/bin/python

""" Module to handle attributes and configuration for misc. sevices """

import os, sys, types, re

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['MiscConfiguration']

GSI_AUTHZ_LOCATION = "/etc/grid-security/gsi-authz"
GUMS_CLIENT_LOCATION = "/etc/gums/gums-client.properties"

class MiscConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to miscellaneous services"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(MiscConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('MiscConfiguration.__init__ started')    
    self.__mappings = {'glexec_location': 'OSG_GLEXEC_LOCATION', 
                       'gums_host': 'gums_host',
                       'authorization_method' : 'authorization_method',
                       'enable_cleanup': 'enable_cleanup',
                       'cleanup_age_in_days': 'cleanup_age_in_days',
                       'cleanup_users_list': 'cleanup_users_list',
                       'cleanup_cron_time': 'cleanup_cron_time'}
    self.__booleans = ['enable_cleanup']
    self.__defaults = {'authorization_method': 'xacml',
                       'enable_cleanup' : 'N',
                       'cleanup_age_in_days' : '14',
                       'cleanup_users_list' : '@vo-file',
                       'cleanup_cron_time' : '15 1 * * *'}
    self.__optional = ['glexec_location', 
                       'enable_cleanup',
                       'cleanup_age_in_days',
                       'cleanup_users_list',
                       'cleanup_cron_time']
    self.__option_types = {'cleanup_age_in_days' : types.IntType}
    self.__enabled = False
    self.__ce_configuration = False
    self.__defaults['user-vo-map-file'] = '/var/lib/osg/osg-user-vo-map'
    self.config_section = "Misc Services"
    self.logger.debug('MiscConfiguration.__init__ completed')
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('MiscConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.__enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)    
      self.logger.debug('MiscConfiguration.parseConfiguration completed')    
      return
    
    self.__enabled = True
    self.__ce_configuration = utilities.ce_installed()
    
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

    # set defaults
    self.logger.debug("Setting defaults")
    for key in self.__defaults:
      if key == 'user-vo-map-file':
        # no attributes for this default
        continue
      if (self.__mappings[key] not in self.attributes or
          utilities.blank(self.attributes[self.__mappings[key]])):
        self.logger.debug("Setting default for %s" % key)
        self.attributes[self.__mappings[key]] = self.__defaults[key]                      

    if (self.attributes['authorization_method'] in ('xacml') and
        ('gums_host' not in self.attributes or 
         utilities.blank(self.attributes['gums_host']))):
      mesg = "You must specify fill in gums_host in the Misc section if you "
      mesg += "set the authorization_method to xacml"
      self.logger.error(mesg)
      raise exceptions.ConfigureError(mesg)
              
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())

    for option in temp:
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('MiscConfiguration.parseConfiguration completed')    

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('MiscConfiguration.checkAttributes started')    
    attributes_ok = True
    
    if not self.__enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('MiscConfiguration.checkAttributes completed')
      return True
    
    if (self.attributes[self.__mappings['authorization_method']] not in \
        ['gridmap', 'xacml', 'local-gridmap']):
      self.logger.error("Setting for for authorization_method "+
                        "option in %s section "  % self.config_section +
                        "is not xacml, gridmap, or local-gridmap")
      attributes_ok = False
      
    if self.attributes['authorization_method'] in ['xacml']:
      if utilities.blank(self.attributes['gums_host']):
        self.logger.error("Gums host not given in gums_host in Misc Services section")
        attributes_ok = False
            
      if not validation.valid_domain(self.attributes[self.__mappings['gums_host']]):
        self.logger.error("Gums host is not a valid domain")
        attributes_ok = False
   
      
    self.logger.debug('MiscConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('MiscConfiguration.configure started')    

    if not self.__enabled:
      self.logger.debug('Not enabled')
      self.logger.debug('MiscConfiguration.configure completed')
      return True
    
    # run fetch-crl script
    if not utilities.fetch_crl():
      error_mesg = "Error while running fetch-crl script"
      self.logger.error(error_mesg)
      raise exceptions.ConfigureError(error_mesg) 
        

    using_gums = False
    if self.attributes['authorization_method'] == 'xacml':
      using_gums = True
      self.__enable_xacml()
    elif self.attributes['authorization_method'] == 'local_gridmap':
      self.__enable_local_gridmap()
    else:
      self.logger.critical("Unknown authorization method specified: %s" % \
                           self.attributes['authorization_method'])
      self.logger.critical("Check the authorization_method option in the " +
                           "Misc Services section")
      raise exceptions.ConfigureError("Invalid authorization_method option " +
                                      "in Misc Services")
      
    if not validation.valid_user_vo_file(self.__defaults['user-vo-map-file']):
      self.logger.debug("Trying to create osg-user-vo-map file")
      result = utilities.create_map_file(using_gums) 
      (temp, invalid_lines) = validation.valid_user_vo_file(self.__defaults['user-vo-map-file'],
                                                           True)
      result = result and temp
      if not result:
        error_mesg = "Can't generate osg-user-vo-map, manual intervention is needed"
        self.logger.critical(error_mesg)
        self.logger.critical("Invalid lines in user-vo-map file:")
        self.logger.critical(invalid_lines)
        raise exceptions.ConfigureError(error_mesg)
      
      
    # Call configure_vdt_cleanup (enabling or disabling as necessary)
    # disable for now
    # self.__enable_cleanup(self.attributes['enable_cleanup'])
      
    self.logger.debug('MiscConfiguration.configure completed')    
    return True

  def moduleName(self):
    """Return a string with the name of the module"""
    return "Misc"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
  
  def getAttributes(self):
    """Return settings"""
    temp = self.attributes.copy()

    # swk - Changing this code to only delete variables if they are present in the dict.
    # I don't know why they are deleted though - there was no comment in the original code.
    for var in (['gums_host', 'authorization_method', 'enable_webpage_creation']):
      if var in temp:
        del temp[var]

    return temp

  def __enable_xacml(self):
    """
    Enable authorization services using xacml protocol
    """
    
    self.logger.info("Updating " + GSI_AUTHZ_LOCATION)
    
    gsi_contents = "globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout"
    if not utilities.atomic_write(GSI_AUTHZ_LOCATION, gsi_contents):
      err_msg = "Error while writing to " + GSI_AUTHZ_LOCATION
      self.logger.error(err_msg)
      raise exceptions.ConfigureError(err_msg)
      
    self.logger.info("Updating " + GUMS_CLIENT_LOCATION)
    gums_properties = open(GUMS_CLIENT_LOCATION).read()
    replacement = "gums.location=https://%s:8443/gums/services/GUMSAdmin" % (self.attributes['gums_host'])
    gums_properties  = re.sub("^gums.location=.*$", 
                              replacement, 
                              gums_properties, 
                              re.MULTILINE)
    replacement = "gums.authz=https://%s:8443/gums/services/GUMSXACMLAuthorizationServicePort" % (self.attributes['gums_host'])
    gums_properties  = re.sub("^gums.authz=.*$", 
                              replacement, 
                              gums_properties, 
                              re.MULTILINE)
    utilities.atomic_write(GUMS_CLIENT_LOCATION, gums_properties)
    
    
    

  
  def __enable_local_gridmap(self):
    """
    Enable authorization using gridmap files
    """
    
    self.logger.info("Updating /etc/grid-security/gsi-authz")
    gsi_contents = "#globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout"
    utilities.atomic_write('/etc/grid-security/gsi-authz', gsi_contents)

    

  def __enable_cleanup(self, enable):
    """
    Enable the VDT cleanup script
    """

    # Form the arguments
    arguments = []
    
    if enable == 'Y':
      arguments.append('--enable')

    arguments.append('--age')
    arguments.append(self.attributes['cleanup_age_in_days'])
    arguments.append('--users')
    arguments.append(self.attributes['cleanup_users_list'])
    arguments.append('--cron-time')
    arguments.append(self.attributes['cleanup_cron_time'])
      
    if not utilities.configure_service('configure_vdt_cleanup', arguments):
      error_mesg = "Got error while running configure_vdt_cleanup, exiting..."
      self.logger.error(error_mesg)
      raise exceptions.ConfigureError(error_mesg)

    return True
