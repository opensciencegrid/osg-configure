""" Module to handle attributes and configuration for Gratia """

import os
import re
import sys
import logging
import subprocess

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation
from osg_configure.modules import configfile
from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.configure_modules.condor import CondorConfiguration
from osg_configure.configure_modules.sge import SGEConfiguration
from osg_configure.configure_modules.slurm import SlurmConfiguration

__all__ = ['GratiaConfiguration']


GRATIA_CONFIG_FILES = {
    'condor': '/etc/gratia/condor/ProbeConfig',
    'sge':    '/etc/gratia/sge/ProbeConfig',
    'lsf':    '/etc/gratia/pbs-lsf/urCollector.conf',
    'pbs':    '/etc/gratia/pbs-lsf/urCollector.conf',
    'slurm':  '/etc/gratia/slurm/ProbeConfig'
}

CE_PROBE_RPMS = ['gratia-probe-condor', 'gratia-probe-gram', 'gratia-probe-pbs-lsf', 'gratia-probe-sge',
                 'gratia-probe-slurm']


def requirements_are_installed():
  return (utilities.gateway_installed() and
          utilities.any_rpms_installed(CE_PROBE_RPMS))


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
    self.options = {'probes':
                    configfile.Option(name='probes',
                                      default_value=''),
                    'resource':
                    configfile.Option(name='resource',
                                      default_value='',
                                      required=configfile.Option.OPTIONAL)}

    # Dictionary holding probe settings, the probe's name is used as the key and the
    # server the probe should report to is the value.
    self.enabled_probe_settings = {}

    # defaults for itb and production use
    self.__itb_defaults = {'probes':
                           'jobmanager:gratia-osg-itb.opensciencegrid.org:80'}
    self.__production_defaults = {'probes':
                                  'jobmanager:gratia-osg-prod.opensciencegrid.org:80'}

    self.__job_managers = ['pbs', 'sge', 'lsf', 'condor', 'slurm']
    self.__probe_config = {}
    self.grid_group = 'OSG'

    self.log("GratiaConfiguration.__init__ completed")

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser 
    object given by configuration and write recognized settings to attributes 
    dict    
    """

    self.log('GratiaConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if (not configuration.has_section(self.config_section) and requirements_are_installed()):
      self.log('CE probes installed but no Gratia section, auto-configuring gratia')
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
    if requirements_are_installed():
      if configuration.has_option('Site Information', 'group'):
        self.grid_group = configuration.get('Site Information', 'group')

      if self.grid_group == 'OSG':
        self.options['probes'].default_value = \
            self.__production_defaults['probes']
      elif self.grid_group == 'OSG-ITB':
        self.options['probes'].default_value = \
            self.__itb_defaults['probes']

      # grab configuration information for various jobmanagers
      probes = self.getInstalledProbes()
      for probe in probes:
        if probe == 'condor':
          self.__probe_config['condor'] = {'condor_location':
                                           CondorConfiguration.getCondorLocation(configuration),
                                           'condor_config':
                                           CondorConfiguration.getCondorConfig(configuration)}
        elif probe == 'pbs':
          if BaseConfiguration.sectionDisabled(configuration, 'PBS'):
            # if the PBS jobmanager is disabled, the CE is probably using LSF
            # in any case, setting up the pbs gratia probe is not useful
            continue
          log_option = configfile.Option(name='log_directory',
                                         required=configfile.Option.OPTIONAL,
                                         default_value='')
          configfile.get_option(configuration, 'PBS', log_option)
          self.__probe_config['pbs'] = {'log_directory': log_option.value}

          accounting_log_option = configfile.Option(name='accounting_log_directory',
                                                    required=configfile.Option.OPTIONAL,
                                                    default_value='')
          configfile.get_option(configuration, 'PBS', accounting_log_option)
          self.__probe_config['pbs'] = {'accounting_log_directory': accounting_log_option.value}
        elif probe == 'lsf':
          if BaseConfiguration.sectionDisabled(configuration, 'LSF'):
            # if the LSF jobmanager is disabled, the CE is probably using PBS
            # in any case, setting up the pbs gratia probe is not useful
            continue
          lsf_location = configfile.Option(name='lsf_location',
                                           default_value='/usr/bin')
          configfile.get_option(configuration, 'LSF', lsf_location)
          self.__probe_config['lsf'] = {'lsf_location': lsf_location.value}

          log_option = configfile.Option(name='log_directory',
                                         required=configfile.Option.OPTIONAL,
                                         default_value='')
          configfile.get_option(configuration, 'LSF', log_option)
          self.__probe_config['lsf']['log_directory'] = log_option.value
        elif probe == 'sge':
          if BaseConfiguration.sectionDisabled(configuration, 'SGE'):
            # if section is disabled then the following code won't work
            # since the parseConfiguration will short circuit, so
            # give a warning and then move on
            self.log("Skipping SGE gratia probe configuration since SGE is disabled",
                     level=logging.WARNING)
            continue
          sge_config = SGEConfiguration(logger=self.logger)
          sge_config.parseConfiguration(configuration)
          self.__probe_config['sge'] = {'sge_accounting_file': sge_config.getAccountingFile()}
        elif probe == 'slurm':
          if BaseConfiguration.sectionDisabled(configuration, 'SLURM'):
            # if section is disabled then the following code won't work
            # since the parseConfiguration will short circuit, so
            # give a warning and then move on
            self.log("Skipping Slurm gratia probe configuration since Slurm is disabled",
                     level=logging.WARNING)
            continue
          slurm_config = SlurmConfiguration(logger=self.logger)
          slurm_config.parseConfiguration(configuration)
          self.__probe_config['slurm'] = {'db_host': slurm_config.getDBHost(),
                                          'db_port': slurm_config.getDBPort(),
                                          'db_user': slurm_config.getDBUser(),
                                          'db_pass': slurm_config.getDBPass(),
                                          'db_name': slurm_config.getDBName(),
                                          'cluster': slurm_config.getSlurmCluster(),
                                          'location': slurm_config.getLocation()}


    self.getOptions(configuration,
                    ignore_options=['itb-jobmanager-gratia',
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
               level=logging.WARNING)
      self.log("GratiaConfiguration.configure completed")
      return True

    # disable all gratia services
    # if gratia is enabled, probes will get enabled below
    if not self.enabled:
      self.log("Not enabled")
      self.log("GratiaConfiguration.configure completed")
      return True

    if utilities.blank(self.options['resource'].value):
      if 'OSG_SITE_NAME' not in attributes:
        self.log('No resource found for gratia reporting. You must give it '
                 'using the resource option in the Gratia section or specify '
                 'it in the Site Information section',
                 level=logging.ERROR)
        self.log("GratiaConfiguration.configure completed")
        return False
      else:
        self.options['resource'].value = attributes['OSG_SITE_NAME']

    if 'OSG_HOSTNAME' not in attributes:
      self.log('Hostname of this machine not specified. Please give this '
               'in the host_name option in the Site Information section',
               level=logging.ERROR)
      self.log("GratiaConfiguration.configure completed")
      return False

    hostname = attributes['OSG_HOSTNAME']
    probe_list = self.getInstalledProbes()
    for probe in probe_list:
      if probe in self.__job_managers:
        if probe not in self.__probe_config:
          # Probe is installed but we don't have configuration for it
          # might be due to pbs-lsf probe sharing or relevant job
          # manager is not shared
          continue

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
      if probe == 'condor':
        self.__configureCondorProbe()
      elif probe == 'pbs':
        self.__configurePBSProbe()
      elif probe == 'lsf':
        self.__configureLSFProbe()
      elif probe == 'sge':
        self.__configureSGEProbe()
      elif probe == 'slurm':
        self.__configureSLURMProbe()


    self.log("GratiaConfiguration.configure completed")
    return True

# pylint: disable-msg=R0201
  @staticmethod
  def getInstalledProbes():
    """
    Check for probes that have been installed and return a list of these probes installed
    """

    probes = {}
    probe_list = os.listdir('/etc/gratia/')
    for probe in probe_list:
      if probe.lower() == 'common':
        # the common directory isn't a probe
        continue
      elif probe.lower() == 'pbs-lsf' and os.path.isfile('/etc/gratia/pbs-lsf/ProbeConfig'):
        probes['pbs'] = '/etc/gratia/pbs-lsf/ProbeConfig'
        probes['lsf'] = '/etc/gratia/pbs-lsf/ProbeConfig'
        continue
      # Chech the config file before adding the probe                                                                                           
      probePath = os.path.join('/etc/gratia',
                              probe,
                              'ProbeConfig')
      if os.path.isfile(probePath):
        probes[probe] = probePath
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
    status &= self.__verify_gratia_dirs()
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
      self.log("Subscription found %s probe, returning" % probe)
      self.log("GratiaConfiguration.__makeSubscription completed")
      return True

    if probe == 'gridftp':
      probe = 'gridftp-transfer'

    try:
      buf = open(probe_file).read()
      buf = re.sub(r'(\s*)ProbeName\s*=.*',
                   r'\1ProbeName="' + "%s:%s" % (probe, hostname) + '"',
                   buf,
                   1)
      buf = re.sub(r'(\s*)SiteName\s*=.*',
                   r'\1SiteName="' + site + '"',
                   buf,
                   1)
      buf = re.sub(r'(\s*)Grid\s*=.*',
                   r'\1Grid="' + self.grid_group + '"',
                   buf,
                   1)
      buf = re.sub(r'(\s*)EnableProbe\s*=.*',
                   r'\1EnableProbe="1"',
                   buf,
                   1)
      for var in ['SSLHost', 'SOAPHost', 'SSLRegistrationHost', 'CollectorHost']:
        buf = re.sub(r'(\s*)' + var + r'\s*=.*',
                     r'\1' + var + '="' + probe_host + '"',
                     buf,
                     1)

      if not utilities.atomic_write(probe_file, buf, mode=420):
        self.log("Error while configuring gratia probes: " +
                 "can't write to %s" % probe_file,
                 level=logging.ERROR)
        raise exceptions.ConfigureError("Error configuring gratia")
    except(IOError, OSError):
      self.log("Error while configuring gratia probes",
               exception=True,
               level=logging.ERROR)
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
        self.log(self.metric_probe_deprecation, level=logging.WARNING)
      server = self.enabled_probe_settings[probe].split(':')[0]
      if not validation.valid_domain(server, True):
        err_mesg = "The server specified for probe %s does not " % probe
        err_mesg += "resolve: %s" % server
        self.log(err_mesg, level=logging.ERROR)
        valid = False
      if server != self.enabled_probe_settings[probe]:
        port = self.enabled_probe_settings[probe].split(':')[1]
        try:
          temp = int(port)
          if temp < 0:
            raise ValueError()
        except ValueError:
          self.log("The port specified for probe %s is not valid, either it "
                   "is less than 0 or not an integer" % probe,
                   exception=True,
                   level=logging.ERROR)
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
      self.log('No site_name or resource defined in Site Information, this'
               ' is required on a CE',
               level=logging.ERROR)
      raise exceptions.SettingError('In Site Information, '
                                    'site_name or resource needs to be set')

    if configuration.has_option('Site Information', 'group'):
      group = configuration.get('Site Information', 'group')
    else:
      self.log('No group defined in Site Information, this is required on a CE',
               level=logging.ERROR)
      raise exceptions.SettingError('In Site Information, group needs to be set')

    if group == 'OSG':
      probes = self.__production_defaults['probes']
    elif group == 'OSG-ITB':
      probes = self.__itb_defaults['probes']
    else:
      raise exceptions.SettingError('In Site Information, group must be '
                                    'OSG or OSG-ITB')

    self.options['probes'].value = probes
    self.__parse_probes(probes)

    return True

  def __configureCondorProbe(self):
    """
    Do condor probe specific configuration
    """

    config_location = GRATIA_CONFIG_FILES['condor']
    buf = file(config_location).read()
    settings = self.__probe_config['condor']
    buf = self.replaceSetting(buf, 'CondorLocation', settings['condor_location'])
    buf = self.replaceSetting(buf, 'CondorConfig', settings['condor_config'])
    if not utilities.atomic_write(config_location, buf):
      return False
    return True

  def __configurePBSProbe(self):
    """
    Do pbs probe specific configuration
    """
    if (self.__probe_config['pbs']['accounting_log_directory'] is None or
        self.__probe_config['pbs']['accounting_log_directory'] == ''):
      return True
    accounting_dir = self.__probe_config['pbs']['accounting_log_directory']
    if not validation.valid_directory(accounting_dir):
      self.log("PBS accounting log not present, PBS gratia probe not configured",
               level=logging.ERROR,
               option='accounting_log_directory',
               section='PBS')
      return True

    config_location = GRATIA_CONFIG_FILES['pbs']
    buf = file(config_location).read()
    buf = self.replaceSetting(buf, 'pbsAcctLogDir', accounting_dir, xml_file=False)
    buf = self.replaceSetting(buf, 'lrmsType', 'pbs', xml_file=False)
    if not utilities.atomic_write(config_location, buf):
      return False
    return True

  def __configureLSFProbe(self):
    """
    Do lsf probe specific configuration
    """
    if (self.__probe_config['lsf']['log_directory'] is None or
        self.__probe_config['lsf']['log_directory'] == ''):
      self.log("LSF accounting log directory not given, LSF gratia probe not configured",
               level=logging.ERROR,
               option='log_directory',
               section='LSF')
      return True
    log_directory = self.__probe_config['lsf']['log_directory']
    if not validation.valid_directory(log_directory):
      self.log("LSF accounting log not present, LSF gratia probe not configured",
               level=logging.ERROR,
               option='log_directory',
               section='LSF')
      return True
    config_location = GRATIA_CONFIG_FILES['lsf']
    buf = file(config_location).read()
    buf = self.replaceSetting(buf, 'lsfAcctLogDir', log_directory, xml_file=False)

    # setup lsfBinDir
    if (self.__probe_config['lsf']['lsf_location'] is None or
        self.__probe_config['lsf']['lsf_location'] == ''):
      self.log("LSF location not given, lsf gratia probe not configured",
               level=logging.ERROR,
               option='lsf_location',
               section='LSF')
      return True
    lsf_bin_dir = os.path.join(self.__probe_config['lsf']['lsf_location'], 'bin')
    buf = self.replaceSetting(buf, 'lsfBinDir', lsf_bin_dir, xml_file=False)
    buf = self.replaceSetting(buf, 'lrmsType', 'lsf', xml_file=False)
    if not utilities.atomic_write(config_location, buf):
      return False
    return True

  def __configureSGEProbe(self):
    """
    Do SGE probe specific configuration
    """
    accounting_path = self.__probe_config['sge']['sge_accounting_file']
    config_location = GRATIA_CONFIG_FILES['sge']
    buf = file(config_location).read()
    buf = self.replaceSetting(buf, 'SGEAccountingFile', accounting_path)
    if not utilities.atomic_write(config_location, buf):
      return False
    return True

  def __configureSLURMProbe(self):
    """
    Do SLURM probe specific configuration
    """
    config_location = GRATIA_CONFIG_FILES['slurm']
    buf = file(config_location).read()

    settings = self.__probe_config['slurm']
    if not validation.valid_file(settings['db_pass']):
      self.log("Slurm DB password file not present",
               level=logging.ERROR,
               option='db_pass',
               section='SLURM')
      return True

    buf = self.replaceSetting(buf, 'SlurmDbHost', settings['db_host'])
    buf = self.replaceSetting(buf, 'SlurmDbPort', settings['db_port'])
    buf = self.replaceSetting(buf, 'SlurmDbUser', settings['db_user'])
    buf = self.replaceSetting(buf, 'SlurmDbPasswordFile', settings['db_pass'])
    buf = self.replaceSetting(buf, 'SlurmDbName', settings['db_name'])
    buf = self.replaceSetting(buf, 'SlurmCluster', settings['cluster'])
    buf = self.replaceSetting(buf, 'SlurmLocation', settings['location'])

    if not utilities.atomic_write(config_location, buf):
      return False
    return True


  def __verify_gratia_dirs(self):
      """
      Verify that the condor per_job_history directory and the DataFolder
      directory are the same and warn if admin if the two don't match
      """

      valid = True
      if 'condor' not in self.__probe_config:
          # Don't need this for non-condor probes
          return valid
      # TODO Change to use utilities.get_condor_config_val (need to add more checking to that function first)
      condor_config_val_bin = os.path.join(self.__probe_config['condor']['condor_location'],
                                "bin",
                                "condor_config_val")
      if not os.path.exists(condor_config_val_bin):
        self.log("While checking gratia parameters: Unable to find condor_config_val binary (looked for %s).\n"
                 "In the [Condor] section of your configuration, set condor_location such that "
                 "(condor_location)/bin/condor_config_val is the location of the condor_config_val binary."
                 % condor_config_val_bin,
                 level=logging.ERROR)
        return False

      config_location = GRATIA_CONFIG_FILES['condor']
      contents = file(config_location).read()
      re_obj = re.compile(r'(?m)^\s*DataFolder\s*=(.*)\s*$')
      match = re_obj.search(contents)
      if match is not None:
        data_folder = match.group(1)
        data_folder = data_folder.strip('" \t')
        # PER_JOB_HISTORY_DIR comes from the schedd, so if condor's not
        # running, we can't get a value (SOFTWARE-1564)
        history_dir = self.__get_history_dir(condor_config_val_bin)
        if not history_dir:
          self.log("Could not verify DataFolder correctness: unable to get PER_JOB_HISTORY_DIR. "
                   "This may be caused by the condor schedd not running.", level=logging.WARNING)
        else:
          if not os.path.samefile(data_folder, history_dir):
            self.log("DataFolder setting in %s and condor PER_JOB_HISTORY_DIR %s "
                     "do not match, these settings must match!" % (config_location,
                                                                   history_dir),
                     level=logging.ERROR)
            valid = False

        # Per Gratia-126 DataFolder must end in / otherwise gratia won't find certinfo files
        if not data_folder.endswith('/'):
          self.log("DataFolder setting in %s must end in a /" % config_location,
                   level=logging.ERROR)
          valid = False

      return valid

  def __get_history_dir(self, condor_config_val_bin):
    cmd = [condor_config_val_bin, '-schedd', 'PER_JOB_HISTORY_DIR']
    try:
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      (history_dir, errtext) = process.communicate()
      if process.returncode != 0:
        self.log("While checking gratia parameters: %s failed. Output follows:\n%s" % (condor_config_val_bin,
                                                                                       errtext), level=logging.INFO)
        return None
    except OSError, err:
      self.log("While checking gratia parameters: Error running %s: %s" % (condor_config_val_bin, str(err)),
               level=logging.INFO)
      return None
    return history_dir.strip()

  @staticmethod
  def replaceSetting(buf, setting, value, xml_file=True):
    """
      Replace the first instance of the option within a string, adding
      the option if it's not present
      
      e.g.
      "a=b\n  setting=old_value" => "a=b\n setting=value"
      and
      "a=b\n " => "a=b\n setting=value"
      
      returns the string with the option string replaced/added 
    """
    re_obj = re.compile(r"^(\s*)%s\s*=.*$" % setting, re.MULTILINE)
    (new_buf, count) = re_obj.subn(r'\1%s="%s"' % (setting, value), buf, 1)
    if count == 0:
      if xml_file:
        new_buf = new_buf.replace('/>', "    %s=\"%s\"\n/>" % (setting, value))
      else:
        new_buf += "%s = \"%s\"\n" % (setting, value)
    return new_buf

  def enabledServices(self):
    """Return a list of  system services needed for module to work
    """

    if not self.enabled or self.ignored:
      return set()

    return set(['gratia-probes-cron'])
  

    
