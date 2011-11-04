#!/usr/bin/python

""" Module to handle attributes and configuration for Gratia """

import os, sys, ConfigParser, re, tempfile

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
    self.logger.debug("GratiaConfiguration.__init__ started")

    self.config_section = 'Gratia'
    self.__mappings = {'probes' : 'probes',
                       'resource' : 'resource'}
    self.__optional = ['resource']
    # Dictionary holding probe settings, the probe's name is used as the key and the
    # server the probe should report to is the value.  
    self.enabled_probe_settings = {}
    self.__defaults = {}
    
    #defaults for itb and production use
    self.__itb_defaults = {'probes' : 'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    self.__production_defaults = {'probes' : 'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}     
    
    self.__job_managers = ['pbs', 'sge', 'lsf', 'condor']
    self.logger.debug("GratiaConfiguration.__init__ completed")
      
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict    
    """
    
    self.logger.debug('GratiaConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if (not configuration.has_section(self.config_section) and
        configfile.ce_config(configuration)):
      self.logger.debug('On CE and no Gratia section, auto-configuring gratia')    
      self.__auto_configure(configuration)
      self.logger.debug('GratiaConfiguration.parseConfiguration completed')    
      return True
    elif not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)
      self.logger.debug('Gratia.parseConfiguration completed')
      return
    
    if not self.setStatus(configuration):
      self.logger.debug('GratiaConfiguration.parseConfiguration completed')    
      return True
      
    # set the appropriate defaults if we're on a CE
    if configfile.ce_config(configuration):
      if configuration.has_option('Site Information', 'group'):
        group = configuration.get('Site Information', 'group')
      if group == 'OSG':
        self.__defaults = self.__production_defaults
      elif group == 'OSG-ITB':
        self.__defaults = self.__itb_defaults

    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = configfile.get_option(configuration, 
                                   self.config_section, 
                                   setting,
                                   optional_settings = self.__optional,
                                   defaults = self.__defaults)
      self.attributes[setting] = temp
      self.logger.debug("Got %s" % temp)
    
    if utilities.blank(self.attributes['probes']):
      return
    
    self.__parse_probes(self.attributes['probes'])
    self.logger.debug('GratiaConfiguration.parseConfiguration completed')
    
      
    
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug("GratiaConfiguration.configure started")

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug("GratiaConfiguration.configure completed")
      return True

    # disable all gratia services
    # if gratia is enabled, probes will get enabled below
    if not self.enabled:
      self.logger.debug("Not enabled")
      self.logger.debug("GratiaConfiguration.configure completed")
      return True
    
    if ('resource' not in self.attributes or
        utilities.blank(self.attributes['resource'])):
      if 'OSG_SITE_NAME' not in attributes:
        self.logger.error('No resource found for gratia reporting.' \
                          'You must give it using the resource option '\
                          'in the Gratia section or specify it in the '\
                          'Site Information section')
        return False
      else:
        self.attributes['resource'] = attributes['OSG_SITE_NAME']
         
    if ('OSG_HOSTNAME' not in attributes):
      self.logger.error('Hostname of this machine not specified.  Please ' \
                        'give this in the host_name option in the Site ' \
                        'Information section' )
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
                              self.attributes['resource'],
                              hostname)


    self.logger.debug("GratiaConfiguration.configure completed")
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
    self.logger.debug("GratiaConfiguration.checkAttributes started")

    if self.ignored:
      self.logger.debug("%s section ignored" % self.config_section)
      self.logger.debug("GratiaConfiguration.checkAttributes completed")
      return True
      
    if not self.enabled:
      self.logger.debug("Not enabled")
      self.logger.debug("GratiaConfiguration.checkAttributes completed")
      return True
    status = self.__check_servers()
    self.logger.debug("GratiaConfiguration.checkAttributes completed")
    return status

  def __subscriptionPresent(self, probe_file, probe_host):
    """
    Check probe file to see if subscription to the host is present
    """
    
    self.logger.debug("GratiaConfiguration.__subscriptionPresent started")
    elements = utilities.get_elements('ProbeConfiguration', probe_file)
    for element in elements:
      try:
        if (element.getAttribute('EnableProbe') == 1 and
            element.getAttribute('SOAPHost') == probe_host):
          self.logger.debug("Subscription for %s in %s found" % (probe_host, probe_file))
          return True
      # pylint: disable-msg=W0703
      except Exception, e:
        self.logger.debug("Exception checking element, %s" % e)

    self.logger.debug("GratiaConfiguration.__subscriptionPresent completed")
    return False
  
  def __makeSubscription(self, probe, probe_file, probe_host, site, hostname):
    """
    Check to see if a given probe has the correct subscription and if not 
    make it.
    """
    
    self.logger.debug("GratiaConfiguration.__makeSubscription started")
    
    if self.__subscriptionPresent(probe_file, probe_host):
      self.logger.debug("Subscription found %s probe, returning"  % (probe))
      self.logger.debug("GratiaConfiguration.__makeSubscription completed")
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
      buffer = re.sub(r'(\s*)EnableProbe\s*=.*',
                      r'\1EnableProbe="1"',
                      buffer,
                      1)
      for x in ['SSLHost', 'SOAPHost', 'SSLRegistrationHost', 'CollectorHost']:
        buffer = re.sub(r'(\s*)' + x + '\s*=.*',
                        r'\1' + x + '="' + probe_host + '"',
                        buffer,
                        1)  

      if not utilities.atomic_write(probe_file, buffer):
        self.logger.error("Error while configuring gratia probes")
        raise exceptions.ConfigureError("Error configuring gratia")
    except IOError, OSError:
      self.logger.error("Error while configuring gratia probes")
      raise exceptions.ConfigureError("Error configuring gratia")

    self.logger.debug("GratiaConfiguration.__makeSubscription completed")
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
        self.logger.warning(self.metric_probe_deprecation)
      server = self.enabled_probe_settings[probe].split(':')[0]
      if not validation.valid_domain(server, True):
        err_mesg = "The server specified for probe %s does not " % probe
        err_mesg += "resolve: %s" % server
        self.logger.error(err_mesg)
        valid = False
      if server != self.enabled_probe_settings[probe]:
        port = self.enabled_probe_settings[probe].split(':')[1]
        try:
          temp = int(port)
          if temp < 0:
            raise ValueError()
        except ValueError:
          self.logger.error("The port specified for probe" \
                            " %s is not valid, either it "\
                            "is less than 0 or not an integer"  % probe)                        
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
      self.attributes['resource'] = resource      
    elif configuration.has_option('Site Information', 'site_name'):
      resource = configuration.get('Site Information', 'site_name')
      self.attributes['resource'] = resource      
    else:
      self.logger.error('No site_name or resource defined in Site ' \
                        'Information, this is required on a CE')
      raise exceptions.SettingError('In Site Information, ' \
                                    'site_name or resource needs to be set')

    if configuration.has_option('Site Information', 'group'):
      group = configuration.get('Site Information', 'group')
    else:
      self.logger.error('No group defined in Site Information, ' \
                        'this is required on a CE')
      raise exceptions.SettingError('In Site Information, ' \
                                    'group needs to be set')

    if group == 'OSG':
      probes =  self.__production_defaults['probes']
    elif group == 'OSG-ITB':
      probes = self.__itb_defaults['probes']
    else:
      raise exceptions.SettingError('In Site Information, group must be ' \
                                    'OSG or OSG-ITB')
    
    self.attributes['probes'] = probes
    self.__parse_probes(probes) 
    
    return True

    
