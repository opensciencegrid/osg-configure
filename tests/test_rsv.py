"""Unit tests to test managed fork configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging


# setup system library path 
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import rsv
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

if os.path.exists('./configs/rsv/meta'):
    RSV_META_DIR = './configs/rsv/meta'
elif os.path.exists('/usr/share/osg-configure/tests/configs/rsv/meta'):
    RSV_META_DIR = '/usr/share/osg-configure/tests/configs/rsv/meta'


class TestRSV(unittest.TestCase):
    """
    Unit test class to test RsvConfiguration class
    """

    def load_settings_from_files(self, *cfgfiles):
        configuration = ConfigParser.SafeConfigParser()
        for cfgfile in cfgfiles:
            configuration.read(get_test_config(cfgfile))

        settings = rsv.RsvConfiguration(logger=global_logger)
        settings.rsv_meta_dir = RSV_META_DIR
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        return settings

    def testParsing1(self):
        """
        Test rsv parsing
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return

        settings = self.load_settings_from_files("rsv/rsv1.ini")
        options = settings.options
        variables = {'gratia_probes': 'pbs,metric,condor',
                     'ce_hosts': 'my.host.com',
                     'gridftp_hosts': 'my.host.com',
                     'gridftp_dir': '/tmp',
                     'gums_hosts': 'my.host.com',
                     'srm_hosts': 'test.com:60443',
                     'srm_dir': '/srm/dir',
                     'srm_webservice_path': 'srm/v2/server',
                     'service_cert': '/etc/redhat-release',
                     'service_key': '/etc/redhat-release',
                     'service_proxy': '/tmp/rsvproxy',
                     'enable_gratia': True,
                     'enable_nagios': True}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsing2(self):
        """
        Test rsv parsing
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return

        settings = self.load_settings_from_files("rsv/rsv2.ini")
        options = settings.options
        variables = {'gratia_probes': '',
                     'ce_hosts': 'my.host.com, my2.host.com',
                     'gridftp_hosts': 'my.host.com, my2.host.com',
                     'gridftp_dir': '/tmp',
                     'gums_hosts': 'my.host.com, my2.host.com',
                     'srm_hosts': 'my.host.com, my2.host.com',
                     'srm_dir': '/srm/dir, /srm/dir2',
                     'srm_webservice_path': 'srm/v2/server,',
                     'service_cert': '/etc/redhat-release',
                     'service_key': '/etc/redhat-release',
                     'service_proxy': '/tmp/rsvproxy',
                     'enable_gratia': False,
                     'enable_nagios': False}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testMultipleHosts(self):
        """
        Test rsv parsing
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/multiple_hosts.ini")
        options = settings.options
        variables = {'ce_hosts': 'host1.site.com, host2.site.com',
                     'gridftp_hosts': 'host3.site.com, host4.site.com',
                     'gridftp_dir': '/tmp',
                     'gums_hosts': 'host8.site.com, host9.site.com',
                     'srm_hosts': 'host5.site.com, host6.site.com, host7.site.com:1234',
                     'srm_dir': '/srm/dir',
                     'srm_webservice_path': 'srm/v2/server',
                     'service_cert': './configs/rsv/rsv1.ini',
                     'service_key': './configs/rsv/rsv1.ini',
                     'service_proxy': '/tmp/rsvproxy',
                     'enable_gratia': True,
                     'enable_nagios': True}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))

    def testParsingIgnored(self):
        """
        Test parsing when ignored
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/ignored.ini")
        attributes = settings.get_attributes()
        self.assertEqual(len(attributes), 0,
                         "Ignored configuration should have no attributes")

    def testParsingDisabled(self):
        """
        Test parsing when disabled
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/disabled.ini")
        attributes = settings.get_attributes()
        self.assertEqual(len(attributes), 0,
                         "Disabled configuration should have no attributes")

    def testMissingAttribute(self):
        """
        Test the parsing when attributes are missing, should get exceptions
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        config_file = get_test_config("rsv/rsv2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = rsv.RsvConfiguration(logger=global_logger)
        settings.rsv_meta_dir = RSV_META_DIR
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        mandatory = ['enable_gratia',
                     'enable_nagios']
        for option in mandatory:
            config_file = get_test_config("rsv/rsv1.ini")
            configuration = ConfigParser.SafeConfigParser()
            configuration.read(config_file)
            configuration.remove_option('RSV', option)

            settings = rsv.RsvConfiguration(logger=global_logger)
            settings.rsv_meta_dir = RSV_META_DIR
            self.assertRaises(exceptions.SettingError,
                              settings.parse_configuration,
                              configuration)

    def testInvalidKey(self):
        """
        Test the check_attributes with invalid key file
        """


        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_key.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid rsv key file ignored")

    def testMissingKey(self):
        """
        Test the check_attributes with a missing rsv key file
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/missing_key.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Missing rsv key file ignored")

    def testInvalidCert(self):
        """
        Test the check_attributes with invalid cert file
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_cert.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid rsv cert file ignored")

    def testMissingCert(self):
        """
        Test the check_attributes with a missing rsv cert file
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/missing_cert.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Missing rsv cert file ignored")

    def testInvalidProxy(self):
        """
        Test the check_attributes with invalid proxy file
        """


        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_proxy.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid rsv proxy file ignored")

    def testMissingProxy(self):
        """
        Test the check_attributes with a missing proxy cert file
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/missing_proxy.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Missing rsv proxy file ignored")

    def testInvalidGratiaProbes(self):
        """
        Test the check_attributes with invalid gratia probes
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_gratia1.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid gratia probe ignored")

        settings = self.load_settings_from_files("rsv/invalid_gratia2.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid gratia probe list ignored")

    def testInvalidCEHost(self):
        """
        Test the check_attributes with invalid ce host
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_ce_host.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid ce  ignored")

    def testInvalidGumsHost(self):
        """
        Test the check_attributes with invalid gums host
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_gums_host.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid gums host ignored")

    def testInvalidGridftpHost(self):
        """
        Test the check_attributes with invalid gridftp host
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_gridftp_host.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid gridftp ignored")

    def testInvalidSRMHost(self):
        """
        Test the check_attributes with invalid srm host
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/invalid_srm_host.ini")
        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Invalid srm ignored")

    def testValidSettings1(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """

        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/rsv1.ini")
        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct configuration incorrectly flagged as incorrect")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it works on valid settings
        """
        # need to have rsv installed to get rsv tests working
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/rsv2.ini")
        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct configuration incorrectly flagged as incorrect")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """
        # If rsv-core is not installed, settings.enabled will always be False
        if not utilities.rpm_installed('rsv-core'):
            return
        settings = self.load_settings_from_files("rsv/rsv1.ini")
        services = settings.enabled_services()
        expected_services = set(['rsv', 'condor-cron'])
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        settings = self.load_settings_from_files("rsv/disabled.ini")
        services = settings.enabled_services()
        expected_services = set()
        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        settings = self.load_settings_from_files("rsv/ignored.ini")
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
