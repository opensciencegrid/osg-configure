#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import storage
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger(__name__)
if sys.version_info[0] >= 2 and sys.version_info[1] > 6:
  global_logger.addHandler(logging.NullHandler())
else:
  # NullHandler is only in python 2.7 and above
  class NullHandler(logging.Handler):
    def emit(self, record):
        pass
            
  global_logger.addHandler(NullHandler())


class TestStorage(unittest.TestCase):
  """
  Unit test class to test StorageConfiguration class
  """

  def testParsing1(self):
    """
    Test storage parsing
    """
    
    # StorageConfiguration is not enabled on non-ce installs
    if not utilities.ce_installed():
      return

    config_file = get_test_config("storage/storage1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = storage.StorageConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_STORAGE_ELEMENT' : 'True',
                 'OSG_DEFAULT_SE' : 'test.domain.org',
                 'OSG_GRID' : './configs/storage1',
                 'OSG_APP' : './configs/storage2',
                 'OSG_DATA' : './configs/storage3',
                 'OSG_WN_TMP' : './configs/storage4',
                 'OSG_SITE_READ' : './configs/storage5',
                 'OSG_SITE_WRITE' : './configs/storage6'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
    self.assertTrue(settings.parseConfiguration([]))
    

  def testParsing2(self):
    """
    Test storage parsing with negative values
    """
    
    # StorageConfiguration is not enabled on non-ce installs
    if not utilities.ce_installed():
      return
    config_file = get_test_config("storage/storage2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = storage.StorageConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_STORAGE_ELEMENT' : 'False',
                 'OSG_DEFAULT_SE' : 'test.domain.org',
                 'OSG_GRID' : './configs/storage1',
                 'OSG_APP' : './configs/storage2',
                 'OSG_DATA' : './configs/storage3',
                 'OSG_WN_TMP' : './configs/storage4',
                 'OSG_SITE_READ' : './configs/storage5',
                 'OSG_SITE_WRITE' : './configs/storage6'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var,                                             
                                            attributes[var],
                                            variables[var]))
    self.assertTrue(settings.parseConfiguration([]))

  def testParsing2(self):
    """
    Test storage parsing with negative values
    """
    
    # StorageConfiguration is not enabled on non-ce installs
    if not utilities.ce_installed():
      return
    config_file = get_test_config("storage/storage2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = storage.StorageConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_STORAGE_ELEMENT' : 'False',
                 'OSG_DEFAULT_SE' : 'test.domain.org',
                 'OSG_GRID' : './configs/storage1',
                 'OSG_APP' : './configs/storage2',
                 'OSG_DATA' : 'UNAVAILABLE',
                 'OSG_SITE_READ' : './configs/storage5',
                 'OSG_SITE_WRITE' : './configs/storage6'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var,                                             
                                            attributes[var],
                                            variables[var]))
    self.assertTrue(settings.parseConfiguration([]))
                
  def testMissingAttribute(self):
    """
    Test the checkAttributes function 
    """
        

    # StorageConfiguration is not enabled on non-ce installs
    if not utilities.ce_installed():
      return
    mandatory = ['se_available',
                 'app_dir',
                 'data_dir']
    for option in mandatory:
      config_file = get_test_config("storage/storage1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('Storage', option)

      settings = storage.StorageConfiguration(logger=global_logger)
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration, 
                            configuration)

    
if __name__ == '__main__':
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)  
  unittest.main()
