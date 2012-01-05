#!/usr/bin/python

""" Module to handle attributes and configuration for misc. sevices """

import os, sys, types, re, logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['MiscConfiguration']

GSI_AUTHZ_LOCATION = "/etc/grid-security/gsi-authz.conf"
GUMS_CLIENT_LOCATION = "/etc/gums/gums-client.properties"
USER_VO_MAP_LOCATION = '/var/lib/osg/user-vo-map'

class MiscConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to miscellaneous services"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(MiscConfiguration, self).__init__(*args, **kwargs)    
    self.log('MiscConfiguration.__init__ started')
    self.options = {'glexec_location' : 
                      configfile.Option(name = 'glexec_location',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_GLEXEC_LOCATION'),
                    'gums_host' : 
                      configfile.Option(name = 'gums_host',
                                        required = configfile.Option.OPTIONAL),
                    'authorization_method' : 
                      configfile.Option(name = 'authorization_method',
                                        default_value = 'xacml'),
                    'enable_cleanup' : 
                      configfile.Option(name = 'enable_cleanup',
                                        required = configfile.Option.OPTIONAL,
                                        type = bool,
                                        default_value = False),
                    'cleanup_age_in_days' : 
                      configfile.Option(name = 'cleanup_age_in_days',
                                        required = configfile.Option.OPTIONAL,
                                        type = int,
                                        default_value = 14),
                    'cleanup_users_list' : 
                      configfile.Option(name = 'cleanup_users_list',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = '@vo-file'),
                    'cleanup_cron_time' : 
                      configfile.Option(name = 'cleanup_cron_time',
                                        required = configfile.Option.OPTIONAL,
                                        default_value = '15 1 * * *')}    
    self.__enabled = False
    self.config_section = "Misc Services"
    self.log('MiscConfiguration.__init__ completed')
    
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('MiscConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config files" % self.config_section)    
      self.log('MiscConfiguration.parseConfiguration completed')    
      return
    
    self.enabled = True
    
    for option in self.options.values():
      self.log("Getting value for %s" % option.name)
      configfile.get_option(configuration,
                            self.config_section, 
                            option)
      self.log("Got %s" % option.value)


              
    # check and warn if unknown options found    
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.options.keys(),
                                        configuration.defaults().keys())
    for option in temp:
      self.log("Found unknown option",
               option = option, 
               section = self.config_section,
               level = logging.WARNING)
    self.log('MiscConfiguration.parseConfiguration completed')    

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('MiscConfiguration.checkAttributes started')    
    attributes_ok = True
    
    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('MiscConfiguration.checkAttributes completed')
      return True
    
    if (self.options['authorization_method'].value not in \
        ['gridmap', 'xacml']):
      self.log("Setting is not xacml, or gridmap",
               option = 'authorization_method',
               section = self.config_section,
               level = logging.ERROR)
      attributes_ok = False
      
    if self.options['authorization_method'].value == 'xacml':
      if utilities.blank(self.options['gums_host'].value):
        self.log("Gums host not given",
                 section = self.config_section,
                 option = 'gums_host',
                 level = logging.ERROR)
        attributes_ok = False
            
      if not validation.valid_domain(self.options['gums_host'].value):
        self.log("Gums host not a valid domain name",
                 section = self.config_section,
                 option = 'gums_host',
                 level = logging.ERROR)
        attributes_ok = False
   
      
    self.log('MiscConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('MiscConfiguration.configure started')    

    if not self.enabled:
      self.log('Not enabled')
      self.log('MiscConfiguration.configure completed')
      return True
    
    # run fetch-crl script
    if not utilities.fetch_crl():
      self.log("Error while running fetch-crl script", level = logging.ERROR)
      raise exceptions.ConfigureError(error_mesg) 
        

    using_gums = False
    if self.options['authorization_method'].value == 'xacml':
      using_gums = True
      self.__enable_xacml()
    elif self.options['authorization_method'].value == 'gridmap':
      self.__disable_callout()
    else:
      self.log("Unknown authorization method: %s" % \
                           self.options['authorization_method'].value,
               option = 'authorization_method',
               section = self.config_section,
               level = logging.ERROR)
      raise exceptions.ConfigureError("Invalid authorization_method option " +
                                      "in Misc Services")
      
    if not validation.valid_user_vo_file(USER_VO_MAP_LOCATION):
      self.log("Trying to create user-vo-map file")
      result = utilities.create_map_file(using_gums) 
      (temp, invalid_lines) = validation.valid_user_vo_file(USER_VO_MAP_LOCATION,
                                                            True)
      result = result and temp
      if not result:
        self.log("Can't generate user-vo-map, manual intervention is needed",
                 level = logging.ERROR)
        self.log("Invalid lines in user-vo-map file:",
                 level = logging.ERROR)
        self.log(invalid_lines,
                 level = logging.ERROR)
        raise exceptions.ConfigureError(error_mesg)
      
      
    # Call configure_vdt_cleanup (enabling or disabling as necessary)
    # disable for now
    # self.__enable_cleanup(self.options['enable_cleanup'].value)
      
    self.log('MiscConfiguration.configure completed')    
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
  
  def __enable_xacml(self):
    """
    Enable authorization services using xacml protocol
    """
    
    self.log("Updating " + GSI_AUTHZ_LOCATION, level = logging.INFO)
    
    gsi_contents = "globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n"
    if not utilities.atomic_write(GSI_AUTHZ_LOCATION, gsi_contents):
      self.log("Error while writing to " + GSI_AUTHZ_LOCATION, 
               level = logging.ERROR)
      raise exceptions.ConfigureError(err_msg)
      
    self.log("Updating " + GUMS_CLIENT_LOCATION, level = logging.INFO)
    if not validation.valid_file(GUMS_CLIENT_LOCATION):
      gums_properties = "gums.location=https://%s:8443" % (self.options['gums_host'].value)
      gums_properties += "/gums/services/GUMSAdmin\n"
      gums_properties += "gums.authz=https://%s:8443" % (self.options['gums_host'].value) 
      gums_properties += "/gums/services/GUMSXACMLAuthorizationServicePort\n"
    else:
      gums_properties = open(GUMS_CLIENT_LOCATION).read()
      replacement = "gums.location=https://%s:8443" % (self.options['gums_host'].value)
      replacement += "/gums/services/GUMSAdmin\n"
      gums_properties  = re.sub("^gums.location=.*$", 
                                replacement, 
                                gums_properties, 
                                re.MULTILINE)
      replacement = "gums.authz=https://%s:8443" % (self.options['gums_host'].value)
      replacement += "/gums/services/GUMSXACMLAuthorizationServicePort\n"
      gums_properties  = re.sub("^gums.authz=.*$", 
                                replacement, 
                                gums_properties, 
                                re.MULTILINE)
    utilities.atomic_write(GUMS_CLIENT_LOCATION, gums_properties)
    
    
    

  
  def __disable_callout(self):
    """
    Enable authorization using gridmap files
    """    
    self.log("Updating " + GSI_AUTHZ_LOCATION, level = logging.INFO)
    gsi_contents = "#globus_mapping liblcas_lcmaps_gt4_mapping.so lcmaps_callout\n"
    if not utilities.atomic_write(GSI_AUTHZ_LOCATION, gsi_contents):
      self.log("Error while writing to " + GSI_AUTHZ_LOCATION, 
               level = logging.ERROR)
      raise exceptions.ConfigureError(err_msg)

    

  def __enable_cleanup(self, enable):
    """
    Enable the VDT cleanup script
    """

    # Form the arguments
    arguments = []
    
    if enable:
      arguments.append('--enable')

    arguments.append('--age')
    arguments.append(self.options['cleanup_age_in_days'].value)
    arguments.append('--users')
    arguments.append(self.options['cleanup_users_list'].value)
    arguments.append('--cron-time')
    arguments.append(self.options['cleanup_cron_time'].value)
      
    if not utilities.configure_service('configure_vdt_cleanup', arguments):
      self.log("Got error while running configure_vdt_cleanup, exiting...", 
               level = logging.ERROR)
      raise exceptions.ConfigureError(error_mesg)

    return True
