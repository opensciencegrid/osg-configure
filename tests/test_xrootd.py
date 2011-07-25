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


from configure_osg.configure_modules import xrootd

global_logger = logging.getLogger('test xrootd configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestXrootd(unittest.TestCase):
  """
  Unit test class to test XrootdConfiguration class
  """

  def testParsing1(self):
    """
    Test xrootd parsing
    """
    
    config_file = os.path.abspath("./configs/xrootd/xrootd1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'user' : 'daemon',
                 'mode' : 'data',
                 'redirector_host' : 'example.com',
                 'redirector_storage_path' : './configs/xrootd',
                 'redirector_storage_cache' : './configs/xrootd',
                 'token_list' : 'ATLASDATADISK[desc:ATLASDATADISK][40000];ATLASPRODDISK[desc:ATLASPRODDISK][30000];',
                 'public_cache_size' : '30'}
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
    Test xrootd parsing
    """
    
    config_file = os.path.abspath("./configs/xrootd/xrootd2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'user' : 'daemon',
                 'mode' : 'data',
                 'redirector_host' : 'example.com',
                 'redirector_storage_path' : './configs/xrootd',
                 'redirector_storage_cache' : './configs/xrootd',
                 'token_list' : 'ATLASDATADISK[desc:ATLASDATADISK][40000];ATLASPRODDISK[desc:ATLASPRODDISK][30000];',
                 'public_cache_size' : '30'}
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
    Test xrootd parsing when set to disabled
    """
    
    config_file = os.path.abspath("./configs/xrootd/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
    
  def testParsingIgnored(self):
    """
    Test xrootd parsing when set to ignored
    """
    
    config_file = os.path.abspath("./configs/xrootd/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")


  def testInvalidTokens1(self):
    """
    Test the checkAttributes function to see if it catches invalid
    space tokens
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/invalid_tokens1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid tokens")
    
  def testInvalidTokens2(self):
    """
    Test the checkAttributes function to see if it catches invalid
    space tokens
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/invalid_tokens2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid tokens")

  def testInvalidRedirector(self):
    """
    Test the checkAttributes function to see if it catches invalid
    xrootd redirector
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/invalid_redirector.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid redirector host")

  def testInvalidMode(self):
    """
    Test the checkAttributes function to see if it catches invalid
    xrootd modes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/invalid_mode.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid mode")

  def testInvalidDaemon(self):
    """
    Test the checkAttributes function to see if it catches invalid
    xrootd user setting
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/invalid_user.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid user setting")

  def testInvalidCacheSize(self):
    """
    Test the checkAttributes function to see if it catches invalid
    cache size
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/invalid_cache_size.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid cache size")

  def testMissingCache(self):
    """
    Test the checkAttributes function to see if it catches a missing 
    cache entry
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/missing_cache.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing cache entry")

  def testMissingPath(self):
    """
    Test the checkAttributes function to see if it catches a missing 
    path entry
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootd/missing_path.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing path entry")

  def testValidSettings1(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/xrootd/check_ok1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/xrootd/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")
    
  def testValidSettings3(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/xrootd/check_ok3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")

  def testValidSettings4(self):
    """
    Test the checkAttributes function to see if it oks a disabled configuration
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/xrootd/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootd.XrootdConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")
    
if __name__ == '__main__':
    unittest.main()
