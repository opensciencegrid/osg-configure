#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path if it's not there at present
try:
  from configure_osg.modules import utilities
except ImportError:
  pathname = '../'
  sys.path.append(pathname)
  from configure_osg.modules import utilities

from configure_osg.modules import exceptions


from configure_osg.configure_modules import storage

global_logger = logging.getLogger('test storage configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)


class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test StorageConfiguration class
  """

  def testParsing1(self):
    """
    Test storage parsing
    """
    
    config_file = os.path.abspath("./configs/storage/storage1.ini")
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
    

  def testParsing2(self):
    """
    Test storage parsing with negative values
    """
    
    config_file = os.path.abspath("./configs/storage/storage2.ini")
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
    


  def testAttributeGeneration1(self):
    """
    Test the creation of a config file given attributes
    """
    
    config_file = os.path.abspath("./configs/storage/storage1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = storage.StorageConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()    
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'Storage'
    self.failUnless(new_config.has_section(section_name), 
                    "%s section not created in config file" % section_name)
    
    options = {'se_available' : 'True',
               'default_se' : 'test.domain.org',
               'grid_dir' : './configs/storage1',
               'app_dir' : './configs/storage2',
               'data_dir' : './configs/storage3',
               'worker_node_temp' : './configs/storage4',
               'site_read' : './configs/storage5',
               'site_write' : './configs/storage6'}
    for option in options:      
      self.failUnless(new_config.has_option(section_name, option), 
                      "Option %s missing" % option)
      self.failUnlessEqual(new_config.get(section_name, option), 
                           options[option], 
                           "Wrong value obtained for %s, expected %s, got %s" %
                           (option,
                            options[option],
                            new_config.get(section_name, option)))
                            
    
  def testAttributeGeneration2(self):
    """
    Test the creation of a config file given attributes
    """
    
    config_file = os.path.abspath("./configs/storage/storage2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = storage.StorageConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()    
    new_config = ConfigParser.SafeConfigParser()
    settings.generateConfigFile(attributes.items(), new_config)
    section_name = 'Storage'
    self.failUnless(new_config.has_section(section_name), 
                    "%s section not created in config file" % section_name)
    
    options = {'se_available' : 'False',
               'default_se' : 'test.domain.org',
               'grid_dir' : './configs/storage1',
               'app_dir' : './configs/storage2',
               'data_dir' : './configs/storage3',
               'worker_node_temp' : './configs/storage4',
               'site_read' : './configs/storage5',
               'site_write' : './configs/storage6'}
    for option in options:      
      self.failUnless(new_config.has_option(section_name, option), 
                      "Option %s missing" % option)
      self.failUnlessEqual(new_config.get(section_name, option), 
                           options[option], 
                           "Wrong value obtained for %s, expected %s, got %s" %
                           (option,
                            options[option],
                            new_config.get(section_name, option)))
                                                        

  def testMissingAttribute(self):
    """
    Test the checkAttributes function 
    """
        

    mandatory = ['se_available',
                 'app_dir',
                 'worker_node_temp',
                 'data_dir']
    for option in mandatory:
      config_file = os.path.abspath("./configs/storage/storage1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('Storage', option)

      settings = storage.StorageConfiguration(logger=global_logger)
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration, 
                            configuration)

    
if __name__ == '__main__':
    unittest.main()
