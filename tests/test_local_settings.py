"""Unit tests to test managed fork configuration"""

#pylint: disable=W0703
#pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.configure_modules import localsettings
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

class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test LocalSettings class
  """

  def testParsing(self):
    """
    Test install locations parsing
    """
    
    config_file = get_test_config("localsettings/local_settings1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.optionxform = str
    configuration.read(config_file)

    settings = localsettings.LocalSettings(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 
    attributes = settings.getAttributes()
    self.assertTrue(attributes.has_key('test1'), 
                    'Attribute test1 missing')
    self.assertEqual(attributes['test1'], 'Value1', 
                     'Wrong value obtained for test1')
    
    self.assertTrue(attributes.has_key('Test2-'), 
                    'Attribute Test2- missing')
    self.assertEqual(attributes['Test2-'], 'Val03-42', 
                     'Wrong value obtained for Test2-')
  
    self.assertFalse(attributes.has_key('missing-key'), 
                'Non-existent key (missing-key) found')
    
    self.assertFalse(attributes.has_key('default-key'), 
                'Default key recognized as a local attribute')
    
if __name__ == '__main__':
  console = logging.StreamHandler()
  console.setLevel(logging.ERROR)
  global_logger.addHandler(console)
  unittest.main()
