#!/usr/bin/python

""" Module to handle attributes related to the storage """

import os, shutil, stat

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['StorageConfiguration']


class StorageConfiguration(BaseConfiguration):
  """Class to handle attributes related to storage"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(StorageConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('StorageConfiguration.__init__ started')
    self.__mappings = {'se_available': 'OSG_STORAGE_ELEMENT', 
                       'default_se': 'OSG_DEFAULT_SE',
                       'grid_dir': 'OSG_GRID',
                       'app_dir': 'OSG_APP',
                       'data_dir': 'OSG_DATA',
                       'worker_node_temp': 'OSG_WN_TMP',
                       'site_read': 'OSG_SITE_READ',
                       'site_write': 'OSG_SITE_WRITE'}
    self.__optional = ['default_se', 
                       'grid_dir',
                       'site_read',
                       'site_write']
    self.config_section = "Storage"
    self.logger.debug('StorageConfiguration.__init__ completed')
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('StorageConfiguration.parseAttributes started')    

    self.checkConfig(configuration)

    if (not configuration.has_section(self.config_section) or
        not configfile.ce_config(configuration)):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)    
      self.logger.debug('StorageConfiguration.parseAttributes completed')    
      return
    else:
      self.enabled = True
      
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)        
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting, 
                                   self.__optional)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)


    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))   
    self.logger.debug('StorageConfiguration.parseAttributes completed')    
       
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('StorageConfiguration.checkAttributes started')    
    attributes_ok = True
    
    if not self.enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('StorageConfiguration.checkAttributes completed')    
      return attributes_ok

    # make sure locations exist
    if not self.__check_app_dir(self.attributes[self.__mappings['app_dir']]):
      self.logger.warn("app_dir does not meet requirements: %s" % \
                        self.attributes[self.__mappings['app_dir']])
      self.logger.warn("The app_dir directory should exist and have permissions "
                       "of 1777 or 777 on OSG installations.")
      attributes_ok = False
    
    self.logger.debug('StorageConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure storage locations for ce usage"""

    self.logger.debug("StorageConfiguration.configure started")
    
    if not self.enabled:
      self.logger.debug('Not enabled, exiting')
      self.logger.debug("StorageConfiguration.configure completed")
      return True
      
    status = True
    grid3_location = os.path.join(self.attributes[self.__mappings['app_dir']],
                                  'etc',
                                  'grid3-locations.txt')
    if not validation.valid_file(grid3_location):
      grid3_source = os.path.join('etc',
                                  'osg',
                                  'grid3-locations.txt')
      if not validation.valid_file(grid3_source):
        status = False
        self.logger.warning("Can't get grid3-location file at %s" % (grid3_source))
        self.logger.warning("You will need to manually create one at %s" %  (grid3_location))
        return status
      
      try:
        shutil.copyfile(grid3_source, grid3_location)        
      except IOError:
        status = False
        self.logger.warning("Can't copy grid3-location file from %s to %s" % (grid3_source, 
                                                                              grid3_location))
      try:
        if status is not False:
          os.chmod(grid3_location, 0666)        
      except IOError:
        status = False
        self.logger.warning("Can't set permissions on grid3-location file at %s" % \
                            (grid3_location))
  
    self.logger.debug("StorageConfiguration.configure completed")    
    return status

  def moduleName(self):
    """Return a string with the name of the module"""
    return "Storage"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
  
  def __check_app_dir(self, app_dir):
    """"
    Checks to make sure that the OSG_APP directory exists and the VO directories have 
    the proper permissions.  Returns True if everything is okay, False otherwise. 
    
    APP_DIR must exist and have a etc directory with 1777 permissions for success.
    """
    try:
      if not validation.valid_location(app_dir) or not os.path.isdir(app_dir):
        self.logger.error("OSG_APP directory not present: %s" % app_dir)
        return False
      
      etc_dir = os.path.join(app_dir, "etc")
      if not validation.valid_location(etc_dir) or not os.path.isdir(etc_dir):
        self.logger.error("$OSG_APP/etc directory not present: %s" % etc_dir)
        return False
    
      permissions = stat.S_IMODE(os.stat(etc_dir).st_mode)
      # check to make sure permissions are 777, 1777 2777 775 1775 2775 755 1755 2755
      all_rwx = stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO
      og_rwx = stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH
      o_rwx = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP 
      o_rwx |= stat.S_IROTH | stat.S_IXOTH
      allowed  = [all_rwx | stat.S_ISVTX, # 1777
                  all_rwx, # 777
                  all_rwx | stat.S_ISGID, # 2777
                  og_rwx, # 775
                  og_rwx | stat.S_ISVTX, # 2775
                  og_rwx | stat.S_ISGID, # 2775
                  o_rwx, # 755
                  o_rwx | stat.S_ISVTX, # 1755
                  o_rwx | stat.S_ISGID] # 2755 
      if permissions not in allowed:
        self.logger.warning("Permissions on $OSG_APP/etc should be 777, 1777, " \
                            "2777, 775, 1775, 2775, 755, 1755, 2755 " \
                            "for sites: %s" % etc_dir)
    # pylint: disable-msg=W0703      
    except Exception, ex:
      self.logger.error("Can't check $OSG_APP, got exception: %s", ex)
      return False
    
    return True
