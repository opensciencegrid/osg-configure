#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, types

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import exceptions
from osg_configure.modules import xml_utilities

pathname = os.path.join('../scripts', 'osg-configure')

try:
    has_configure_osg = False
    fp = open(pathname, 'r')
    configure_osg = imp.load_module('test_module', fp, pathname, ('', '', 1))
    has_configure_osg = True
except:
    raise


class TestXMLUtilities(unittest.TestCase):

    def test_get_elements(self):
      """
      Check to make sure that get_elements properly gets information 
      from xml files
      """
      
      xml_file = 'test_files/subscriptions.xml'
      self.failUnlessEqual(xml_utilities.get_elements('foo', xml_file), 
                           [], 
                           'Got invalid elements')
      subscriptions = xml_utilities.get_elements('subscription', xml_file)
      self.failUnlessEqual(len(subscriptions), 
                           2, 
                           'Got wrong number of elements')
      tag_names = [x.tagName for x in subscriptions]
      self.failUnlessEqual(['subscription', 'subscription'], 
                           tag_names, 
                           'Got wrong elements')
      
