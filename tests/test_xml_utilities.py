"""Unit tests to test xml related functions"""

# pylint: disable=W0703
# pylint: disable=R0904

import os
import sys
import unittest
import imp


# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import xml_utilities
from osg_configure.modules.utilities import get_test_config

pathname = os.path.join('../scripts', 'osg-configure')
if not os.path.exists(pathname):
    pathname = os.path.join('/', 'usr', 'sbin', 'osg-configure')
    if not os.path.exists(pathname):
        raise Exception("Can't find osg-configure script")

try:
    has_configure_osg = False
    fp = open(pathname, 'r')
    configure_osg = imp.load_module('test_module', fp, pathname, ('', '', 1))
    has_configure_osg = True
except:
    raise Exception("Can't import osg-configure script")


class TestXMLUtilities(unittest.TestCase):
    """Unit test class to test functions in xml_utilities module"""

    def test_get_elements(self):
        """
        Check to make sure that get_elements properly gets information
        from xml files
        """

        xml_file = get_test_config('test_files/subscriptions.xml')
        self.assertEqual(xml_utilities.get_elements('foo', xml_file),
                         [],
                         'Got invalid elements')
        subscriptions = xml_utilities.get_elements('subscription', xml_file)
        self.assertEqual(len(subscriptions),
                         2,
                         'Got wrong number of elements')
        tag_names = [x.tagName for x in subscriptions]
        self.assertEqual(['subscription', 'subscription'],
                         tag_names,
                         'Got wrong elements')
