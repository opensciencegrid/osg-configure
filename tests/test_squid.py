#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path if it's not there at present
try:
  from osg_configure.modules import utilities
except ImportError:
  pathname = '../'
  sys.path.append(pathname)
  from osg_configure.modules import utilities

from osg_configure.modules import exceptions


from osg_configure.configure_modules import squid

global_logger = logging.getLogger('test squid configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestSquidSettings(unittest.TestCase):
  """
  Unit test class to test SquidConfiguration class
  """

  def testParsing1(self):
    """
    Test squid parsing
    """
    
    config_file = os.path.abspath("./configs/squid/squid1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_SQUID_LOCATION' : "%s:3128" % utilities.get_hostname(),
                 'OSG_SQUID_POLICY' : 'LRU',
                 'OSG_SQUID_CACHE_SIZE' : '2048',
                 'OSG_SQUID_MEM_CACHE' : '256'}
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
    Test squid parsing
    """
    
    config_file = os.path.abspath("./configs/squid/squid2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    variables = {'OSG_SQUID_LOCATION' : 'example.com:3128',
                 'OSG_SQUID_POLICY' : 'LRU',
                 'OSG_SQUID_CACHE_SIZE' : '2048',
                 'OSG_SQUID_MEM_CACHE' : '256'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
    
  def testParsingDisabled(self):
    """
    Test parsing when disabled
    """
    
    config_file = os.path.abspath("./configs/squid/squid_disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 4, 
                         "Disabled configuration should have 4 attributes")
    
    variables = {'OSG_SQUID_LOCATION' : 'UNAVAILABLE',
                 'OSG_SQUID_POLICY' : 'UNAVAILABLE',
                 'OSG_SQUID_CACHE_SIZE' : 'UNAVAILABLE',
                 'OSG_SQUID_MEM_CACHE' : 'UNAVAILABLE'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))
                                                            
  def testParsingIgnored(self):
    """
    Test parsing when ignored
    """
    
    config_file = os.path.abspath("./configs/squid/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.getAttributes()
    self.failUnlessEqual(len(attributes), 4, 
                         "Ignored configuration should have 4 attributes")
    
    variables = {'OSG_SQUID_LOCATION' : 'UNAVAILABLE',
                 'OSG_SQUID_POLICY' : 'UNAVAILABLE',
                 'OSG_SQUID_CACHE_SIZE' : 'UNAVAILABLE',
                 'OSG_SQUID_MEM_CACHE' : 'UNAVAILABLE'}
    for var in variables:      
      self.failUnless(attributes.has_key(var), 
                      "Attribute %s missing" % var)
      self.failUnlessEqual(attributes[var], 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            attributes[var], 
                                            variables[var]))


  def testMissingAttribute(self):
    """
    Test the parsing when attributes are missing, should get exceptions
    """
        

    os.environ['VDT_LOCATION'] = os.getcwd()
    mandatory = ['location', 
                 'policy',
                 'cache_size',
                 'memory_size']
    for option in mandatory:
      config_file = os.path.abspath("./configs/squid/squid1.ini")
      configuration = ConfigParser.SafeConfigParser()
      configuration.read(config_file)
      configuration.remove_option('Squid', option)

      settings = squid.SquidConfiguration(logger=global_logger)
      self.failUnlessRaises(exceptions.SettingError, 
                            settings.parseConfiguration, 
                            configuration)


  def testBadMemory(self):
    """
    Test the checkAttributes function when memory size is not an integer
    """
        

    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/squid/squid_bad_mem.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration")

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid memory size")
    
  def testBadCache(self):
    """
    Test the checkAttributes function when cache size is not an integer
    """
        

    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/squid/squid_bad_cache.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration")

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid cache size")
                

  def testBadHost(self):
    """
    Test the checkAttributes function when the squid proxy hostname is
    not valie
    """
        

    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/squid/squid_bad_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration")

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid host")

  def testBadPort(self):
    """
    Test the checkAttributes function when port for the squid proxy is 
    not an integer
    """
        

    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/squid/squid_bad_port.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration")

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid port number")

  def testMissingLocation(self):
    """
    Test the checkAttributes function when squid location is missing
    """
        

    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/squid/squid_missing_location.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration")

    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid squid location")

  def testValidSettings(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/squid/valid_settings.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = squid.SquidConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct locations incorrectly flagged as missing")
    
if __name__ == '__main__':
    unittest.main()
