#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import localsettings

global_logger = logging.getLogger('test localsettings configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test LocalSettings class
  """

  def testParsing(self):
    """
    Test install locations parsing
    """
    
    config_file = os.path.abspath("./configs/localsettings/local_settings1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.optionxform = str
    configuration.read(config_file)

    settings = localsettings.LocalSettings(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.failUnless(attributes.has_key('test1'), 
                    'Attribute test1 missing')
    self.failUnlessEqual(attributes['test1'], 'Value1', 
                         'Wrong value obtained for test1')
    
    self.failUnless(attributes.has_key('Test2-'), 
                    'Attribute Test2- missing')
    self.failUnlessEqual(attributes['Test2-'], 'Val03-42', 
                         'Wrong value obtained for Test2-')
  
    self.failIf(attributes.has_key('missing-key'), 
                'Non-existent key (missing-key) found')
    
    self.failIf(attributes.has_key('default-key'), 
                'Default key recognized as a local attribute')
    
if __name__ == '__main__':
    unittest.main()
