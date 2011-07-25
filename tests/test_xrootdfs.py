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

from configure_osg.configure_modules import xrootdfs

global_logger = logging.getLogger('test xrootdfs configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestXrootdFS(unittest.TestCase):
  """
  Unit test class to test XrootdFSConfiguration class
  """

  def testParsing1(self):
    """
    Test xrootdfs parsing
    """
    
    config_file = os.path.abspath("./configs/xrootdfs/xrootdfs.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'user' : 'daemon',
                 'redirector_host' : 'example.com',
                 'mount_point' : './configs/xrootdfs',
                 'redirector_storage_path' : './configs/xrootdfs'}
    print attributes
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
    Test xrootdfs parsing when section is disabled
    """
    
    config_file = os.path.abspath("./configs/xrootdfs/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")

  def testParsingIgnored(self):
    """
    Test xrootdfs parsing when section is ignored
    """
    
    config_file = os.path.abspath("./configs/xrootdfs/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")

  def testInvalidHost(self):
    """
    Test the checkAttributes function to see if it catches invalid
    xrootd redirector host
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootdfs/invalid_host.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid redirector host")

  def testInvalidMount(self):
    """
    Test the checkAttributes function to see if it catches invalid
    xrootd mount point
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootdfs/invalid_mount.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid mount point")

  def testInvalidUser(self):
    """
    Test the checkAttributes function to see if it catches invalid
    user being specified for xrootdfs
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootdfs/invalid_user.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid user")


  def testMissingPath(self):
    """
    Test the checkAttributes function to see if it catches an invalid
    storage path
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/xrootdfs/missing_path.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing storage path")

  def testValidSettings1(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/xrootdfs/check_ok1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
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
    config_file = os.path.abspath("./configs/xrootdfs/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = xrootdfs.XrootdFSConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings incorrectly flagged as missing")
    
    
if __name__ == '__main__':
    unittest.main()
