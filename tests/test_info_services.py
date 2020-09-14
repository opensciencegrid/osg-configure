"""Unit tests to test infoservices configuration class"""
# This has been copied from test_cemon.py and has had the names changed.
# Further changes will be needed to reduce duplication between the two
# sets of tests; changes will need to be made to the configure modules
# to reduce duplication there as well.

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

from osg_configure.modules import exceptions
try:
    from osg_configure.configure_modules import infoservices
except ImportError:
    infoservices = None
    print("infoservices not found -- skipping infoservices tests")
from osg_configure.modules import utilities
from osg_configure.modules.utilities import get_test_config

global_logger = logging.getLogger(__name__)
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass
global_logger.addHandler(NullHandler())


class TestInfoServices(unittest.TestCase):
    """
    Unit test class to test InfoServicesConfiguration class
    """

    def testParsingDisabled(self):
        """
        Test infoservices parsing when set to disabled
        """

        if not infoservices: return
        config_file = get_test_config("infoservices/disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

    def testParsingIgnored(self):
        """
        Test infoservices parsing when set to ignored
        """

        if not infoservices: return
        config_file = get_test_config("infoservices/ignored.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks a disabled section
        """

        if not infoservices: return
        config_file = get_test_config("infoservices/disabled.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Disabled section incorrectly flagged as invalid")

    def testMissingCEITBDefaults(self):
        """
        Test the check_attributes function to see if it oks the itb defaults
        set when the infoservices section is missing
        """

        if not infoservices: return
        config_file = get_test_config("infoservices/itb_defaults2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "ITB defaults incorrectly flagged as invalid")

    def testMissingProductionDefaults(self):
        """
        Test the check_attributes function to see if it oks the production defaults
        set when the infoservices section is missing
        """

        if not infoservices: return
        config_file = get_test_config("infoservices/prod_defaults2.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "production defaults incorrectly flagged as invalid")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        if not infoservices: return
        config_file = get_test_config("infoservices/infoservices.ini")
        configuration = configparser.SafeConfigParser()
        configuration.read(config_file)

        settings = infoservices.InfoServicesConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception as e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        expected_services = set()
        if settings.ce_collector_required_rpms_installed and settings.htcondor_gateway_enabled:
            expected_services.add('condor-ce')
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))


if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()

# vim:sw=2:sts=2
