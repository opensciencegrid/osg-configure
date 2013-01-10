""" Module to handle attributes related to the storage """

import os
import shutil
import stat
import logging

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
    self.log('StorageConfiguration.__init__ started')
    self.options = {'se_available' : 
                      configfile.Option(name = 'se_available',
                                        opt_type = bool,
                                        default_value = False,
                                        mapping = 'OSG_STORAGE_ELEMENT'),
                    'default_se' : 
                      configfile.Option(name = 'default_se',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_DEFAULT_SE'),
                    'grid_dir' : 
                      configfile.Option(name = 'grid_dir',
                                        default_value = '/etc/osg/wn-client',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_GRID'),
                    'app_dir' : 
                      configfile.Option(name = 'app_dir',
                                        mapping = 'OSG_APP'),
                    'data_dir' : 
                      configfile.Option(name = 'data_dir',
                                        default_value = 'UNAVAILABLE',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_DATA'),
                    'worker_node_temp' : 
                      configfile.Option(name = 'worker_node_temp',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_WN_TMP'),
                    'site_read' : 
                      configfile.Option(name = 'site_read',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_SITE_READ'),
                    'site_write' : 
                      configfile.Option(name = 'site_write',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_SITE_WRITE')}
    self.config_section = "Storage"
    self.log('StorageConfiguration.__init__ completed')
      
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser 
    object given by configuration and write recognized settings to attributes 
    dict
    """
    self.log('StorageConfiguration.parseAttributes started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('StorageConfiguration.parseAttributes completed')    
      return
    if not utilities.ce_installed():
      self.enabled = False
      self.log("osg-ce rpm not installed, skipping ce specific module")
      self.log('StorageConfiguration.parseAttributes completed')    
      return
    else:
      self.enabled = True
      
    self.getOptions(configuration)
    self.log('StorageConfiguration.parseAttributes completed')    
       
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('StorageConfiguration.checkAttributes started')    
    attributes_ok = True
    
    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('StorageConfiguration.checkAttributes completed')    
      return attributes_ok

    # make sure locations exist
    if not self.__check_app_dir(self.options['app_dir'].value):
      self.log("The app_dir and app_dir/etc directories should exist and " +
               "have permissions of 1777 or 777 on OSG installations.",
               section = self.config_section,
               option = 'app_dir',
               level = logging.ERROR)
      attributes_ok = False

    # WN_TMP may be blank if the job manager dynamically generates it but 
    # warni just in case
    if  utilities.blank(self.options['worker_node_temp'].value):
      self.log("worker_node_temp is blank, this is okay if you've set your " +
               "job manager to set this dynamically, otherwise jobs may " +
               "fail to run",
               section = self.config_section,
               option = 'worker_node_temp',
               level = logging.WARNING)
    self.log('StorageConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure storage locations for ce usage"""

    self.log("StorageConfiguration.configure started")
    
    if not self.enabled:
      self.log('Not enabled, exiting')
      self.log("StorageConfiguration.configure completed")
      return True
      
    status = True
    grid3_location = os.path.join(self.options['app_dir'].value,
                                  'etc',
                                  'grid3-locations.txt')
    if not validation.valid_file(grid3_location):
      grid3_source = os.path.join('/',
                                  'etc',
                                  'osg',
                                  'grid3-locations.txt')
      if not validation.valid_file(grid3_source):
        self.log("Can't get grid3-location file at %s" % (grid3_source), 
                 level = logging.WARNING)
        self.log("You will need to manually create one at %s" %  (grid3_location),
                 level = logging.WARNING)
      
      try:
        shutil.copyfile(grid3_source, grid3_location)        
      except IOError:
        self.log("Can't copy grid3-location file from %s to %s" % (grid3_source, 
                                                                   grid3_location),
                 level = logging.WARNING)
      try:
        if validation.valid_file(grid3_location):
          os.chmod(grid3_location, 0666)        
      except IOError:
        self.log("Can't set permissions on grid3-location file at %s" % \
                            (grid3_location),
                 level = logging.WARNING)
  
    self.log("StorageConfiguration.configure completed")    
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
        self.log("Directory not present: %s" % app_dir,
                 section = self.config_section,
                 option = 'app_dir',
                 level = logging.ERROR)
        return False
      
      etc_dir = os.path.join(app_dir, "etc")
      if not validation.valid_location(etc_dir) or not os.path.isdir(etc_dir):
        self.log("$OSG_APP/etc directory not present: %s" % etc_dir,
                 section = self.config_section,
                 option = 'app_dir',
                 level = logging.ERROR)
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
        self.log("Permissions on $OSG_APP/etc should be 777, 1777, " \
                 "2777, 775, 1775, 2775, 755, 1755, 2755 " \
                 "for sites: %s" % etc_dir,
                 section = self.config_section,
                 option = 'app_dir',
                 level = logging.WARNING)
    # pylint: disable-msg=W0703      
    except Exception:
      self.log("Can't check $OSG_APP, got an exception", 
               level = logging.ERROR,
               exception = True)
      return False
    
    return True
