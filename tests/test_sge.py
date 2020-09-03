"""Unit tests to test sge configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

from __future__ import absolute_import
import os
import sys
import unittest
import configparser
import logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.configure_modules import sge
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


class TestSGE(unittest.TestCase):
    """
    Unit test class to test SGEConfiguration class
    """

    def testParsing(self):
        """
        Test configuration parsing
        """

        config_file = get_test_config("sge/sge1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        options = {'OSG_JOB_MANAGER_HOME': './test_files',
                   'OSG_SGE_LOCATION': './test_files',
                   'OSG_SGE_ROOT': './test_files',
                   'OSG_SGE_CELL': 'sge',
                   'OSG_JOB_MANAGER': 'SGE'}
        for option in options:
            value = options[option]
            self.assertTrue(option in attributes,
                            "Attribute %s missing" % option)
            err_msg = "Wrong value obtained for %s, " \
                      "got %s instead of %s" % (option, attributes[option], value)
            self.assertEqual(attributes[option], value, err_msg)

    def testParsingDisabled(self):
        """
        Test parsing disabled configuration
        """

        config_file = get_test_config("sge/sge_disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertEqual(len(attributes), 0,
                         "Disabled configuration should have no attributes")

    def testParsingIgnored(self):
        """
        Test parsing ignored configuration
        """

        config_file = get_test_config("sge/ignored.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertEqual(len(attributes), 0,
                         "Ignored configuration should have no attributes")

    def testMissingAttribute(self):
        """
        Test the parsing when attributes are missing, should get exceptions
        """

        mandatory = ['sge_root',
                     'sge_cell',
                     'sge_bin_location']
        for option in mandatory:
            config_file = get_test_config("sge/sge1.ini")
            configuration = configparser.SafeConfigParser()
            configuration.read(config_file)
            configuration.remove_option('SGE', option)

            settings = sge.SGEConfiguration(logger=global_logger)
            self.assertRaises(exceptions.SettingError,
                              settings.parse_configuration,
                              configuration)

    def testMissingSGERoot(self):
        """
        Test the check_attributes function to see if it catches missing SGE location
        """

        config_file = get_test_config("sge/missing_root.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice missing SGE root")

    def testMissingSGECell(self):
        """
        Test the check_attributes function to see if it catches missing SGE cell
        """

        config_file = get_test_config("sge/missing_cell.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice missing SGE cell")

    def testMissingSGEConfig(self):
        """
        Test the check_attributes function to see if it catches missing SGE config
        """

        config_file = get_test_config("sge/missing_config.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice missing SGE config")

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """

        config_file = get_test_config("sge/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)
        root = os.path.join(config_file[:-16], 'test_files')
        configuration.set('SGE', 'sge_root', root)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct settings incorrectly flagged as invalid")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """

        config_file = get_test_config("sge/check_ok2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)
        root = os.path.join(config_file[:-17], 'test_files')
        configuration.set('SGE', 'sge_root', root)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct settings incorrectly flagged as invalid")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        config_file = get_test_config("sge/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = {'condor-ce', 'globus-gridftp-server'}
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("sge/sge_disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = set()
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("sge/ignored.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = sge.SGEConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = set()
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
