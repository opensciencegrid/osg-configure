"""Unit tests to test lsf configuration """

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

from osg_configure.configure_modules import lsf
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


class TestLSF(unittest.TestCase):
    """
    Unit test class to test LSFConfiguration class
    """

    def testParsing(self):
        """
        Test configuration parsing
        """

        config_file = get_test_config("lsf/lsf1.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        options = {'OSG_JOB_MANAGER_HOME': '/opt/lsf',
                   'OSG_LSF_LOCATION': '/opt/lsf',
                   'OSG_JOB_MANAGER': 'LSF'}
        for option in options:
            value = options[option]
            self.assertTrue(option in attributes,
                            "Attribute %s missing" % option)
            err_msg = "Wrong value obtained for %s, " \
                      "got %s instead of %s" % (option, attributes[option], value)
            self.assertEqual(attributes[option], value, err_msg)

    def testParsingDisabled(self):
        """
        Test parsing when disabled
        """

        config_file = get_test_config("lsf/lsf_disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertEqual(len(attributes),
                         0,
                         "Disabled configuration should have no attributes")

    def testParsingIgnored(self):
        """
        Test parsing when ignored
        """

        config_file = get_test_config("lsf/ignored.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertEqual(len(attributes),
                         0,
                         "Ignored configuration should have no attributes")

    def testMissingLSFLocation(self):
        """
        Test the check_attributes function to see if it catches missing LSF location
        """
        config_file = get_test_config("lsf/missing_location.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice missing LSF location")

    def testMissingLSFProfile(self):
        """
        Test the check_attributes function to see if it catches missing LSF profile
        """
        config_file = get_test_config("lsf/missing_profile.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
        self.assertRaises(exceptions.SettingError,
                          settings.parse_configuration,
                          configuration)

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """
        config_file = get_test_config("lsf/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
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
        config_file = get_test_config("lsf/check_ok2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
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

        config_file = get_test_config("lsf/check_ok.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = {'condor-ce', 'globus-gridftp-server'}
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("lsf/lsf_disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = lsf.LSFConfiguration(logger=global_logger)
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
