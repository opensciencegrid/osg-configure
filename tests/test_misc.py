"""Unit tests to test misc configuration"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import ConfigParser
import logging
import tempfile
import subprocess

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import misc
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


class TestMisc(unittest.TestCase):
    """
    Unit test class to test MiscConfiguration class
    """

    def testParsing1(self):
        """
        Test misc parsing
        """

        config_file = get_test_config("misc/misc1.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'glexec_location': './configs/misc',
                     'gums_host': 'my.gums.org',
                     'authorization_method': 'xacml'}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))
        attributes = settings.get_attributes()
        variables = {'OSG_GLEXEC_LOCATION': './configs/misc'}
        for var in variables:
            self.assertTrue(attributes.has_key(var),
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))

    def testParsing2(self):
        """
        Test misc parsing with negative values
        """

        config_file = get_test_config("misc/misc2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        options = settings.options
        variables = {'glexec_location': './configs/misc',
                     'gums_host': 'my.gums.org',
                     'authorization_method': 'xacml'}
        for var in variables:
            self.assertTrue(options.has_key(var),
                            "Option %s missing" % var)
            self.assertEqual(options[var].value,
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, options[var].value, variables[var]))
        attributes = settings.get_attributes()
        variables = {'OSG_GLEXEC_LOCATION': './configs/misc'}
        for var in variables:
            self.assertTrue(attributes.has_key(var),
                            "Attribute %s missing" % var)
            self.assertEqual(attributes[var],
                             variables[var],
                             "Wrong value obtained for %s, got %s but " \
                             "expected %s" % (var, attributes[var], variables[var]))

    def testParsingAuthentication(self):
        """
        Test misc parsing with negative values
        """

        config_file = get_test_config("misc/misc_xacml.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(settings.options.has_key('authorization_method'),
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'xacml',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'xacml'))

        config_file = get_test_config("misc/misc_gridmap.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(settings.options.has_key('authorization_method'),
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'gridmap',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'gridmap'))

        config_file = get_test_config("misc/misc_local_gridmap.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        self.assertTrue(settings.options.has_key('authorization_method'),
                        "Attribute authorization_method missing")
        self.assertEqual(settings.options['authorization_method'].value,
                         'local-gridmap',
                         "Wrong value obtained for %s, got %s but " \
                         "expected %s" % ('authorization_method',
                                          settings.options['authorization_method'].value,
                                          'local-gridmap'))

    def testMissingAttribute(self):
        """
        Test the parsing when attributes are missing, should get exceptions
        """

        mandatory = ['gums_host']
        for option in mandatory:
            config_file = get_test_config("misc/misc1.ini")
            configuration = ConfigParser.SafeConfigParser()
            configuration.read(config_file)
            configuration.remove_option('Misc Services', option)

            settings = misc.MiscConfiguration(logger=global_logger)
            settings.parse_configuration(configuration)
            self.assertTrue(not settings.check_attributes({}))

    def testXacmlMissingGums(self):
        """
        Test the check_attributes function when xacml is specified but the
        gums host isn't
        """

        config_file = get_test_config("misc/misc_xacml_missing_gums.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        settings.parse_configuration(configuration)
        self.assertTrue(exceptions.ConfigureError,
                        settings.check_attributes({}))

    def testXacmlBadGums(self):
        """
        Test the check_attributes function when xacml is specified but the
        gums host isn't valid
        """

        config_file = get_test_config("misc/misc_xacml_bad_gums.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Did not notice bad gums host")

    def testValidSettings(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("misc/valid_settings.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as missing")

    def testValidSettings2(self):
        """
        Test the check_attributes function to see if it oks good attributes
        """

        config_file = get_test_config("misc/valid_settings2.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertTrue(settings.check_attributes(attributes),
                        "Correct locations incorrectly flagged as invalid")

    def testInvalidSettings(self):
        """
        Test the check_attributes function to see if it flags bad attributes
        """

        config_file = get_test_config("misc/invalid_settings1.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)

        attributes = settings.get_attributes()
        self.assertFalse(settings.check_attributes(attributes),
                         "Bad config incorrectly flagged as okay")

    def testServiceList(self):
        """
        Test to make sure right services get returned
        """

        config_file = get_test_config("misc/misc_xacml.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        if utilities.rpm_installed('fetch-crl'):
            expected_services = set(['fetch-crl-cron',
                                     'fetch-crl-boot',
                                     'gums-client-cron'])
        elif utilities.rpm_installed('fetch-crl3'):
            expected_services = set(['fetch-crl3-cron',
                                     'fetch-crl3-boot',
                                     'gums-client-cron'])
        else:
            expected_services = set(['gums-client-cron'])

        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))

        config_file = get_test_config("misc/misc_gridmap.ini")
        configuration = ConfigParser.SafeConfigParser()
        configuration.read(config_file)

        settings = misc.MiscConfiguration(logger=global_logger)
        try:
            settings.parse_configuration(configuration)
        except Exception, e:
            self.fail("Received exception while parsing configuration: %s" % e)
        services = settings.enabled_services()
        if utilities.rpm_installed('fetch-crl'):
            expected_services = set(['fetch-crl-cron',
                                     'fetch-crl-boot',
                                     'edg-mkgridmap'])
        elif utilities.rpm_installed('fetch-crl3'):
            expected_services = set(['fetch-crl3-cron',
                                     'fetch-crl3-boot',
                                     'edg-mkgridmap'])
        else:
            expected_services = set(['edg-mkgridmap'])

        self.assertEqual(services, expected_services,
                         "List of enabled services incorrect, " +
                         "got %s but expected %s" % (services, expected_services))


    def _test_lcmaps(self, pre_file, post_file, errstring, *update_lcmaps_text_args):
        lcmaps_pre = open(get_test_config(pre_file)).read().strip()
        expected_lcmaps_post = open(get_test_config(post_file)).read().strip()

        settings = misc.MiscConfiguration(logger=global_logger)
        lcmaps_post = settings._update_lcmaps_text(lcmaps_pre, *update_lcmaps_text_args)

        diff = diff_strings(expected_lcmaps_post, lcmaps_post)

        self.assertEqual(diff, '',
                         "%s (diff: \n%s\n)" % (errstring, diff))


    def testLCMAPSGums(self):
        """
        Test to make sure lcmaps.db is properly modified for using GUMS
        """
        self._test_lcmaps('misc/lcmaps.db.fresh', 'misc/lcmaps.db.gums',
                          'lcmaps.db incorrectly updated for GUMS',
                          True, "testnode.testdomain")

    def testLCMAPSFreshGridmap(self):
        """
        Test to make sure a fresh lcmaps.db is properly modified for using a
        grid-mapfile.
        """
        self._test_lcmaps('misc/lcmaps.db.fresh', 'misc/lcmaps.db.gridmap1',
                          "Fresh lcmaps.db incorrectly updated for grid-mapfile",
                          False, "testnode.testdomain")

    def testLCMAPSModifiedGridmap(self):
        """
        Test to make sure a modified lcmaps.db is properly further modified
        for using a grid-mapfile.
        """
        self._test_lcmaps('misc/lcmaps.db.gums', 'misc/lcmaps.db.gridmap2',
                          "Modified lcmaps.db incorrectly updated for grid-mapfile",
                          False, "localhost")

    def testLCMAPSModifiedGUMS(self):
        """
        Test to make sure a modified lcmaps.db is properly further modified
        for using GUMS.
        """
        self._test_lcmaps('misc/lcmaps.db.gridmap1', 'misc/lcmaps.db.gums',
                          "Modified lcmaps.db incorrectly updated for GUMS",
                          True, "testnode.testdomain")

    def testLCMAPSMissingGridmap(self):
        """
        Test to make sure an lcmaps.db with a missing commented-out gridmapfile
        line gets a gridmapfile line added.
        """
        self._test_lcmaps('misc/lcmaps.db.missing_gridmap.pre', 'misc/lcmaps.db.missing_gridmap.post',
                          "lcmaps.db with missing gridmapfile line incorrectly updated",
                          False, "localhost")

    def testLCMAPSMissingGUMS(self):
        """
        Test to make sure an lcmaps.db with a missing commented-out gumsclient
        line gets a gumsclient line added.
        """

        self._test_lcmaps('misc/lcmaps.db.missing_gums.pre', 'misc/lcmaps.db.missing_gums.post',
                          "lcmaps.db with missing gumsclient line incorrectly updated",
                          True, "localhost")


def diff_strings(string1, string2):
    """
    Use diff(1) to get human-readable differences between two multi-line
    strings
    """
    tempfile1 = tempfile.NamedTemporaryFile()
    tempfile2 = tempfile.NamedTemporaryFile()

    tempfile1.write(string1.strip() + '\n')
    tempfile1.flush()

    tempfile2.write(string2.strip() + '\n')
    tempfile2.flush()

    diff_proc = subprocess.Popen(["diff", tempfile1.name, tempfile2.name], stdout=subprocess.PIPE)
    diff_out, _ = diff_proc.communicate()

    tempfile1.close()
    tempfile2.close()

    return diff_out.strip()

if __name__ == '__main__':
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    global_logger.addHandler(console)
    unittest.main()
