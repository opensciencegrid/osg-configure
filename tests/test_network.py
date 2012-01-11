#!/usr/bin/env python

import os, imp, sys, unittest, ConfigParser, logging

# setup system library path
pathname = os.path.realpath('../')
sys.path.insert(0, pathname)

from osg_configure.modules import utilities
from osg_configure.modules import exceptions
from osg_configure.configure_modules import network

global_logger = logging.getLogger('test network configuration')
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
global_logger.addHandler(console)

class TestLocalSettings(unittest.TestCase):
  """
  Unit test class to test NetworkConfiguration class
  """
  
  def testParsing(self):
    """
    Test misc parsing
    """
    
    config_file = os.path.abspath("./configs/network/check_ok1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'source_range' : '2048,4096',
                 'port_range' : '9182,16384',
                 'source_state_file' : '/tmp/source_range',
                 'port_state_file' : '/tmp/port_range'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))
    
    config_file = os.path.abspath("./configs/network/check_ok2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'source_range' : '2048,4096',
                 'port_range' : '',
                 'source_state_file' : '/tmp/source_range',
                 'port_state_file' : ''}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))

    config_file = os.path.abspath("./configs/network/check_ok3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    options = settings.options
    variables = {'source_range' : '',
                 'port_range' : '9182,16384',
                 'source_state_file' : '',
                 'port_state_file' : '/tmp/port_range'}
    for var in variables:      
      self.failUnless(options.has_key(var), 
                      "Option %s missing" % var)
      self.failUnlessEqual(options[var].value, 
                           variables[var], 
                           "Wrong value obtained for %s, got %s but " \
                           "expected %s" % (var, 
                                            options[var].value, 
                                            variables[var]))
  

  def testMissingStateFile(self):
    """
    Test checks for missing state files
    """
    
    config_file = os.path.abspath("./configs/network/missing_source_state.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, missing source state file " % config_file +
                     "should have been flagged")


    config_file = os.path.abspath("./configs/network/missing_port_state.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, missing source state file " % config_file +
                     "should have been flagged")
    

  def testMissingRange(self):
    """
    Test checks for missing port ranges when state file is specified
    """
    
    config_file = os.path.abspath("./configs/network/missing_source_range.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, missing source range " % config_file +
                     "should have been flagged")


    config_file = os.path.abspath("./configs/network/missing_port_range.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, missing source port range " % config_file +
                     "should have been flagged")

  def testInvalidSourceRange(self):
    """
    Test checks for invalid source ranges (e.g. ab,28)
    """
    
    config_file = os.path.abspath("./configs/network/invalid_source_range1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, invalid source range " % config_file +
                     "should have been flagged")

    config_file = os.path.abspath("./configs/network/invalid_source_range2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, invalid source range " % config_file +
                     "should have been flagged")

    config_file = os.path.abspath("./configs/network/invalid_source_range3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, invalid source range " % config_file +
                     "should have been flagged")


  def testInvalidPortRange(self):
    """
    Test checks for invalid port range
    """

    config_file = os.path.abspath("./configs/network/invalid_port_range1.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, invalid port range " % config_file +
                     "should have been flagged")

    config_file = os.path.abspath("./configs/network/invalid_port_range2.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, invalid port range " % config_file +
                     "should have been flagged")

    config_file = os.path.abspath("./configs/network/invalid_port_range3.ini")
    configuration = ConfigParser.SafeConfigParser()
    configuration.read(config_file)

    settings = network.NetworkConfiguration(logger=global_logger)
    try:
      settings.parseConfiguration(configuration)
    except Exception, e:
      self.fail("Received exception while parsing configuration: %s" % e)
 

    self.assertFalse(setting.checkAttributes({}),
                     "In %s, invalid port range " % config_file +
                     "should have been flagged")
