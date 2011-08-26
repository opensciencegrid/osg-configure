#!/usr/bin/env python

""" Module to handle attributes and configuration for RSV service """

import os
import re
import pwd
import sys
import ConfigParser

from configure_osg.modules import exceptions
from configure_osg.modules import utilities
from configure_osg.modules.configurationbase import BaseConfiguration

__all__ = ['RsvConfiguration']


class RsvConfiguration(BaseConfiguration):
  """Class to handle attributes and configuration related to osg-rsv services"""

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(RsvConfiguration, self).__init__(*args, **kwargs)    
    self.logger.debug('RsvConfiguration.__init__ started')    
    self.__mappings = {'enable_local_probes': 'enable_local_probes',
                       'gratia_probes' : 'gratia_probes',
                       'ce_hosts' : 'ce_hosts',
                       'gridftp_hosts' : 'gridftp_hosts',
                       'gridftp_dir' : 'gridftp_dir',
                       'gums_hosts' : 'gums_hosts',
                       'srm_hosts' : 'srm_hosts',
                       'srm_dir' : 'srm_dir',
                       'srm_webservice_path' : 'srm_webservice_path',
                       'service_cert' : 'service_cert',
                       'service_key' : 'service_key',
                       'service_proxy' : 'service_proxy',
                       'user_proxy' : 'user_proxy',
                       'enable_gratia' : 'enable_gratia',
                       'gratia_collector' : 'gratia_collector',
                       'enable_nagios' : 'enable_nagios',
                       'nagios_send_nsca' : 'nagios_send_nsca'}
    self.__defaults = {'enable_local_probes' : True,
                       'gratia_probes' : None,
                       'ce_hosts' : utilities.get_hostname(),
                       'gridftp_hosts': utilities.get_hostname(),
                       'gridftp_dir': '/tmp',
                       'gums_hosts' : utilities.get_hostname(),
                       'service_cert' : '/etc/grid-security/rsvcert.pem',
                       'service_key' : '/etc/grid-security/rsvkey.pem', 
                       'service_proxy' : '/tmp/rsvproxy',
                       # It would be nice to get this information from gratia.py instead
                       # of replicating it here but that is not currently easy.
                       'gratia_collector' : 'rsv.grid.iu.edu:8880',
                       'nagios_send_nsca' : False}
    self.__optional = ['gratia_probes',
                       'ce_hosts',
                       'gums_hosts',
                       'srm_hosts',
                       'srm_dir',
                       'srm_webservice_path',
                       'service_cert',
                       'service_key',
                       'service_proxy',
                       'user_proxy',
                       'gratia_collector',
                       'nagios_send_nsca']
    self.__booleans = ['enable_local_probes',
                       'enable_gratia',
                       'enable_nagios',
                       'nagios_send_nsca']

    self.__rsv_user = "rsv"
    self.__ce_hosts = []
    self.__gridftp_hosts = []
    self.__gums_hosts = []
    self.__srm_hosts = []
    self.__gratia_probes_2d = []
    self.__enable_rsv_downloads = False
    self.__meta = ConfigParser.RawConfigParser()
    self.config_section = "RSV"
    self.rsv_control = os.path.join('/', 'usr', 'bin', 'rsv-control')
    self.rsv_meta_dir = os.path.join('/', 'etc', 'rsv', 'meta', 'metrics')
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

      if not utilities.valid_boolean(configuration, self.config_section, option):
        mesg = "In %s section, %s needs to be set to True or False" % (self.config_section, option)
        self.logger.error(mesg)
        raise exceptions.ConfigureError(mesg)

      self.attributes[self.__mappings[option]] = configuration.getboolean(self.config_section, option)


    # check and warn if unknown options found 
    temp = utilities.get_set_membership(configuration.options(self.config_section),
                                        self.__mappings,
                                        configuration.defaults().keys())
    for option in temp:
      if option == 'enabled':
        continue
      self.logger.warning("Found unknown option [%s].%s" % (self.config_section, option))


    # Parse lists
    self.__ce_hosts = split_list(self.attributes[self.__mappings['ce_hosts']])
    self.__gums_hosts = split_list(self.attributes[self.__mappings['gums_hosts']])
    self.__srm_hosts = split_list(self.attributes[self.__mappings['srm_hosts']])

    # If the gridftp hosts are not defined then they default to the CE hosts
    if self.__mappings['gridftp_hosts'] in self.attributes:
      self.__gridftp_hosts = split_list(self.attributes[self.__mappings['gridftp_hosts']])
    else:
      self.__gridftp_hosts = self.__ce_hosts

    if self.__mappings['gratia_probes'] in self.attributes:
      self.__gratia_probes_2d = self.split_2d_list(self.attributes[self.__mappings['gratia_probes']])

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

    attributes_ok &= self.__check_auth_settings()

    # check hosts
    attributes_ok &= self.__validate_host_list(self.__ce_hosts, "ce_hosts")
    attributes_ok &= self.__validate_host_list(self.__gums_hosts, "gums_hosts")
    attributes_ok &= self.__validate_host_list(self.__srm_hosts, "srm_hosts")
    attributes_ok &= self.__check_gridftp_settings()

    # check Gratia list
    attributes_ok &= self.__check_gratia_settings()

    self.logger.debug('RsvConfiguration.checkAttributes completed')    
    return attributes_ok 

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.logger.debug('RsvConfiguration.configure started')    

    if self.ignored:
      self.logger.warning("%s configuration ignored" % self.config_section)
      self.logger.debug('RsvConfiguration.configure completed') 
      return True

    # disable configuration for now
    self.logger.debug('Not enabled, returning True')
    self.logger.debug('RsvConfiguration.configure completed')
    return True

    if not self.enabled:
      self.logger.debug('Not enabled, returning True')
      self.logger.debug('RsvConfiguration.configure completed') 
      return True

    # Slurp in all the meta files which will tell us what type of metrics
    # we have and if they are enabled by default.
    self.load_rsv_meta_files()

    # Reset always?

    # Log rotation?

    # Put proxy information into rsv.ini
    if not self.__configure_cert_info():
      return False
    
    # Enable consumers
    if not self.__configure_consumers():
      return False

    # Enable metrics
    #if not self.__configure_ce_metrics():
    #  return False

    # ...

    if not self.__configure_gratia_metrics():
      return False

    # Setup Apache?  I think this is done in the RPM

    gratia_collector = self.attributes[self.__mappings['gratia_collector']]
    arguments.append('--gratia-collector')
    arguments.append(gratia_collector)

    if self.attributes[self.__mappings['enable_local_probes']]:
      arguments.append('--local-metrics')

    arguments.extend(self.__get_gridftp_options())
    arguments.extend(self.__get_gums_options())

    arguments.extend(self.__get_srm_options())

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


  def moduleName(self):
    """Return a string with the name of the module"""
    return "RSV"

  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be configured separately"""
    return True  

  def parseSections(self):
    """Returns the sections from the configuration file that this module handles"""
    return [self.config_section]


  def __check_gridftp_settings(self):
    """
    Check gridftp settings and make sure they are valid
    """

    status_check = self.__validate_host_list(self.__gridftp_hosts, "gridftp_hosts")

    if utilities.blank(self.attributes[self.__mappings['gridftp_dir']]):
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("Invalid gridftp_dir given: %s" %
                        self.attributes[self.__mappings['gridftp_dir']])
      status_check = False

    return status_check 

  def __check_auth_settings(self):
    """ Check authorization/certificate settings and make sure that they are valid """

    check_value = True

    # Do not allow both the service cert settings and proxy settings
    if ((self.attributes[self.__mappings['service_cert']] or
         self.attributes[self.__mappings['service_key']]  or
         self.attributes[self.__mappings['service_proxy']])
        and
        (self.attributes[self.__mappings['user_proxy']])):
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("You cannot specify user_proxy with any of (service_cert, service_key, service_proxy).  They are mutually exclusive options.")
      check_value = False

    # Make sure that either a service cert or user cert is selected
    if not ((self.attributes[self.__mappings['service_cert']] and
             self.attributes[self.__mappings['service_key']] and
             self.attributes[self.__mappings['service_proxy']])
            or
            self.attributes[self.__mappings['user_proxy']]):
      self.logger.error("In %s section" % self.config_section)
      self.logger.error("You must specify either service_cert/service_key/service_proxy *or* user_proxy in order to provide credentials for RSV to run jobs")
      check_value = False

    if self.attributes[self.__mappings['service_cert']]:
      value = self.attributes[self.__mappings['service_cert']]
      if utilities.blank(value) or not utilities.valid_file(value):
        self.logger.warning("In %s section" % self.config_section)
        self.logger.warning("service_cert must point to an existing file: %s" % value)
        check_value = False

      value = self.attributes[self.__mappings['service_key']]
      if utilities.blank(value) or not utilities.valid_file(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("service_key must point to an existing file: %s" % value)
        check_value = False

      value = self.attributes[self.__mappings['service_proxy']]
      if utilities.blank(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("service_proxy must have a valid location: %s" % value)
        check_value = False

      value = os.path.dirname(self.attributes[self.__mappings['service_proxy']])
      if not utilities.valid_location(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("service_proxy must be located in a valid directory: %s" % value)
        check_value = False

    else:
      # if not using a service certificate, make sure that the proxy file exists
      value = self.attributes[self.__mappings['user_proxy']]
      if utilities.blank(value) or not utilities.valid_file(value):
        self.logger.error("In %s section" % self.config_section)
        self.logger.error("user_proxy does not point to an existing file: %s" % value)
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
    """ Check to see if gratia settings are valid """

    valid_probes = ['condor',
                    'gridftp-transfer',
                    'hadoop-transfer',
                    'lsf',
                    'metric',
                    'pbs',
                    'sge']

    status_check = True
    for list in self.__gratia_probes_2d:
      for probe in list:
        if probe not in valid_probes:
          status_check = False
          err_mesg =  "In %s section, gratia_probes setting:" % self.config_section
          err_mesg += "Probe %s is not a valid probe, " % probe
          err_mesg += "valid probes consist of %s" % " ".join(valid_probes)
          self.logger.error(err_mesg)

    return status_check

  def __configure_gratia_metrics(self):
    """
    Enable Gratia metrics
    """

    if not self.__gratia_probes_2d:
      self.logger.debug("Skipping Gratia metric configuration because gratia_probes_2d is empty")
      return True

    if not self.__ce_hosts:
      self.logger.debug("Skipping Gratia metric configuration because ce_hosts is empty")
      return True

    num_ces = len(self.__ce_hosts)
    num_gratia = len(self.__gratia_probes_2d)
    if num_ces != num_gratia and num_gratia != 1:
      self.logger.error("The number of CE hosts does not match the number of Gratia host definitions")
      self.logger.error("Number of CE hosts: %s" % num_ces)
      self.logger.error("Number of Gratia host definitions: %2" % num_gratia)
      self.logger.error("They must match, or you must have only one Gratia host definition (which will be used for all hosts")
      return False

    i = 0
    for ce in self.__ce_hosts:
      gratia = None
      # If there is only one Gratia entry then we will use it for all defined CE hosts
      if num_gratia == 1:
        gratia = self.__gratia_probes_2d[0]
      else:
        gratia = self.__gratia_probes_2d[i]
        i += 1
      
      if not utilities.run_script([self.rsv_control, "--enable", "--host", ce, " ".join(gratia)]):
        self.logger.error("ERROR: Attempt to run command failed.  Command:\n\t%s" % cmd)
        return False

    return True
  
      
  def __validate_host_list(self, hosts, setting):
    """ Validate a list of hosts """
    ret = True
    for host in hosts:
      if host == "UNAVAILABLE":
        continue
      
      # Strip off the port
      if ':' in host:
        (hostname, port) = host.split(':')
      else:
        hostname = host
        port = False

      if not utilities.valid_domain(host):
        self.logger.error("Invalid domain in [%s].%s: %s" % (self.config_section, setting, host))
        ret = False

      if port and re.search('\D', port):
        self.logger.error("Invalid port in [%s].%s: %s" % (self.config_section, setting, host))

    return ret


  def __configure_cert_info(self):
    """ Configure certificate information """

    # Load in the existing configuration file
    config_file = os.path.join('/', 'etc', 'rsv', 'rsv.conf')
    config = ConfigParser.RawConfigParser()
    config.optionxform = str

    if os.path.exists(config_file):
      config.read(config_file)

    if not config.has_section('rsv'):
      config.add_section('rsv')

    # Set the appropriate options in the rsv.conf file
    if self.attributes[self.__mappings['service_cert']]:
      config.set('rsv', 'service-cert', self.attributes[self.__mappings['service_cert']])
      config.set('rsv', 'service-key', self.attributes[self.__mappings['service_key']])
      config.set('rsv', 'service-proxy', self.attributes[self.__mappings['service_proxy']])
    elif self.attributes[self.__mappings['user_proxy']]:
      config.set('rsv', 'proxy-file', self.attributes[self.__mappings['user_proxy']])

      # Remove these keys or they will override the proxy-file setting in rsv-control
      config.remove_option('rsv', 'service-cert')
      config.remove_option('rsv', 'service-key')
      config.remove_option('rsv', 'service-proxy')

    # Write back to disk
    config_fp = open(config_file, 'w')
    config.write(config_fp)
    config_fp.close()

    return True


  def __configure_consumers(self):
    """ Enable the appropriate consumers """

    # The current logic is:
    #  - we ALWAYS want the html-consumer if we are told to install consumers
    #  - we want the gratia-consumer if enable_gratia is True
    #  - we want the nagios-consumer if enable_nagios is True

    consumers = ["html-consumer"]

    if self.attributes[self.__mappings['enable_gratia']]:
      consumers.append("gratia-consumer")
      # TODO - set up Gratia directories?  Look at setup_gratia() in configure_rsv

    if self.attributes[self.__mappings['enable_nagios']]:
      consumers.append("nagios-consumer")
      self.__configure_nagios_files()

    # Rotate logs
    # /var/log/rsv/consumers/$consumer.log
    # "$VDT_LOCATION/osg-rsv/logs/consumers/$consumer.output"

    consumer_list = " ".join(consumers)
    self.logger.debug("Enabling consumers: %s " % consumer_list)

    if utilities.run_script([self.rsv_control, "--enable", consumer_list]):
      return True
    else:
      return False


  def __configure_nagios_files(self):
    """ Store the nagios configuration """

    # The Nagios conf file contains a password so set it to mode 0400 owned by rsv
    pw_file = os.path.join('/', 'etc', 'rsv', 'rsv-nagios.conf')
    (uid,gid) = pwd.getpwnam(self.__rsv_user)[2:4]
    os.chown(pw_file, uid, gid)
    os.chmod(pw_file, 0400)
    
    # Add the configuration file 
    nagios_conf_file = os.path.join('/', 'etc', 'rsv', 'consumers', 'nagios-consumer.conf')
    config = ConfigParser.RawConfigParser()
    config.optionxform = str
    
    if os.path.exists(nagios_conf_file):
      config.read(nagios_conf_file)
      
    if not config.has_section('nagios-consumer'):
      config.add_section('nagios-consumer')

    args = "--conf-file %s" % pw_file
    if self.attributes[self.__mappings['nagios_send_nsca']]:
      args += " --send-nsca"

    config.set("nagios-consumer", "args", args)
    
    config_fp = open(nagios_conf_file, 'w')
    config.write(config_fp)
    config_fp.close()

    return


  def load_rsv_meta_files(self):
    """ All the RSV meta files are in INI format.  Pull them in so that we know what
    metrics to enable """

    files = os.listdir(self.rsv_meta_dir)

    for file in files:
      if re.search('\.meta$', file):
        self.__meta.read(os.path.join(self.rsv_meta_dir, file))

    return

  def split_2d_list(self, list):
    """ Split a comma/whitespace separated list of list of items.
    Each list needs to be enclosed in parentheses and separated by whitespace and/or a comma.
    Parentheses are optional if only one list is supplied.
    
    Valid examples include:
    (1,2,3),(4,5)
    1,2,3,4,5
    (1,2), (4) , (5,6)  (8),    # comma at end is ok, comma between lists is optional

    Invalid examples:
    (1,2,3), 4    # 4 needs to be in parentheses
    1,2,3, (4,5)  # 1,2,3 needs to be parenthesized
    (1,2, (3, 4)  # missing a right parenthesis
    """

    if not list:
      return [[]]

    original_list = list

    # If there are no parentheses then just treat this like a normal comma-separated list
    # and return it as a 2-D array (with only one element in one direction)
    if not re.search("\(", list) and not re.search("\)", list):
      return [split_list(list)]

    # We want to grab parenthesized chunks
    pattern = re.compile("\s*\(([^()]+)\)\s*,?")
    array = []
    while 1:
      match = re.match(pattern, list)
      if not match:
        # If we don't have a match then we are either finished processing, or there is
        # a syntax error.  So if we have anything left in the string we will bail
        if re.search("\S", list):
          self.logger.error("ERROR: syntax error in parenthesized list")
          self.logger.error("ERROR: Supplied list:\n\t%s" % original_list)
          self.logger.error("ERROR: Leftover after parsing:\n\t%s" % list)
          return False
        else:
          return array

      array.append(split_list(match.group(1)))
    
      # Remove what we just matched so that we get the next chunk on the next iteration
      match_length = len(match.group(0))
      new_list = new_list[match_length:]

    # We shouldn't reach here, but just in case...
    return array


def split_list(list):
  """ Split a comma separated list of items """
  items = []
  for entry in list.split(','):
    items.append(entry.strip())
    
  return items

