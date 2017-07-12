"""Unit tests for job gateway configuration"""

import os
import sys
import unittest
import ConfigParser
import logging


# Important libraries are in the parent directory
sys.path.insert(0, os.path.realpath('../'))

from osg_configure.modules.utilities import get_test_config
from osg_configure.configure_modules import gateway

# NullHandler is only available in Python 2.7+
try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

global_logger = logging.getLogger(__name__)
global_logger.addHandler(NullHandler())


class TestGateway(unittest.TestCase):
    def testParsing(self):
        """
        Test Gateway module parsing
        """

        config_file = get_test_config("gateway/gateway_default.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = gateway.GatewayConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'gram_gateway_enabled': False,
                     'htcondor_gateway_enabled': True}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but "
                             "expected %s" % (var, options[var].value, variables[var]))

    def testGram(self):
        """
        Verifies that enabling GRAM now causes an error
        """
        config_file = get_test_config("gateway/gateway_gram.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = gateway.GatewayConfiguration(logger=global_logger)
        settings.parse_configuration(configuration)
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not raise error on GRAM enabled")


if __name__ == '__main__':
    unittest.main()
