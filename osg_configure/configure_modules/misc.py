#!/usr/bin/python

""" Module to handle attributes and configuration for misc. sevices """

import os, sys, types

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['MiscConfiguration']


class MiscConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to miscellaneous services"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(MiscConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('MiscConfiguration.__init__ started')    
    self.__mappings = {'glexec_location': 'OSG_GLEXEC_LOCATION', 
                       'use_cert_updater': 'OSG_CERT_UPDATER',
                       'enable_webpage_creation': 'enable_webpage_creation',
                       'gums_host': 'gums_host',
                       'authorization_method' : 'authorization_method',
                       'enable_cleanup': 'enable_cleanup',
                       'cleanup_age_in_days': 'cleanup_age_in_days',
                       'cleanup_users_list': 'cleanup_users_list',
                       'cleanup_cron_time': 'cleanup_cron_time'}
    self.__booleans = ['use_cert_updater',
                       'enable_webpage_creation',
                       'enable_cleanup']
    self.__defaults = {'enable_webpage_creation' : 'N',
                       'enable_cleanup' : 'N',
                       'cleanup_age_in_days' : '14',
                       'cleanup_users_list' : '@vo-file',
                       'cleanup_cron_time' : '15 1 * * *'}
    self.__optional = ['glexec_location', 
                       'use_cert_updater',
                       'enable_webpage_creation',
                       'enable_cleanup',
                       'cleanup_age_in_days',
                       'cleanup_users_list',
                       'cleanup_cron_time']
    self.__option_types = {'cleanup_age_in_days' : types.IntType}
    self.__enabled = False
    self.__ce_configuration = False
    self.__defaults['user-vo-map-file'] = '/etc/osg/osg-user-vo-map.txt'
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

    if (self.attributes['authorization_method'] in ('prima', 'xacml') and
        ('gums_host' not in self.attributes or 
         utilities.blank(self.attributes['gums_host']))):
      if 'VDT_GUMS_HOST' in os.environ:
        mesg = "Using prima but getting gums host from VDT_GUMS_HOST, "\
               "a subsequent invocation without this variable set " \
               "will result in failure unless you set the gums_host " \
               "option in the Misc Services section"
        self.logger.warning(mesg)
        sys.stdout.write(mesg + "\n")
        sys.stdout.flush()        
        self.attributes[self.__mappings['gums_host']] = \
          os.environ['VDT_GUMS_HOST']
      else:
        mesg = "Using prima but getting gums host from your " \
               "prima-authz.conf, a subsequent invocation  may result " \
               "in failure if this file is changed unless you set the " \
               "gums_host option in the Misc Services section"
        self.logger.warning(mesg)
        sys.stderr.write(mesg + "\n")
        sys.stdout.flush()
        gums_host = utilities.get_gums_host()
        if gums_host is None:
          self.attributes[self.__mappings['gums_host']] = ''
        else:
          self.attributes[self.__mappings['gums_host']] = gums_host[0]
          
    if 'authorization_method' not in self.attributes:
      if utilities.using_prima():
        if utilities.using_xacml_protocol():
          self.attributes['authorization_method'] = 'xacml'
        else:
          self.attributes['authorization_method'] = 'prima'
      else:
        self.attributes['authorization_method'] = 'gridmap'
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
        ['gridmap', 'prima', 'xacml', 'local-gridmap']):
      self.logger.error("Setting for for authorization_method "+
                        "option in %s section "  % self.config_section +
                        "is not prima, xacml, gridmap, or local-gridmap")
      attributes_ok = False
      
    if self.attributes['authorization_method'] in ['prima', 'xacml']:
      if utilities.blank(self.attributes['gums_host']):
        self.logger.error("Gums host not given in gums_host in Misc Services or in " +
                          "VDT_GUMS_HOST variable")
        attributes_ok = False
            
      if not validation.valid_domain(self.attributes[self.__mappings['gums_host']]):
        self.logger.error("Gums host is not a valid domain")
        attributes_ok = False
   
      
    self.logger.debug('MiscConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('MiscConfiguration.configure started')    

    # disable configuration for now
    self.logger.debug('Not enabled')
    self.logger.debug('MiscConfiguration.configure completed')
    return True
    
    if not self.__enabled:
      self.logger.debug('Not enabled')
      self.logger.debug('MiscConfiguration.configure completed')
      return True
    
    if self.attributes[self.__mappings['use_cert_updater']] == 'Y':
      self.logger.debug('enabling ca-certs-updater')
      arguments = ['--server', 'y']    
      self.logger.info("Running configure_ca_cert_updater as: %s" % (" ".join(arguments)))
      if not utilities.configure_service('configure_ca_cert_updater', arguments):
        self.logger.error("Error while configuring ca certs updater")
        raise exceptions.ConfigureError("Error configuring ca certs updater")
      
      # run fetch-crl script
      if not utilities.fetch_crl():
        error_mesg = "Error while running fetch-crl script"
        self.logger.error(error_mesg)
        raise exceptions.ConfigureError(error_mesg) 
        

    if self.attributes['authorization_method'] == 'gridmap':
      self.__enable_gridmap()
      using_prima = False
    elif self.attributes['authorization_method'] == 'local_gridmap':
      self.__enable_local_gridmap()
      using_prima = False
    elif self.attributes['authorization_method'] == 'prima':
      using_prima = True
      self.__enable_prima()
    elif self.attributes['authorization_method'] == 'xacml':
      using_prima = True
      self.__enable_xacml()
    else:
      self.logger.critical("Unknown authorization method specified: %s" % \
                           self.attributes['authorization_method'])
      self.logger.critical("Check the authorization_method option in the " +
                           "Misc Services section")
      raise exceptions.ConfigureError("Invalid authorization_method option " +
                                      "in Misc Services")
      
    if (not utilities.blank(self.attributes['authorization_method']) and
        not validation.valid_user_vo_file(self.__defaults['user-vo-map-file'])):
      self.logger.debug("Trying to create osg-user-vo-map.txt file")
      result = utilities.create_map_file(using_prima) 
      (temp, invalid_lines) = validation.valid_user_vo_file(self.__defaults['user-vo-map-file'],
                                                           True)
      result = result and temp
      if not result:
        error_mesg = "Can't generate osg-user-vo-map.txt, manual intervention is needed"
        self.logger.critical(error_mesg)
        self.logger.critical("Invalid lines in user-vo-map.txt file:")
        self.logger.critical(invalid_lines)
        raise exceptions.ConfigureError(error_mesg)
      
      
    if self.attributes['enable_webpage_creation'] == 'Y':
      if not (sys.version_info[0] == 2 and sys.version_info[1] >= 3):
        message = "Your system python version is too old to enable webpage creation"
        message += "enable_webpage_creation in Misc Services will be ignored"
        self.logger.error(message)
      else:
        self.logger.debug("Enabling webpage creation")
        self.__enable_webpage_creation()


    # Call configure_vdt_cleanup (enabling or disabling as necessary)
    self.__enable_cleanup(self.attributes['enable_cleanup'])
      
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

  def __enable_prima(self):
    """
    Enable authorization services using old prima protocol
    """
    arguments = ['--gums-server', self.attributes['gums_host']]
    self.logger.info("Running configure_prima with: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_prima', arguments):
      self.logger.error("Error while configuring prima")
      raise exceptions.ConfigureError("Error configuring prima")

    arguments = ['--client', '--gums-host', self.attributes['gums_host']]
    os.environ['VDT_GUMS_HOST'] = self.attributes['gums_host']
    self.logger.info("Running configure_gums as: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_gums', arguments):
      self.logger.error("Error while configuring gums-host-cron")
      raise exceptions.ConfigureError("Error configuring gums-host-cron")



    if self.__ce_configuration:    
      arguments = ['--enable', '--gums-server', self.attributes['gums_host']]
      self.logger.info("Running configure_prima_gt4 with: %s" % (" ".join(arguments)))
      if not utilities.configure_service('configure_prima_gt4', arguments):
        self.logger.error("Error while configuring gt4 prima ")
        raise exceptions.ConfigureError("Error configuring gt4 prima")
  
  def __enable_xacml(self):
    """
    Enable authorization services using xacml protocol
    """
    arguments = ['--gums-server', self.attributes['gums_host'], '--xacml']
    self.logger.info("Running configure_prima with: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_prima', arguments):
      self.logger.error("Error while configuring prima")
      raise exceptions.ConfigureError("Error configuring prima")

    arguments = ['--client', '--gums-host', self.attributes['gums_host']]
    os.environ['VDT_GUMS_HOST'] = self.attributes['gums_host']
    self.logger.info("Running configure_gums as: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_gums', arguments):
      self.logger.error("Error while configuring gums-host-cron")
      raise exceptions.ConfigureError("Error configuring gums-host-cron")

    if self.__ce_configuration:
      arguments = ['--enable', '--gums-server', self.attributes['gums_host'], '--xacml']
      self.logger.info("Running configure_prima_gt4 with: %s" % (" ".join(arguments)))
      if not utilities.configure_service('configure_prima_gt4', arguments):
        self.logger.error("Error while configuring gt4 prima ")
        raise exceptions.ConfigureError("Error configuring gt4 prima")
  
  def __enable_gridmap(self):
    """
    Enable authorization using gridmap files
    """
    
    arguments = ['--server', 'y']
    self.logger.info("Running configure_edg_make-gridmap with %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_edg_make_gridmap', arguments):
      self.logger.error("Error while configuring edg_make_gridmap")
      raise exceptions.ConfigureError("Error configuring edg-mkgridmap service")
    
    arguments = ['--disable']
    self.logger.info("Running configure_prima_gt4 with: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_prima_gt4', arguments):
      self.logger.error("Error while configuring gt4 prima ")
      raise exceptions.ConfigureError("Error configuring gt4 prima")
      
  def __enable_local_gridmap(self):
    """
    Enable authorization using gridmap files
    """
    
    self.logger.debug("Disabling edg-mkgridmap service")
    if not utilities.disable_service('edg-mkgridmap'):
      self.logger.error("Error while enabling edg-mkgridmap")
      raise exceptions.ConfigureError("Error enabling edg-mkgridmap")
    
    self.logger.debug("Disabling gums host cron service")
    if not utilities.disable_service('gums-host-cron'):
      self.logger.error("Error while disabling gums-host-cron")
      raise exceptions.ConfigureError("Error disabling gums-host-cron")

    arguments = ['--disable']
    self.logger.info("Running configure_prima_gt4 with: %s" % (" ".join(arguments)))
    if not utilities.configure_service('configure_prima_gt4', arguments):
      self.logger.error("Error while configuring gt4 prima ")
      raise exceptions.ConfigureError("Error configuring gt4 prima")

  def __enable_webpage_creation(self):
    """
    Create webpage creation if certain conditions are met
    """
    
    setup_args = [os.path.join('/usr/bin/setup-osg-portal')]
    if not utilities.run_vdt_configure(setup_args):
      error_mesg = "Got error while running setup-osg-portal, exiting..."
      self.logger.error(error_mesg)
      raise exceptions.ConfigureError(error_mesg)
    return True


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
