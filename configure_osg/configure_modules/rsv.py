#!/usr/bin/env python

""" Module to handle attributes and configuration for rsv service """

import os
import sys

from configure_osg.modules import exceptions
from configure_osg.modules import utilities
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['RsvConfiguration']


class RsvConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to osg-rsv services"""

  report_to_deprecation = """INFO:
The 'report_to' config setting in the [RSV] section of your config.ini
file is no longer used.  All OSG installations will automatically report
to the GOC RSV collector.  If you want to send to a different collector
use the 'gratia_collector' option and specify the hostname:port of the
desired collector.  If you do not understand what to do then just remove
the 'report_to' setting in your config.ini file to use the default and
stop this message from displaying.""" 
  
  print_local_time_deprecation = """INFO:
The 'print_local_time' config setting in the [RSV] section of your config.ini
file is no longer supported.  All HTML consumers will now print local time
by default.  If you would like different behavior (e.g. your RSV HTML consumer
should print results using a different time zone) please submit an OSG ticket
about this issue.  This message is informational, not an error.  To prevent 
this message from showing again remove the print_local_time setting from your
config.ini file."""
      
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(RsvConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('RsvConfiguration.__init__ started')    
    self.__mappings = {'rsv_user': 'rsv_user', 
                       'enable_local_probes': 'enable_local_probes',
                       'enable_ce_probes': 'enable_ce_probes',
                       'gratia_probes' : 'gratia_probes',
                       'ce_hosts' : 'ce_hosts',
                       'enable_gridftp_probes' : 'enable_gridftp_probes',
                       'gridftp_hosts' : 'gridftp_hosts',
                       'gridftp_dir' : 'gridftp_dir',
                       'enable_gums_probes' : 'enable_gums_probes',
                       'gums_hosts' : 'gums_hosts',
                       'enable_srm_probes' : 'enable_srm_probes',
                       'srm_hosts' : 'srm_hosts',
                       'srm_dir' : 'srm_dir',
                       'srm_webservice_path' : 'srm_webservice_path',
                       'use_service_cert' : 'use_service_cert',
                       'rsv_cert_file' : 'rsv_cert_file',
                       'rsv_key_file' : 'rsv_cert_key',
                       'rsv_proxy_out_file' : 'rsv_proxy_out_file',
                       'proxy_file' : 'proxy_file',
                       'enable_gratia' : 'enable_gratia',
                       'print_local_time' : 'print_local_time',
                       'gratia_collector' : 'gratia_collector',
                       'report_to' : 'report_to',
                       'setup_rsv_nagios' : 'setup_rsv_nagios',
                       'rsv_nagios_conf_file' : 'rsv_nagios_conf_file',
                       'rsv_nagios_send_nsca' : 'rsv_nagios_send_nsca',
                       'setup_for_apache' : 'setup_for_apache',
                       'apache_config_file' : 'apache_config_file',
                       'verbose_output' : 'verbose_output',
                       'vo_name': 'vo_name'}
    self.__defaults = {'rsv_user' : 'rsvuser',
                       'enable_local_probes' : True,
                       'gratia_probes' : None,
                       'ce_hosts' : utilities.get_hostname(),
                       'gridftp_hosts': utilities.get_hostname(),
                       'gridftp_dir': '/tmp',
                       'gums_hosts' : utilities.get_hostname(),
                       'rsv_cert_file' : '/etc/grid-security/rsvcert.pem',
                       'rsv_key_file' : '/etc/grid-security/rsvkey.pem', 
                       'rsv_proxy_out_file' : '/tmp/rsvproxy',
                       'setup_for_apache' : True,
                       'verbose_output' : True,
                       # It would be nice to get this information from gratia.py instead
                       # of replicating it here but that is not currently easy.
                       'gratia_collector' : 'rsv.grid.iu.edu:8880',
                       'rsv_nagios_send_nesca' : False,
                       'rsv_nagios_conf_file' : os.path.join(utilities.get_vdt_location(),
                                                             'osg-rsv',
                                                             'etc',
                                                             'rsv-nagios.conf')}
    self.__optional = ['gratia_probes',
                       'ce_hosts',
                       'gums_hosts',
                       'srm_hosts',
                       'srm_dir',
                       'srm_webservice_path',
                       'rsv_cert_file',
                       'rsv_key_file',
                       'rsv_proxy_out_file',
                       'print_local_time',
                       'proxy_file',
                       'verbose_output',
                       'gratia_collector',
                       'report_to',
                       # enable_local_probes is optional because it was added mid-release
                       'enable_local_probes',
                       'apache_config_file',
                       'rsv_nagios_send_nsca',
                       'vo_name']                                                         
    self.__booleans = ['use_service_cert',
                       'enable_local_probes',
                       'enable_gratia',
                       'enable_ce_probes',
                       'enable_gridftp_probes',
                       'enable_gums_probes',
                       'enable_srm_probes',
                       'setup_rsv_nagios',
                       'rsv_nagios_send_nsca',
                       'setup_for_apache',
                       'verbose_output']
    self.__ce_hosts = []
    self.__gridftp_hosts = []
    self.__gums_hosts = []
    self.__srm_hosts = []
    self.__gratia_probes = []
    self.__enable_rsv_downloads = False
    self.config_section = "RSV"
    self.logger.debug('RsvConfiguration.__init__ completed')
    
  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or 
    SafeConfigParser object given by configuration and write recognized settings 
    to attributes dict
    """
    self.logger.debug('RsvConfiguration.parseConfiguration started')    

    self.checkConfig(configuration)
    
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.logger.debug("%s section not in config file" % self.config_section)    
      self.logger.debug('RsvConfiguration.parseConfiguration completed')    
      return True

    if not self.setStatus(configuration):
      self.logger.debug('RsvConfiguration.parseConfiguration completed')    
      return True
      
    for setting in self.__mappings:
      self.logger.debug("Getting value for %s" % setting)
      temp = utilities.get_option(configuration, 
                                  self.config_section, 
                                  setting, 
                                  self.__optional, 
                                  self.__defaults)
      self.attributes[self.__mappings[setting]] = temp
      self.logger.debug("Got %s" % temp)      

         
    # set boolean options
    self.logger.debug("Setting boolean options")    
    for option in self.__booleans:
      if not configuration.has_option(self.config_section, option):
        continue
      
      if not utilities.valid_boolean(configuration, 
                                     self.config_section, 
                                     option):
        mesg = "In %s section, %s needs to be set to True or False" \
                          % (self.config_section, option)
        self.logger.error(mesg)
        raise exceptions.ConfigureError(mesg)

      self.attributes[self.__mappings[option]] =  \
            configuration.getboolean(self.config_section, option)

    
    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())

    if self.attributes[self.__mappings['enable_ce_probes']]:
      for host in self.attributes[self.__mappings['ce_hosts']].split(','):        
        self.__ce_hosts.append(host.strip())
      
    if self.attributes[self.__mappings['enable_gridftp_probes']]:
      if self.__mappings['gridftp_hosts'] in self.attributes:
        for host in self.attributes[self.__mappings['gridftp_hosts']].split(','):
          self.__gridftp_hosts.append(host.strip())
      else:
        self.__gridftp_hosts = self.__ce_hosts
         
    if self.attributes[self.__mappings['enable_gums_probes']]:
      if self.__mappings['gums_hosts'] in self.attributes:
        for host in self.attributes[self.__mappings['gums_hosts']].split(','):
          self.__gums_hosts.append(host.strip())
      else:
        self.__gums_hosts = self.__ce_hosts
        
    if self.attributes[self.__mappings['enable_srm_probes']]:
      if self.__mappings['srm_hosts'] in self.attributes:
        for host in self.attributes[self.__mappings['srm_hosts']].split(','):
          self.__srm_hosts.append(host.strip())
      else:
        self.logger.warning("enable_srm_probes is True, but no srm_hosts are defined")

    if (self.__mappings['gratia_probes'] in self.attributes and
        not utilities.blank(self.attributes['gratia_probes'])): 
      for probe in self.attributes[self.__mappings['gratia_probes']].split(','):
        self.__gratia_probes.append(probe.strip())
        
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option %s in %s section" % 
                           (option, self.config_section))
    self.logger.debug('RsvConfiguration.parseConfiguration completed')    

# pylint: disable-msg=W0613
  def checkAttributes(self, attributes):
    """
    Check attributes currently stored and make sure that they are consistent
    """
    
    self.logger.debug('RsvConfiguration.checkAttributes started')
    attributes_ok = True
    
    if not self.enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('RsvConfiguration.checkAttributes completed')    
      return attributes_ok

    if self.ignored:
      self.logger.debug('Ignored, returning True')
      self.logger.debug('RsvConfiguration.checkAttributes completed')    
      return attributes_ok
      
    attributes_ok = attributes_ok & self.__check_auth_settings()
        
    # check ce hosts
    if self.attributes[self.__mappings['enable_ce_probes']]:
      for host in self.__ce_hosts:
        if not utilities.valid_domain(host):
          self.logger.error("In %s section" % self.config_section)
          self.logger.error("Invalid domain in ce_hosts: %s" % host)
          attributes_ok = False

    # check gums hosts
    if self.attributes[self.__mappings['enable_gums_probes']]:
      for host in self.__gums_hosts:
        if not utilities.valid_domain(host):
          self.logger.error("In %s section" % self.config_section)
          self.logger.error("Invalid domain in gums_hosts: %s" % host)
          attributes_ok = False

    attributes_ok = attributes_ok & self.__check_gridftp_settings()
      
    attributes_ok = attributes_ok & self.__check_srm_settings()
    
    attributes_ok = attributes_ok & self.__check_gratia_settings()
    
    # check nagios info
    if self.attributes[self.__mappings['setup_rsv_nagios']]:
      if utilities.blank(self.attributes[self.__mappings['rsv_nagios_conf_file']]):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("Invalid rsv_nagios_conf_file must be given: %s" %
                          self.attributes[self.__mappings['rsv_nagios_conf_file']])
        attributes_ok = False

      if not utilities.valid_file(self.attributes[self.__mappings['rsv_nagios_conf_file']]):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("Invalid rsv_nagios_conf_file must be a file: %s" %
                          self.attributes[self.__mappings['rsv_nagios_conf_file']])
        attributes_ok = False
    
    self.logger.debug('RsvConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('RsvConfiguration.configure started')    

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('RsvConfiguration.configure completed') 
      return True

    if not self.enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('RsvConfiguration.configure completed') 
      return True

    arguments = ['--html-consumer', '--server', 'y', '--init', '--reset', ]

    gratia_collector = self.attributes[self.__mappings['gratia_collector']]
    arguments.append('--gratia-collector')
    arguments.append(gratia_collector)

    if self.attributes[self.__mappings['report_to']]:
      sys.stdout.write(self.report_to_deprecation + "\n")
      self.logger.warning(self.report_to_deprecation)

    if self.attributes[self.__mappings['enable_local_probes']]:
      arguments.append('--local-metrics')
      
    arguments.append('--user')
    arguments.append(self.attributes[self.__mappings['rsv_user']])
    
    arguments.extend(self.__get_ce_options())
    arguments.extend(self.__get_gridftp_options())
    arguments.extend(self.__get_gums_options())
    
    arguments.extend(self.__get_srm_options())

    arguments.extend(self.__get_gratia_options())
    
    if self.attributes[self.__mappings['enable_gratia']]:
      arguments.append('--gratia')
    
    if self.attributes[self.__mappings['setup_for_apache']]:
      arguments.append('--setup-for-apache')

      if self.attributes[self.__mappings['apache_config_file']]:
        arguments.append('--apache-conf-file')
        arguments.append(self.attributes[self.__mappings['apache_config_file']])

    arguments.extend(self.__get_nagios_options())
    
    arguments.extend(self.__get_auth_options())

    if (self.__mappings['vo_name'] in self.attributes and
        not utilities.blank(self.attributes[self.__mappings['vo_name']])):
      arguments.append('--vo-name')
      arguments.append(self.attributes[self.__mappings['vo_name']])

    if self.attributes[self.__mappings['print_local_time']]:
      sys.stdout.write(self.print_local_time_deprecation + "\n")
      self.logger.info(self.print_local_time_deprecation)

    self.logger.info("Running configure_rsv with: %s" % (" ".join(arguments)))

    if not utilities.configure_service('configure_rsv', arguments):
      self.logger.error("Error while configuring RSV")
      raise exceptions.ConfigureError("Error configuring RSV")

    self.logger.debug('Enabling condor-cron service')
    if not utilities.enable_service('condor-cron'):
      self.logger.error("Error while enabling condor-cron")
      raise exceptions.ConfigureError("Error configuring rsv")    
    self.logger.debug('RsvConfiguration.configure completed')
    return True
  
  def getAttributes(self):
    """Return settings"""
    # no RSV attributes for the osg-attributes.conf file
    self.logger.debug('RsvConfiguration.getAttributes started')    
    self.logger.debug('RsvConfiguration.getAttributes completed')    
    return {}

# pylint: disable-msg=W0613
  def generateConfigFile(self, attribute_list, config_file):
    """Take a list of (key, value) tuples in attribute_list and add the 
    appropriate configuration options to the config file"""
    # generate reverse mapping so that we can create the appropriate options
    self.logger.debug('RsvConfiguration.generateConfigFile started')    
    self.logger.debug('RsvConfiguration.generateConfigFile completed')    
    return config_file

    
  def moduleName(self):
    """Return a string with the name of the module"""
    return "RSV"
  
  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True  

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]
  
  def __check_srm_settings(self):
    """
    Check to see if srm settings are valid
    """
    
    if not self.attributes[self.__mappings['enable_srm_probes']]:
      return True
    
    status_check = True
    for host in self.__srm_hosts:
      if ':' in host:
        hostname = host.split(':')[0]
      else:
        hostname = host

      if not utilities.valid_domain(hostname):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("Invalid domain in srm_hosts: %s" % host)
        status_check = False

    return status_check
  
  def __check_gridftp_settings(self):
    """
    Check gridftp settings and make sure they are valid
    """
    
    if not self.attributes[self.__mappings['enable_gridftp_probes']]:
      return True
    
    status_check = True    
    for host in self.__gridftp_hosts:
      if not utilities.valid_domain(host):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("Invalid domain in gridftp_hosts: %s" % host)
        status_check = False
    
    if utilities.blank(self.attributes[self.__mappings['gridftp_dir']]):
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("Invalid gridftp_dir given: %s" %
                        self.attributes[self.__mappings['gridftp_dir']])
      status_check = False
    
    return status_check 
  
  def __check_auth_settings(self):
    """
    Check authorization/certificate settings and make sure that they
    are valid
    """

    check_value = True
    # check certificates
    if self.attributes[self.__mappings['use_service_cert']]:
      # cert, and key files must exist if using service cert 
      value = self.attributes[self.__mappings['rsv_cert_file']]
      if utilities.blank(value) or not utilities.valid_file(value):
        self.logger.warning("In %s section" % self.config_section)
        self.logger.warning("rsv_cert_file must point to an existing " \
                            "file: %s" % value)
        check_value = False

      value = self.attributes[self.__mappings['rsv_key_file']]
      if utilities.blank(value) or not utilities.valid_file(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("rsv_key_file must point to an existing " \
                          "file: %s" % value)
        check_value = False

      value = self.attributes[self.__mappings['rsv_proxy_out_file']]
      if utilities.blank(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("rsv_proxy_out_file must have a valid " \
                          "location: %s" % value)
        check_value = False
      
      value = os.path.dirname(value)
      if not utilities.valid_location(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("rsv_proxy_out_file must be located in a valid " \
                          "directory: %s" % value)
        check_value = False
      
    else:
      # if not using a service certificate, make sure that the proxy file exists
      value = self.attributes[self.__mappings['proxy_file']]
      if utilities.blank(value) or not utilities.valid_file(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("Using a user certificate (because use_service_cert = False) but proxy_file does not point to an existing file: %s" % value)
        check_value = False

    return check_value
  
  def __get_srm_options(self):
    """
    Return arguments used for configuring srm probes
    """
    
    arguments = []
    if not self.attributes[self.__mappings['enable_srm_probes']]:
      return []
    
    arguments.append('--srm-metrics')
    arguments.append('--srm-uri')
    arguments.append(",".join(self.__srm_hosts))        

    srm_dirs = []
    for value in self.attributes[self.__mappings['srm_dir']].split(','):
      srm_dirs.append(value.strip())

    if len(self.__srm_hosts) != len(srm_dirs):
      self.logger.error("When enabling SRM metrics you must specify the same number of entries in the srm_dir variable as you have in the srm_hosts section.  There are %i host entries and %i srm_dir entries." % (len(self.__srm_hosts), len(srm_dirs)))
      raise exceptions.ConfigureError("Failed to configure RSV")
                        
    arguments.append('--srm-dir')
    arguments.append(",".join(srm_dirs))

    if (self.__mappings['srm_webservice_path'] in self.attributes and
        not utilities.blank(self.attributes[self.__mappings['srm_webservice_path']])):
      srm_ws_paths = []
      for value in self.attributes[self.__mappings['srm_webservice_path']].split(','):
        srm_ws_paths.append(value.strip())

      if len(self.__srm_hosts) != len(srm_ws_paths):
        self.logger.error("If you set srm_webservice_path when enabling SRM metrics you must specify the same number of entries in the srm_webservice_path variable as you have in the srm_hosts section.  There are %i host entries and %i srm_webservice_path entries." % (len(self.__srm_hosts), len(srm_ws_paths)))
        raise exceptions.ConfigureError("Failed to configure RSV")
        
      arguments.append('--srm-webservice-path')
      arguments.append(",".join(srm_ws_paths))

    return arguments
    
  def __get_auth_options(self):
    """
    Return arguments for configuring authorization/certificate options
    """
    arguments = []
    if self.attributes[self.__mappings['use_service_cert']]:
      arguments.append('--use-rsv-cert')
      arguments.append('--rsv-cert-file')
      arguments.append(self.attributes[self.__mappings['rsv_cert_file']])
      arguments.append('--rsv-key-file')
      arguments.append(self.attributes[self.__mappings['rsv_key_file']])
      arguments.append('--rsv-proxy-out-file')
      arguments.append(self.attributes[self.__mappings['rsv_proxy_out_file']])
    else:
      arguments.append('--proxy')
      arguments.append(self.attributes[self.__mappings['proxy_file']])
    return arguments
  
  def __get_nagios_options(self):
    """
    Return arguments for configuring nagios rsv options
    """
    
    if not self.attributes[self.__mappings['setup_rsv_nagios']]:
      return []

    options = ['--setup-rsv-nagios',
               '--rsv-nagios-conf-file',
               self.attributes[self.__mappings['rsv_nagios_conf_file']]]

    if self.attributes[self.__mappings['rsv_nagios_send_nsca']]:
      options.append("--rsv-nagios-send-nsca")

    return options
    
  def __get_gridftp_options(self):
    """
    Return arguments for configuring gridftp rsv options
    """
    
    if not self.attributes[self.__mappings['enable_gridftp_probes']]:
      return []
    
    return ['--gridftp-metrics',
            '--gridftp-uri',
            ",".join(self.__gridftp_hosts),        
            '--gridftp-dir',
            self.attributes[self.__mappings['gridftp_dir']]]

  def __get_ce_options(self):
    """
    Return arguments for configuring ce rsv options
    """
      
    if not self.attributes[self.__mappings['enable_ce_probes']]:
      return []
    
    return ['--ce-metrics',
            '--ce-uri',
            ",".join(self.__ce_hosts)]        
    
  def __get_gums_options(self):
    """
    Return arguments for configuring rsv gums probes
    """

    if not self.attributes[self.__mappings['enable_gums_probes']]:
      return []
    
    return ['--gums-metrics',
            '--gums-uri',
            ",".join(self.__gums_hosts)]

  def __check_gratia_settings(self):
    """
    Check to see if gratia settings are valid
    """
    
    valid_probes = ['condor',
                    'gridftp-transfer',
                    'hadoop-transfer',
                    'lsf',
                    'metric',
                    'pbs',
                    'sge',
                    'managedfork']
    
    if (self.__mappings['gratia_probes'] not in self.attributes or
        utilities.blank(self.attributes['gratia_probes'])):
      return True
    
    status_check = True
    for probe in self.__gratia_probes:
      if probe not in valid_probes:
        status_check = False
        err_mesg =  "In %s section, gratia_probes setting:" % self.config_section
        err_mesg += "Probe %s is not a valid probe, " % probe
        err_mesg += "valid probes consist of %s" % " ".join(valid_probes)
        self.logger.error(err_mesg)

    return status_check
    
  def __get_gratia_options(self):
    """
    Return arguments for configuring rsv gums probes
    """

    if (self.__mappings['gratia_probes'] in self.attributes and
        utilities.blank(self.attributes['gratia_probes'])): 
      return []
    
    return ['--gratia-metrics',
            " ".join(self.__gratia_probes)]
