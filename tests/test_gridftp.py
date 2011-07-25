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


from configure_osg.configure_modules import gridftp

global_logger = logging.getLogger('test gridftp configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestGridFTP(unittest.TestCase):
  """
  Unit test class to test GridFTPConfiguration class
  """

  def testParsing1(self):
    """
    Test gridftp parsing
    """
    
    config_file = os.path.abspath("./configs/gridftp/gridftp1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'mode' : 'xrootd',
                 'redirector' : 'example.com',
                 'mount_point' : './configs/gridftp',
                 'redirector_storage_path' : './configs/gridftp'}
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
    Test gridftp parsing
    """
    
    config_file = os.path.abspath("./configs/gridftp/gridftp2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    variables = {'mode' : 'standalone',
                 'redirector' : 'example.com',
                 'mount_point' : './configs/gridftp',
                 'redirector_storage_path' : './configs/gridftp'}
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
    Test gridftp parsing when disabled
    """
    
    config_file = os.path.abspath("./configs/gridftp/disabled.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Disabled configuration should have no attributes")
    
  def testParsingIgnoreed(self):
    """
    Test gridftp parsing when ignored
    """
    
    config_file = os.path.abspath("./configs/gridftp/ignored.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    os.environ['VDT_LOCATION'] = '/opt/osg'
    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    attributes = settings.attributes
    self.failUnlessEqual(len(attributes), 0, 
                         "Ignored configuration should have no attributes")

    
  def testInvalidRedirector(self):
    """
    Test the checkAttributes function to see if it catches invalid
    redirector host
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gridftp/invalid_redirector.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
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
    gridftp modes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gridftp/invalid_mode.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice invalid mode")

  def testMissingRedirector(self):
    """
    Test the checkAttributes function to see if it catches a missing
    redirector host
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gridftp/missing_redirector.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing redirector")

  def testMissingMountPoint(self):
    """
    Test the checkAttributes function to see if it catches a missing mount 
    xrootd point
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gridftp/missing_mount.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing mount point")

  def testMissingStoragePath(self):
    """
    Test the checkAttributes function to see if it catches a missing storage
    path
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gridftp/missing_storage_path.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failIf(settings.checkAttributes(attributes), 
                "Did not notice missing storage path")

  def testMissingStoragePathDefault(self):
    """
    Test the checkAttributes function to see if it will use the storage path from 
    the xrootd section if the storage path is missing in the gridftp section
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()

    config_file = os.path.abspath("./configs/gridftp/storage_path_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.attributes
    if attributes['redirector_storage_path'] != './configs/gridftp':
      self.fail("Didn't get correct redirector storage path from Xrootd section")

  def testValidSettings1(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gridftp/check_ok1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings flagged as invalid")

  def testValidSettings2(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gridftp/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings flagged as invalid")
    
  def testValidSettings3(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gridftp/check_ok3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings flagged as invalid")

  def testValidSettings4(self):
    """
    Test the checkAttributes function to see if it oks good attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gridftp/check_ok4.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings flagged as invalid")
    
  def testValidSettings5(self):
    """
    Test the checkAttributes function to see if it verifies correct
    attributes
    """
        
    os.environ['VDT_LOCATION'] = os.getcwd()
    config_file = os.path.abspath("./configs/gridftp/check_ok5.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = gridftp.GridFTPConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(settings.checkAttributes(attributes), 
                    "Correct settings flagged as invalid")

if __name__ == '__main__':
    unittest.main()
