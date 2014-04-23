"""Unit tests for CE configuration"""

import os
import sys
import unittest
import ConfigParser
import logging


# Important libraries are in the parent directory
sys.path.insert(0, os.path.realpath('../'))

from osg_configure.modules import utilities
from osg_configure.modules.utilities import get_test_config
from osg_configure.modules import exceptions
from osg_configure.configure_modules import ce

try:
  NullHandler = logging.NullHandler
except AttributeError:
  # NullHandler is only available in Python 2.7+
  class NullHandler(logging.Handler):
    def emit(self, record):
      pass

global_logger = logging.getLogger(__name__)
global_logger.addHandler(NullHandler())


class TestCE(unittest.TestCase):

  def testParsing(self):
    """
    Test CE module parsing
    """

    config_file = get_test_config("ce/ce_default.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = ce.CEConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)

    options = settings.options
    variables = {'gram_ce_enabled': True,
                 'htcondor_ce_enabled': False}
    for var in variables:
      self.assertTrue(options.has_key(var),
                      "Option %s missing" % var)
      self.assertEqual(options[var].value,
                       variables[var],
                       "Wrong value obtained for %s, got %s but "
                       "expected %s" % (var, options[var].value, variables[var]))


if __name__ == '__main__':
  unittest.main()
