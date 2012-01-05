#!/usr/bin/python

""" Module to handle attributes related to the sge jobmanager configuration """

import ConfigParser, os, re, types, logging

from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules import exceptions
from osg_configure.modules.jobmanagerbase import JobManagerConfiguration

__all__ = ['SGEConfiguration']


class SGEConfiguration(JobManagerConfiguration):
  """Class to handle attributes related to sge job manager configuration"""

  SGE_CONFIG_FILE = '/etc/grid-services/available/jobmanager-sge'
  GRAM_CONFIG_FILE = '/etc/globus/globus-pbs.conf'
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(SGEConfiguration, self).__init__(*args, **kwargs)
    self.log('SGEConfiguration.__init__ started') 
    # option information
    self.options = {'sge_root' : 
                      configfile.Option(name = 'sge_root',
                                        mapping = 'OSG_SGE_ROOT'),
                    'sge_cell' : 
                      configfile.Option(name = 'sge_CELL',
                                        mapping = 'OSG_SGE_CELL'),
                    'job_contact' : 
                      configfile.Option(name = 'job_contact',
                                        mapping = 'OSG_JOB_CONTACT'),
                    'util_contact' : 
                      configfile.Option(name = 'util_contact',
                                        mapping = 'OSG_UTIL_CONTACT'),
                    'seg_enabled' : 
                      configfile.Option(name = 'seg_enabled',
                                        required = configfile.Option.OPTIONAL,
                                        type = bool,
                                        default_value = False),
                    'accept_limited' : 
                      configfile.Option(name = 'accept_limited',
                                        required = configfile.Option.OPTIONAL,
                                        type = bool,
                                        default_value = False)}               
    self.__set_default = True
    self.config_section = "SGE"
    self.log('SGEConfiguration.__init__ completed')    
      
  def parseConfiguration(self, configuration):
    """Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """
    self.log('SGEConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section):
      self.log('SGE section not found in config file')
      self.log('SGEConfiguration.parseConfiguration completed')    
      return
    
    if not self.setStatus(configuration):
      self.log('SGEConfiguration.parseConfiguration completed')    
      return True
       
    for option in self.options.values():
      self.log("Getting value for %s" % option.name)
      configfile.get_option(configuration, 
                            self.config_section, 
                            option)
      self.log("Got %s" % option.value)
        
    # fill in values for sge_location and home
    self.options['job_manager'] = configfile.Option(name = 'job_manager',
                                                    value = 'SGE',
                                                    mapping = 'OSG_JOB_MANAGER')
    self.options['home'] = configfile.Option(name = 'job_manager_home',
                                             value = self.options['sge_root'].value,
                                             mapping = 'OSG_JOB_MANAGER_HOME')
    self.options['osg_sge_location'] = configfile.Option(name = 'osg_sge_location',
                                                         value = self.options['sge_root'].value,
                                                         mapping = 'OSG_SGE_LOCATION')
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.options.keys(),
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.log("Found unknown option",
               option = option, 
               section = self.config_section,
               level = logging.WARNING)

    # used to see if we need to enable the default fork manager, if we don't 
    # find the managed fork service enabled, set the default manager to fork
    # needed since the managed fork section could be removed after managed fork
    # was enabled 
    if (configuration.has_section('Managed Fork') and
        configuration.has_option('Managed Fork', 'enabled') and
        configuration.getboolean('Managed Fork', 'enabled')):
      self.__set_default = False
   
    self.log('SGEConfiguration.parseConfiguration completed')    
  
# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """Check attributes currently stored and make sure that they are consistent"""
    self.log('SGEConfiguration.checkAttributes started')    
    attributes_ok = True
    if not self.enabled:
      self.log('SGE not enabled, returning True')
      self.log('SGEConfiguration.checkAttributes completed')    
      return attributes_ok
    
    if self.ignored:
      self.log('Ignored, returning True')
      self.log('SGEConfiguration.checkAttributes completed')    
      return attributes_ok

    # make sure locations exist
    if not validation.valid_location(self.options['sge_root'].value):
      attributes_ok = False
      self.log("Non-existent location given: %s" % 
                          (self.options['sge_root'].value),
                option = 'sge_root',
                section = self.config_section,
                level = logging.ERROR)

    settings_file = os.path.join(self.options['sge_root'].value,
                                 self.options['sge_cell'].value, 
                                 'common', 
                                 'settings.sh')
    
    if not validation.valid_file(settings_file):
      attributes_ok = False
      self.log("$SGE_ROOT/$SGE_CELL/common/settings.sh not present: %s" % 
                          settings_file,
                option = 'sge_cell',
                section = self.config_section,
                level = logging.ERROR)

    if not self.validContact(self.options['job_contact'].value, 
                             'sge'):
      attributes_ok = False
      self.log("Invalid job contact: %s" % 
                         (self.options['job_contact'].value),
               option = 'job_contact',
               section = self.config_section,
               level = logging.ERROR)
      
    if not self.validContact(self.options['util_contact'].value, 
                             'sge'):
      attributes_ok = False
      self.log("Invalid util contact: %s" % 
                        (self.options['util_contact'].value),
               option = 'util_contact',
               section = self.config_section,
               level = logging.ERROR)

    if self.options['seg_enabled'].value:
      if (self.options['log_directory'].value is None or
          not validation.valid_directory(self.options['log_directory'].value)):
        mesg = "%s is not a valid directory location " % self.options['log_directory'].value
        mesg += "for sge log files"
        self.log(mesg, 
                 section = self.config_section,
                 option = 'log_directory',
                 level = logging.ERROR)
      
    self.log('SGEConfiguration.checkAttributes completed')    
    return attributes_ok 
  
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('SGEConfiguration.configure started')

    if not self.enabled:
      self.log('SGE not enabled, returning True')    
      self.log('SGEConfiguration.configure completed')    
      return True

    if self.ignored:
      self.log("%s configuration ignored" % self.config_section, 
               level = logging.WARNING)
      self.log('SGEConfiguration.configure completed')    
      return True

    # The accept_limited argument was added for Steve Timm.  We are not adding
    # it to the default config.ini template because we do not think it is
    # useful to a wider audience.
    # See VDT RT ticket 7757 for more information.
    if self.options['accept_limited'].value:
      if not self.enable_accept_limited(SGEConfiguration.SGE_CONFIG_FILE):
        self.log('Error writing to ' + SGEConfiguration.SGE_CONFIG_FILE, 
                 level = logging.ERROR)
        self.log('SGEConfiguration.configure completed')
        return False
    else:
      if not self.disable_accept_limited(SGEConfiguration.SGE_CONFIG_FILE):
        self.log('Error writing to ' + SGEConfiguration.SGE_CONFIG_FILE, 
                 level = logging.ERROR)
        self.log('SGEConfiguration.configure completed')
        return False

    if not self.setupGramConfig():
      self.log('Error writing to ' + SGEConfiguration.GRAM_CONFIG_FILE,
               level = logging.ERROR)
      return False

    if self.__set_default:
      self.log('Configuring gatekeeper to use regular fork service')
      self.set_default_jobmanager('fork')

    if self.options['seg_enabled'].value:
      self.enable_seg('sge', SGEConfiguration.SGE_CONFIG_FILE)
      #TODO: do other SEG configuration
    else:
      self.disable_seg(SGEConfiguration.SGE_CONFIG_FILE)
      #TODO: do other SEG configuration

    # TODO: do other globus job manager configuration, e.g. paths etc.s      

    self.log('SGEConfiguration.configure started')    
    return True
  
  def moduleName(self):
    """Return a string with the name of the module"""
    return "SGE"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True
  
  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]

  def setupGramConfig(self):
    """
    Populate the gram config file with correct values
    
    Returns True if successful, False otherwise
    """    
    buffer = open(SGEConfiguration.GRAM_CONFIG_FILE).read()
    bin_location = os.path.join(self.options['sge_location'].value,
                                'bin',
                                'qsub')
    if validation.valid_file(bin_location):
      (buffer, count) = re.subn('^qsub=.*$',
                                "qsub=\"%s\"" % bin_location,
                                buffer,
                                1)
      if count == 0:
        buffer = "qsub=\"%s\"\n" % bin_location + buffer
    bin_location = os.path.join(self.options['sge_location'].value,
                                'bin',
                                'qstat')
    if validation.valid_file(bin_location):
      (buffer, count) = re.subn('^qstat=.*$',
                                "qstat=\"%s\"" % bin_location,
                                buffer,
                                1)
      if count == 0:
        buffer = "qstat=\"%s\"\n" % bin_location + buffer
    bin_location = os.path.join(self.options['sge_location'].value,
                                'bin',
                                'qdel')
    if validation.valid_file(bin_location):
      (buffer, count) = re.subn('^qdel=.*$',
                                "qdel=\"%s\"" % bin_location,
                                buffer,
                                1)
      if count == 0:
        buffer = "qdel=\"%s\"\n" % bin_location + buffer
    
    new_setting = "sge_cell=\"%s\"" % self.options['sge_cell'].value
    (buffer, count) = re.subn('^sge_cell=.*$',
                              new_setting,
                              buffer,
                              1)
    if count == 0:
      buffer = new_setting + "\n" + buffer
    
    new_setting = "sge_root=\"%s\"" % self.options['sge_root'].value
    (buffer, count) = re.subn('^sge_root=.*$',
                              new_setting,
                              buffer,
                              1)
    if count == 0:
      buffer = new_setting + "\n" + buffer

    if self.options['seg_enabled'].value:
      new_setting = "log_path=\"%s\"" % self.options['log_directory'].value
      (buffer, count) = re.subn('^sge_root=.*$',
                                new_setting,
                                buffer,
                                1)
      if count == 0:
        buffer = new_setting + "\n" + buffer
    
    if not utilities.atomic_write(SGEConfiguration.GRAM_CONFIG_FILE, buffer):
      return False
