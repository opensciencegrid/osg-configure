#!/usr/bin/python

""" Module to handle legacy attributes """

from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['LegacyConfiguration']


class LegacyConfiguration(BaseConfiguration):
  """Class to handle attributes related to installation locations"""
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(LegacyConfiguration, self).__init__(*args, **kwargs)
    self.logger.debug('LegacyConfiguration.__init__ started')        
    self.__mappings = {'GRID3_SITE_NAME': 'OSG_SITE_NAME', 
                       'GRID3_APP_DIR': 'OSG_APP',
                       'GRID3_DATA_DIR': 'OSG_DATA',
                       'GRID3_TMP_DIR': 'OSG_DATA',
                       'GRID3_TMP_WN_DIR': 'OSG_WN_TMP',
                       'GRID3_SPONSOR': 'OSG_SPONSOR',
                       'GRID3_SITE_INFO': 'OSG_SITE_INFO',
                       'GRID3_UTIL_CONTACT': 'OSG_UTIL_CONTACT',
                       'GRID3_JOB_CONTACT': 'OSG_JOB_CONTACT',
                       'GRID3_USER_VO_MAP': 'OSG_USER_VO_MAP',
                       'GRID3_GRIDFTP_LOG': 'OSG_GRIDFTP_LOG',
                       'GRID3_TRANSFER_CONTACT': 'OSG_UTIL_CONTACT'}
    self.logger.debug('LegacyConfiguration.__init__ completed')        
        
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('LegacyConfiguration.checkAttributes started')        
    attributes_ok = True
    # Make sure all settings are present
    for setting in self.__mappings:
      if setting not in self.attributes:
        self.logger.debug("Missing setting for %s for legacy attributes" % 
                          (self.__mappings[setting]))
    self.logger.debug('LegacyConfiguration.checkAttributes completed')        
    return attributes_ok 
  
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('LegacyConfiguration.configure started')        
    for key in self.__mappings:
      self.logger.debug("Checking for %s" % key)        
      if self.__mappings[key] in attributes:
        self.logger.debug("Found %s for %s" % (attributes[self.__mappings[key]], 
                                               key))        
        self.attributes[key] = attributes[self.__mappings[key]]
      else:
        self.logger.debug("%s not found" % key)        
    self.logger.debug('LegacyConfiguration.configure completed')        
    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "Legacy"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return False
