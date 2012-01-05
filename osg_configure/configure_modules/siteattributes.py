#!/usr/bin/python

""" Module to handle attributes related to the site location and details """

import re, socket, logging

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
    self.log('SiteAttributes.__init__ started')
    self.options = {'group' : 
                      configfile.Option(name = 'group',
                                        default_value = 'OSG',
                                        mapping = 'OSG_GROUP'),
                    'host_name' : 
                      configfile.Option(name = 'host_name',
                                        mapping = 'OSG_HOSTNAME'),
                    'site_name' : 
                      configfile.Option(name = 'site_name',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_SITE_NAME'),
                    'sponsor' : 
                      configfile.Option(name = 'sponsor',
                                        mapping = 'OSG_SPONSOR'),
                    'site_policy' : 
                      configfile.Option(name = 'site_policy',
                                        mapping = 'OSG_SITE_INFO'),
                    'contact' : 
                      configfile.Option(name = 'contact',
                                        mapping = 'OSG_CONTACT_NAME'),
                    'email' : 
                      configfile.Option(name = 'email',
                                        mapping = 'OSG_CONTACT_EMAIL'),
                    'city' : 
                      configfile.Option(name = 'city',
                                        mapping = 'OSG_SITE_CITY'),
                    'country' : 
                      configfile.Option(name = 'country',
                                        mapping = 'OSG_SITE_COUNTRY'),
                    'longitude' : 
                      configfile.Option(name = 'longitude',
                                        type = float,
                                        mapping = 'OSG_SITE_LONGITUDE'),
                    'latitude' : 
                      configfile.Option(name = 'latitude',
                                        type = float,
                                        mapping = 'OSG_SITE_LATITUDE'),
                    'resource' : 
                      configfile.Option(name = 'resource',
                                        required = configfile.Option.OPTIONAL,
                                        mapping = 'OSG_SITE_NAME'),
                    'resource_group' : 
                      configfile.Option(name = 'resource_group',
                                        required = configfile.Option.OPTIONAL)}
    
    self.config_section = "Site Information"
    self.enabled = True
    self.log('SiteAttributes.__init__ completed')
        
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('SiteAttributes.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)    
      self.log('SiteAttributes.parseConfiguration completed')
      return
    
    for option in self.options.values():
      self.log("Getting value for %s" % option.name)
      configfile.get_option(configuration,
                            self.config_section, 
                            option)
      self.log("Got %s" % option.value)
 

    # check and warn if unknown options found    
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.options.keys(),
                                        configuration.defaults().keys())
    for option in temp:
      self.log("Found unknown option",
               option = option, 
               section = self.config_section,
               level = logging.WARNING)
    self.log('SiteAttributes.parseConfiguration completed')

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('SiteAttributes.checkAttributes started')
    attributes_ok = True
    
    if not self.enabled:
      self.log('Not enabled, returning True')
      self.log('SiteAttributes.checkAttributes completed')    
      return attributes_ok


        
    # OSG_GROUP must be either OSG or OSG-ITB
    if self.options['group'].value not in ('OSG', 'OSG-ITB'):
      self.log("The group setting must be either OSG or OSG-ITB, got: %s" %
               self.options['group'].value,
               option = 'group',
               section = self.config_section,
               level = logging.ERROR)
      attributes_ok = False
    
    # host_name must be different from the default setting
    if self.options['host_name'].value == 'my.domain.name':      
      self.log("Setting left at default value: my.domain.name",
               option = 'host_name',
               section = self.config_section,
               level = logging.ERROR)
      attributes_ok = False
    
    # host_name must be a valid dns name, check this by getting it's ip adddress
    if not validation.valid_domain(self.options['host_name'].value, True):
      self.log("hostname %s can't be resolved" % self.options['host_name'],
               option = 'host_name',
               section = self.config_section,
               level = logging.ERROR)
      attributes_ok = False

    # site_name or resource/resource_group must be specified not both
    if (not utilities.blank(self.options['site_name'].value) and
        (not utilities.blank(self.options['resource'].value) or
         not utilities.blank(self.options['resource_group'].value))):
      self.log("In section '%s', site_name and resource or " \
               "resource_group given at the same time, you should "\
               "use just the resource and resource_group settings.",
               level = logging.WARNING)
    
    
    if  self.options['latitude'].value > 90 or self.options['latitude'].value < -90:
      self.log("Latitude must be between -90 and 90, got %s" % 
                self.options['latitude'].value,
               section = self.config_section,
               option = 'latitude',
               level = logging.ERROR)    
      attributes_ok = False
  
    if  self.options['longitude'].value > 180 or self.options['longitude'].value < -180:
      self.log("Longitude must be between -180 and 180, got %s" % 
                self.options['longitude'].value,
               section = self.config_section,
               option = 'longitude',
               level = logging.ERROR)    
      attributes_ok = False

  
    # make sure that the email address is different from the default value
    if self.options['email'] == 'foo@my.domain':
      self.log("The email setting must be changed from the default",
               section = self.config_section,
               option = 'email',
               level = logging.ERROR)
      attributes_ok = False
      
    # make sure the email address has the correct format and that the domain portion is
    # resolvable    
    if not validation.valid_email(self.options['email'].value):
      self.log("Invalid email address in site information: %s" % 
               self.options['email'].value,
               section = self.config_section,
               option = 'email',
               level = logging.ERROR)
      attributes_ok = False
    else:
      match = re.match('(?:[a-zA-Z\-_+0-9.]+)@([a-zA-Z0-9_\-]+(?:\.[a-zA-Z0-9_\-]+)+)', 
                     self.options['email'].value)
      try:
        socket.gethostbyname(match.group(1))
      except socket.herror:
        self.log("Can't resolve domain in  email: %s" % self.options['email'].value,
                 section = self.config_section,
                 option = 'email',
                 level = logging.WARNING,
                 exception = True)
      except socket.gaierror:
        self.log("Can't resolve domain in  email: %s" % self.options['email'].value,
                 section = self.config_section,
                 option = 'email',
                 level = logging.WARNING,
                 exception = True)
        
    vo_list = self.options['sponsor'].value    
    percentage = 0
    vo_names = utilities.get_vos(None)
    if vo_names == []:
      map_file_present = False
    else:
      map_file_present = True
    vo_names.append('usatlas')   # usatlas is a valid vo name
    vo_names.append('uscms')   # uscms is a valid vo name
    vo_names.append('local')   # local is a valid vo name
    
    cap_vo_names = [vo.upper() for vo in vo_names]
    for vo in re.split('\s*,?\s*', vo_list):
      vo_name = vo.split(':')[0]
      if vo_name not in vo_names:
        if vo_name.upper() in cap_vo_names:
          self.log("VO name  %s has the wrong capitialization" % vo_name,
                   section = self.config_section,
                   option = 'sponsor',
                   level = logging.WARNING)
          vo_mesg = "Valid VO names are as follows:\n"
          for name in vo_names:
            vo_mesg +=  name + "\n"
          self.log(vo_mesg, level = logging.WARNING)
        else:
          if map_file_present:
            self.log("In %s section, problem with sponsor setting" % \
                                 self.config_section)
            self.log("VO name %s not found" % vo_name,
                   section = self.config_section,
                   option = 'sponsor',
                   level = logging.ERROR)
            vo_mesg = "Valid VO names are as follows:\n"
            for name in vo_names:
              vo_mesg +=  name + "\n"
            self.log(vo_mesg, level = logging.ERROR)
            attributes_ok = False
          else:
            self.log("VO name %s not found" % vo_name,
                     section = self.config_section,
                     option = 'sponsor',
                     level = logging.WARNING)
            self.log("/var/lib/osg/user-vo-map may be missing or empty " +
                     "please verify your gums or edg-mkgridmap " +
                     "settings are correct",
                     level = logging.WARNING)
            

      if len(vo.split(':')) == 1:
        percentage += 100
      elif len(vo.split(':')) == 2:
        vo_percentage = vo.split(':')[1]
        try:        
          percentage += int(vo_percentage)
        except ValueError:
          self.log("VO percentage (%s) in sponsor field (%s) not an integer" \
                   % (vo_percentage, vo),
                   section = self.config_section,
                   option = 'sponsor',
                   level = logging.ERROR,
                   exception = True)
          attributes_ok = False
      else:
        self.log("VO sponsor field is not formated correctly: %s" % vo,
                 section = self.config_section,
                 option = 'sponsor',
                 level = logging.ERROR)
        self.log("Sponsors should be given as sponsor:percentage "
                 "separated by a space or comma")
        
        
    if percentage != 100:
      self.log("VO percentages in sponsor field do not add up to 100, got %s"\
               % percentage,
               section = self.config_section,
               option = 'sponsor',
               level = logging.ERROR)
      attributes_ok = False
    self.log('SiteAttributes.checkAttributes completed')
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

  def getAttributes(self):
    """
    Get attributes for the osg attributes file using the dict in self.options

    Returns a dictionary of ATTRIBUTE => value mappings
    
    Need to override parent class method since two options may map to OSG_SITE_NAME
    """

    self.log("%s.getAttributes started" % self.__class__)

    attributes = BaseConfiguration.getAttributes(self)
    if attributes == {}:
      self.log("%s.getAttributes completed" % self.__class__)
      return attributes
    
    if ('OSG_SITE_NAME' in attributes and
        self.options['resource'].value is not None and
        not utilities.blank(self.options['resource'].value)):
      attributes['OSG_SITE_NAME'] = self.options['resource'].value
      self.log("%s.getAttributes completed" % self.__class__)
      return attributes
    
    self.log("%s.getAttributes completed" % self.__class__)
    return attributes
    