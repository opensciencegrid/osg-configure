"""Unit tests to test misc configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import configparser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import misc
from osg_configure.modules.utilities import get_test_config

# NullHandler is only available in Python 2.7+
try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

global_logger = logging.getLogger(__name__)
global_logger.addHandler(NullHandler())


class TestMisc(unittest.TestCase):
    """
    Unit test class to test MiscConfiguration class
    """

    def testParsingAuthentication(self):
        """
        Test misc parsing with negative values
        """

        config_file = get_test_config("misc/misc_gridmap.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue('authorization_method' in settings.options,
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'gridmap',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'gridmap'))

        config_file = get_test_config("misc/misc_local_gridmap.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue('authorization_method' in settings.options,
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'local-gridmap',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'local-gridmap'))

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("misc/valid_settings2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as invalid")

    def testInvalidSettings(self):
        """
        Test the check_attributes function to see if it flags bad attributes
        """

        config_file = get_test_config("misc/invalid_settings1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Bad config incorrectly flagged as okay")


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
