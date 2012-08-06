#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import validation
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
                 'OSG_GRID' : '/tmp',
                 'OSG_APP' : '/tmp',
                 'OSG_DATA' : '/var',
                 'OSG_WN_TMP' : '/usr',
                 'OSG_SITE_READ' : '/bin',
                 'OSG_SITE_WRITE' : '/usr/bin'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
    if not validation.valid_directory('/tmp/etc'):
      # handle cases where this is not run under osg test framework
      os.mkdir('/tmp/etc')
      os.chmod('/tmp/etc', 0777)      
      self.assertTrue(settings.checkAttributes(attributes))
      os.rmdir('/tmp/etc')
    else:
      self.assertTrue(settings.checkAttributes(attributes))
      


  def testParsing2(self):
    """
    Test storage parsing
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
                 'OSG_GRID' : '/usr',
                 'OSG_APP' : '/tmp',
                 'OSG_DATA' : '/usr/bin',
                 'OSG_WN_TMP' : '/usr/sbin',
                 'OSG_SITE_READ' : '/tmp',
                 'OSG_SITE_WRITE' : '/var'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var,                                             
                                            attributes[var],
                                            variables[var]))
    if not validation.valid_directory('/tmp/etc'):
      # handle cases where this is not run under osg test framework
      os.mkdir('/tmp/etc')
      os.chmod('/tmp/etc', 0777)      
      self.assertTrue(settings.checkAttributes(attributes))
      os.rmdir('/tmp/etc')
    else:
      self.assertTrue(settings.checkAttributes(attributes))

  def testParsing3(self):
    """
    Test storage parsing
    """
    
    # StorageConfiguration is not enabled on non-ce installs
    if not utilities.ce_installed():
      return
    config_file = get_test_config("storage/storage3.ini")
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
                 'OSG_GRID' : '/etc',
                 'OSG_APP' : '/tmp',
                 'OSG_DATA' : 'UNAVAILABLE',
                 'OSG_SITE_READ' : '/var',
                 'OSG_SITE_WRITE' : '/usr'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var,                                             
                                            attributes[var],
                                            variables[var]))
    if not validation.valid_directory('/tmp/etc'):
      # handle cases where this is not run under osg test framework
      os.mkdir('/tmp/etc')
      os.chmod('/tmp/etc', 0777)      
      self.assertTrue(settings.checkAttributes(attributes))
      os.rmdir('/tmp/etc')
    else:
      self.assertTrue(settings.checkAttributes(attributes))
                
  def testMissingAttribute(self):
    """
    Test the checkAttributes function 
    """
        

    # StorageConfiguration is not enabled on non-ce installs
    if not utilities.ce_installed():
      return
    mandatory = ['se_available',
                 'app_dir']
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
