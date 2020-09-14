"""Unit tests to test managed fork configuration"""

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

from osg_configure.configure_modules import localsettings
from osg_configure.modules.utilities import get_test_config
from osg_configure.modules import exceptions

# NullHandler is only available in Python 2.7+
try:
    NullHandler = logging.NullHandler
except AttributeError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

global_logger = logging.getLogger(__name__)
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
        configuration = configparser.SafeConfigParser()
        configuration.optionxform = str
        configuration.read(config_file)

        settings = localsettings.LocalSettings(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue('test1' in attributes,
                        'Attribute test1 missing')
        self.assertEqual(attributes['test1'], 'Value1',
                         'Wrong value obtained for test1')

        self.assertFalse('missing_key' in attributes,
                         'Non-existent key (missing_key) found')

        self.assertFalse('default_key' in attributes,
                         'Default key recognized as a local attribute')

    def testBogusVarName(self):
        config_file = get_test_config("localsettings/bogusvarname.ini")
        configuration = configparser.SafeConfigParser()
        configuration.optionxform = str
        configuration.read(config_file)

        settings = localsettings.LocalSettings(logger=global_logger)
        self.assertRaises(exceptions.SettingError,
                          settings.parse_configuration,
                          configuration)


    def testBogusQuote(self):
        config_file = get_test_config("localsettings/bogusquote.ini")
        configuration = configparser.SafeConfigParser()
        configuration.optionxform = str
        configuration.read(config_file)

        settings = localsettings.LocalSettings(logger=global_logger)
        self.assertRaises(exceptions.SettingError,
                          settings.parse_configuration,
                          configuration)


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
