#!/usr/bin/python

""" Module to handle attributes and configuration for Gratia """

import os, sys, ConfigParser, re, tempfile, logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['GratiaConfiguration']


class GratiaConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to gratia services"""

  metric_probe_deprecation = """WARNING:
The metric probe should no longer be configured using 'probes' option in the 
[Gratia] section. All OSG installations will automatically report to the GOC 
RSV collector.  If you want to send to a different collector use the 
'gratia_collector' option in the [RSV] section and specify the 
hostname:port of the desired collector.  If you do not understand what to 
do then just remove the metric probe specification in the 'probes' option 
in your config.ini file.""" 
  
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(GratiaConfiguration, self).__init__(*args, **kwargs)
    self.log("GratiaConfiguration.__init__ started")

    self.config_section = 'Gratia'
    self.options = {'probes' : 
                      configfile.Option(name = 'probes',
                                        default_value = ''),
                    'resource' : 
                      configfile.Option(name = 'resource',
                                        default_value = '',
                                        required = configfile.Option.OPTIONAL)}
    
    # Dictionary holding probe settings, the probe's name is used as the key and the
    # server the probe should report to is the value.  
    self.enabled_probe_settings = {}
    
    # defaults for itb and production use
    self.__itb_defaults = {'probes' : 
                            'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    self.__production_defaults = {'probes' : 
                                    'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}     
    
    self.__job_managers = ['pbs', 'sge', 'lsf', 'condor']
    self.log("GratiaConfiguration.__init__ completed")
    
    self.grid_group = 'OSG'
      
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser 
    object given by configuration and write recognized settings to attributes 
    dict    
    """
    
    self.log('GratiaConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if (not configuration.has_section(self.config_section) and
        utilities.ce_installed()):
      self.log('On CE and no Gratia section, auto-configuring gratia')    
      self.__auto_configure(configuration)
      self.log('GratiaConfiguration.parseConfiguration completed')    
      return True
    elif not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('Gratia.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.log('GratiaConfiguration.parseConfiguration completed')    
      return True
      
    # set the appropriate defaults if we're on a CE
    if utilities.ce_installed():
      if configuration.has_option('Site Information', 'group'):
        self.grid_group = configuration.get('Site Information', 'group')
        
      if self.grid_group == 'OSG':
        self.options['probes'].default_value = \
            self.__production_defaults['probes']
      elif self.grid_group == 'OSG-ITB':
        self.options['probes'].default_value = \
            self.__itb_defaults['probes']

    self.getOptions(configuration, 
                    ignore_options = ['itb-jobmanager-gratia',
                                      'itb-gridftp-gratia',
                                      'osg-jobmanager-gratia',
                                      'osg-gridftp-gratia',
                                      'enabled'])
    
    if utilities.blank(self.options['probes'].value):
      self.log('GratiaConfiguration.parseConfiguration completed')
      return
    
    self.__parse_probes(self.options['probes'].value)
    self.log('GratiaConfiguration.parseConfiguration completed')
    
      
    
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log("GratiaConfiguration.configure started")

    if self.ignored:
      self.log("%s configuration ignored" % self.config_section, 
               level = logging.WARNING)
      self.log("GratiaConfiguration.configure completed")
      return True

    # disable all gratia services
    # if gratia is enabled, probes will get enabled below
    if not self.enabled:
      self.log("Not enabled")
      self.log("GratiaConfiguration.configure completed")
      return True
    
    if (utilities.blank(self.options['resource'].value)):
      if 'OSG_SITE_NAME' not in attributes:
        self.log('No resource found for gratia reporting. You must give it '\
                 'using the resource option in the Gratia section or specify '\
                 'it in the Site Information section',
                 level = logging.ERROR)
        self.log("GratiaConfiguration.configure completed")
        return False
      else:
        self.options['resource'].value = attributes['OSG_SITE_NAME']
         
    if ('OSG_HOSTNAME' not in attributes):
      self.log('Hostname of this machine not specified. Please give this '\
               'in the host_name option in the Site Information section', 
               level = logging.ERROR)
      self.log("GratiaConfiguration.configure completed")
      return False
    
    hostname = attributes['OSG_HOSTNAME']
    probe_list = self.getInstalledProbes()
    for probe in probe_list:
      if probe in self.__job_managers:
        if 'jobmanager' in self.enabled_probe_settings:
          probe_host = self.enabled_probe_settings['jobmanager']
        else:
          continue
      else:
        if probe in self.enabled_probe_settings:
          probe_host = self.enabled_probe_settings[probe]
        else:
          continue
      self.__makeSubscription(probe, 
                              probe_list[probe], 
                              probe_host, 
                              self.options['resource'].value,
                              hostname)


    self.log("GratiaConfiguration.configure completed")
    return True

# pylint: disable-msg=R0201
  def getInstalledProbes(self):
    """Check for probes that have been installed and return a list of these probes installed"""
    
    probes = {}
    probe_list = os.listdir('/etc/gratia/')
    for probe in probe_list:
      if probe.lower() == 'common':
        # the common directory isn't a probe
        continue
      elif probe.lower() == 'pbs-lsf':
        probes['pbs'] = '/etc/gratia/pbs-lsf/ProbeConfig'
        probes['lsf'] = '/etc/gratia/pbs-lsf/ProbeConfig'
        continue
        
      probes[probe] = os.path.join('/etc/gratia',
                                   probe,
                                   'ProbeConfig')
            
    return probes

  # pylint: disable-msg=W0613  
  def checkAttributes(self, attributes):
    """Check configuration  and make sure things are setup correctly"""
    self.log("GratiaConfiguration.checkAttributes started")

    if self.ignored:
      self.log("%s section ignored" % self.config_section)
      self.log("GratiaConfiguration.checkAttributes completed")
      return True
      
    if not self.enabled:
      self.log("Not enabled")
      self.log("GratiaConfiguration.checkAttributes completed")
      return True
    status = self.__check_servers()
    self.log("GratiaConfiguration.checkAttributes completed")
    return status

  def __subscriptionPresent(self, probe_file, probe_host):
    """
    Check probe file to see if subscription to the host is present
    """
    
    self.log("GratiaConfiguration.__subscriptionPresent started")
    elements = utilities.get_elements('ProbeConfiguration', probe_file)
    for element in elements:
      try:
        if (element.getAttribute('EnableProbe') == 1 and
            element.getAttribute('SOAPHost') == probe_host):
          self.log("Subscription for %s in %s found" % (probe_host, probe_file))
          return True
      # pylint: disable-msg=W0703
      except Exception, e:
        self.log("Exception checking element, %s" % e)

    self.log("GratiaConfiguration.__subscriptionPresent completed")
    return False
  
  def __makeSubscription(self, probe, probe_file, probe_host, site, hostname):
    """
    Check to see if a given probe has the correct subscription and if not 
    make it.
    """
    
    self.log("GratiaConfiguration.__makeSubscription started")
    
    if self.__subscriptionPresent(probe_file, probe_host):
      self.log("Subscription found %s probe, returning"  % (probe))
      self.log("GratiaConfiguration.__makeSubscription completed")
      return True
    
    if probe == 'gridftp':
      probe = 'gridftp-transfer'
    
    try:  
      buffer = open(probe_file).read()
      buffer = re.sub(r'(\s*)ProbeName\s*=.*',
                      r'\1ProbeName="' + "%s:%s" % (probe, hostname) + '"',
                      buffer,
                      1)
      buffer = re.sub(r'(\s*)SiteName\s*=.*',
                      r'\1SiteName="' + site + '"',
                      buffer,
                      1)
      buffer = re.sub(r'(\s*)Grid\s*=.*',
                      r'\1Grid="' + self.grid_group + '"',
                      buffer,
                      1)
      buffer = re.sub(r'(\s*)EnableProbe\s*=.*',
                      r'\1EnableProbe="1"',
                      buffer,
                      1)
      for x in ['SSLHost', 'SOAPHost', 'SSLRegistrationHost', 'CollectorHost']:
        buffer = re.sub(r'(\s*)' + x + '\s*=.*',
                        r'\1' + x + '="' + probe_host + '"',
                        buffer,
                        1)  

      if not utilities.atomic_write(probe_file, buffer, mode=420):
        self.log("Error while configuring gratia probes: " +
                 "can't write to %s" % probe_file,
                 level = logging.ERROR)
        raise exceptions.ConfigureError("Error configuring gratia")
    except IOError, OSError:
      self.log("Error while configuring gratia probes",
               exception = True,
               level = logging.ERROR)
      raise exceptions.ConfigureError("Error configuring gratia")

    self.log("GratiaConfiguration.__makeSubscription completed")
    return True
    
    
  def moduleName(self):
    """Return a string with the name of the module"""
    return "Gratia"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return False
  
  def __check_servers(self):
    """
    Returns True or False depending whether the server_list is a valid list 
    of servers. 
    A valid list consists of host[:port] entries separated by commas, 
    e.g. server1.example.com,server2.example.com:2188
    """
    valid = True
    for probe in self.enabled_probe_settings:
      if probe == 'metric':
        sys.stdout.write(self.metric_probe_deprecation + "\n")
        self.log(self.metric_probe_deprecation, level = logging.WARNING)
      server = self.enabled_probe_settings[probe].split(':')[0]
      if not validation.valid_domain(server, True):
        err_mesg = "The server specified for probe %s does not " % probe
        err_mesg += "resolve: %s" % server
        self.log(err_mesg, level = logging.ERROR)
        valid = False
      if server != self.enabled_probe_settings[probe]:
        port = self.enabled_probe_settings[probe].split(':')[1]
        try:
          temp = int(port)
          if temp < 0:
            raise ValueError()
        except ValueError:
          self.log("The port specified for probe %s is not valid, either it "\
                   "is less than 0 or not an integer"  % probe,
                   exception = True,
                   level = logging.ERROR)                        
    return valid
  
  def __parse_probes(self, probes):
    """
    Parse a list of probes and set the list of enabled probes for this 
    configuration
    """
    
    for probe_entry in probes.split(','):
      tmp = probe_entry.split(':')    
      probe_name = tmp[0].strip()
      if probe_name == 'gridftp':
        probe_name = 'gridftp-transfer'
      if len(tmp[1:]) == 1:
        self.enabled_probe_settings[probe_name] = tmp[1]
      else :
        self.enabled_probe_settings[probe_name] = ':'.join(tmp[1:])
    
                     
  def __auto_configure(self, configuration):
    """
    Configure gratia for a ce which does not have the gratia section
    """
    self.enabled = True
    
    if configuration.has_option('Site Information', 'resource'):
      resource = configuration.get('Site Information', 'resource')
      self.options['resource'].value = resource      
    elif configuration.has_option('Site Information', 'site_name'):
      resource = configuration.get('Site Information', 'site_name')
      self.options['resource'].value = resource      
    else:
      self.log('No site_name or resource defined in Site Information, this'\
               ' is required on a CE',
               level = logging.ERROR)
      raise exceptions.SettingError('In Site Information, ' \
                                    'site_name or resource needs to be set')

    if configuration.has_option('Site Information', 'group'):
      group = configuration.get('Site Information', 'group')
    else:
      self.log('No group defined in Site Information, this is required on a CE',
               level = logging.ERROR)
      raise exceptions.SettingError('In Site Information, ' \
                                    'group needs to be set')

    if group == 'OSG':
      probes =  self.__production_defaults['probes']
    elif group == 'OSG-ITB':
      probes = self.__itb_defaults['probes']
    else:
      raise exceptions.SettingError('In Site Information, group must be ' \
                                    'OSG or OSG-ITB')
    
    self.options['probes'].value = probes
    self.__parse_probes(probes) 
    
    return True

    
