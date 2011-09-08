#!/usr/bin/python

""" Module to handle attributes related to the site location and details """

import re, socket

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['SiteAttributes']


class SiteAttributes(BaseConfiguration):
  """Class to handle attributes related to site information such as location and 
  contact information
  """
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(SiteAttributes, self).__init__(*args, **kwargs)
    self.logger.debug('SiteAttributes.__init__ started')
    self.__mappings = {'group': 'OSG_GROUP', 
                       'host_name': 'OSG_HOSTNAME',
                       'site_name': 'OSG_SITE_NAME',
                       'sponsor': 'OSG_SPONSOR',
                       'site_policy': 'OSG_SITE_INFO',
                       'contact': 'OSG_CONTACT_NAME',
                       'email': 'OSG_CONTACT_EMAIL',
                       'city': 'OSG_SITE_CITY',
                       'country': 'OSG_SITE_COUNTRY',
                       'longitude': 'OSG_SITE_LONGITUDE',
                       'latitude': 'OSG_SITE_LATITUDE',
                       'resource': 'OSG_SITE_NAME',
                       'resource_group': 'resource_group'}
    self.__defaults = {'group' : 'OSG'}
    self.__optional_settings = ['site_name',
                                'resource',
                                'resource_group']
    self.config_section = "Site Information"
    self.__enabled = True
    self.logger.debug('SiteAttributes.__init__ completed')
        
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.logger.debug('SiteAttributes.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.__enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)    
      self.logger.debug('SiteAttributes.parseConfiguration completed')
      return
    
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting,
                                   defaults = self.__defaults,
                                   optional_settings = self.__optional_settings)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)
 
    # site_name or resource/resource_group must be specified not both
    if (configuration.has_option(self.config_section, 'site_name') and
        (configuration.has_option(self.config_section, 'resource') or
         configuration.has_option(self.config_section, 'resource_group'))):
      self.logger.warn("In section '%s', site_name and resource or " \
                       "resource_group given at the same time, you should "\
                       "use just the resource and resource_group settings.")
    if configuration.has_option(self.config_section, 'resource'):
      resource = configuration.get(self.config_section, 'resource')
      if self.attributes['OSG_SITE_NAME'] != resource:
        self.attributes['OSG_SITE_NAME'] = resource

    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))   
    self.logger.debug('SiteAttributes.parseConfiguration completed')

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.logger.debug('SiteAttributes.checkAttributes started')
    attributes_ok = True
    
    if not self.__enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('SiteAttributes.checkAttributes completed')    
      return attributes_ok

    # Make sure all settings are present
    for setting in self.__mappings:
      if self.__mappings[setting] not in self.attributes:
        self.logger.error("Missing setting for %s", self.__mappings[setting])
        attributes_ok = False
        
    # OSG_GROUP must be either OSG or OSG-ITB
    if self.attributes['OSG_GROUP'] not in ('OSG', 'OSG-ITB'):
      self.logger.error("The group setting must be either OSG or OSG-ITB, got: %s" %
                        self.attributes['OSG_GROUP'])
      attributes_ok = False
    
    # OSG_HOSTNAME must be different from the default setting
    if self.attributes['OSG_HOSTNAME'] == 'my.domain.name':      
      self.logger.error("In %s section, hostname %s set to default my.domain.name" % \
                        (self.config_section, self.attributes['OSG_HOSTNAME']))
      self.logger.error("Check to make sure that localhost in the " +
                        "Default section has been changed")
      attributes_ok = False
    
    # OSG_HOSTNAME must be a valid dns name, check this by getting it's ip adddress
    if not validation.valid_domain(self.attributes['OSG_HOSTNAME'], True):
      self.logger.error("In %s section, hostname %s can't be resolved" % \
                        (self.config_section, self.attributes['OSG_HOSTNAME']))
      attributes_ok = False
    
    try:
      temp = float(self.attributes['OSG_SITE_LATITUDE'])
      if temp > 90 or temp < -90:
        self.logger.error("In %s section, problem with latitude setting" % self.config_section)
        self.logger.error("Latitude must be between -90 and 90, got %s" % 
                          self.attributes['OSG_SITE_LATITUDE'])    
        attributes_ok = False
    except ValueError:
      self.logger.error("In %s section, problem with latitude setting" % self.config_section)
      self.logger.error("Latitude must be a number, got %s" % 
                        self.attributes['OSG_SITE_LATITUDE'])
      attributes_ok = False
  
    try:
      temp = float(self.attributes['OSG_SITE_LONGITUDE'])
      if temp > 180 or temp < -180:
        self.logger.error("In %s section, problem with longitude setting" % self.config_section)
        self.logger.error("Longitude must be between -180 and 180, got %s" % 
                          self.attributes['OSG_SITE_LONGITUDE'])
        attributes_ok = False
    except ValueError:
      self.logger.error("In %s section, problem with longitude setting" % self.config_section)
      self.logger.error("Longitude must be a number, got %s" % 
                        self.attributes['OSG_SITE_LONGITUDE'])
      attributes_ok = False
  
    # make sure that the email address is different from the default value
    if self.attributes['OSG_CONTACT_EMAIL'] == 'foo@my.domain':
      self.logger.error("In %s section, problem with email setting" % self.config_section)
      self.logger.error("The email setting must be changed from the default")
      self.logger.error("Make sure that the admin_email setting in the Default " +
                        "section has been changed from foo@my.domain.")
      attributes_ok = False
      
    # make sure the email address has the correct format and that the domain portion is
    # resolvable    
    match = re.match('(?:[a-zA-Z\-_+0-9.]+)@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)+)', 
                     self.attributes['OSG_CONTACT_EMAIL'])
    if not validation.valid_email(self.attributes['OSG_CONTACT_EMAIL']):
      self.logger.error("In %s section, problem with email setting" % self.config_section)
      self.logger.error("Invalid email address in site information: %s" % 
                        self.attributes['OSG_CONTACT_EMAIL'])
      attributes_ok = False
    else:
      try:
        socket.gethostbyname(match.group(1))
      except socket.herror, exception:
        self.logger.warning("In %s section, problem with email setting" % self.config_section)
        self.logger.warning("Can't resolve domain in contact email: %s" % exception)
      except socket.gaierror, exception:
        self.logger.warning("In %s section, problem with email setting" % self.config_section)
        self.logger.warning("Can't resolve domain in contact email: %s" % exception)
        
    vo_list = self.attributes[self.__mappings['sponsor']]    
    percentage = 0
    vo_names = utilities.get_vos(None)
    if vo_names == []:
      map_file_present = False
    else:
      map_file_present = True
    vo_names.append('usatlas')   # local is a valid vo name
    vo_names.append('uscms')   # local is a valid vo name
    vo_names.append('local')   # local is a valid vo name
    
    cap_vo_names = [vo.upper() for vo in vo_names]
    for vo in re.split('\s*,?\s*', vo_list):
      vo_name = vo.split(':')[0]
      if vo_name not in vo_names:
        if vo_name.upper() in cap_vo_names:
          self.logger.warning("In %s section, problem with sponsor setting" % \
                              self.config_section)
          self.logger.warning("VO name  %s has the wrong capitialization" % vo_name)
          vo_mesg = "Valid VO names are as follows:\n"
          for name in vo_names:
            vo_mesg +=  name + "\n"
          self.logger.critical(vo_mesg)
        else:
          if map_file_present:
            self.logger.critical("In %s section, problem with sponsor setting" % \
                                 self.config_section)
            self.logger.critical("VO name %s not found" % vo_name)
            vo_mesg = "Valid VO names are as follows:\n"
            for name in vo_names:
              vo_mesg +=  name + "\n"
            self.logger.critical(vo_mesg)
            attributes_ok = False
          else:
            self.logger.warning("In %s section, problem with sponsor setting" % \
                                 self.config_section)
            self.logger.warning("VO name %s not found" % vo_name)
            self.logger.warning("osg-user-vo-map.txt may be missing or empty " +
                                "please verify your gums or edg-mkgridmap " +
                                "settings are correct")
            

      if len(vo.split(':')) == 1:
        percentage += 100
      elif len(vo.split(':')) == 2:
        vo_percentage = vo.split(':')[1]
        try:        
          percentage += int(vo_percentage)
        except ValueError:
          self.logger.critical("VO percentage (%s) in sponsor field (%s) not an integer" \
                               % (vo_percentage, vo))   
          attributes_ok = False
      else:
        self.logger.critical("VO sponsor field is not formated correctly: %s" % vo)
        self.logger.critical("sponsors should be given as sponsor:percentage "
                             "separated by a space or comma")
        
        
    if percentage != 100:
      self.logger.critical("VO percentages in sponsor field do not add up to 100, got %s"\
                            % percentage)
      attributes_ok = False
    self.logger.debug('SiteAttributes.checkAttributes completed')
    return attributes_ok 
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "SiteInformation"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
