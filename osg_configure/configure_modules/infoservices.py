"""This module provides a class to handle attributes and configuration
 for OSG info services subscriptions"""

import re
import urlparse
import logging

from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import configfile
from osg_configure.modules import validation
from osg_configure.modules.configurationbase import BaseConfiguration

__all__ = ['InfoServicesConfiguration']

CE_COLLECTOR_ATTRIBUTES_FILE = '/etc/condor-ce/config.d/10-osg-attributes-generated.conf'
CE_COLLECTOR_CONFIG_FILE = '/etc/condor-ce/config.d/10-ce-collector-generated.conf'
HTCONDOR_CE_COLLECTOR_PORT = 9619

SERVICECERT_PATH = "/etc/grid-security/http/httpcert.pem"
SERVICEKEY_PATH = "/etc/grid-security/http/httpkey.pem"

# BATCH_SYSTEMS here is both the config sections for the batch systems
# and the values in the OSG_BatchSystems attribute since they are
# coincidentally the same. If they ever change, make a mapping.
BATCH_SYSTEMS = ['Condor', 'LSF', 'PBS', 'SGE', 'SLURM']

class InfoServicesConfiguration(BaseConfiguration):
  """
  Class to handle attributes and configuration related to
  miscellaneous services
  """

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(InfoServicesConfiguration, self).__init__(*args, **kwargs)
    self.log("InfoServicesConfiguration.__init__ started")
    # file location for xml file with info services subscriptions
    self.config_section = 'Info Services'
    self.options = {'ress_servers': configfile.Option(name = 'ress_servers',
                                                       default_value=''),
                    'bdii_servers': configfile.Option(name = 'bdii_servers',
                                                       default_value=''),
                    'ce_collectors': configfile.Option(name='ce_collectors',
                                                       default_value='',
                                                       required = configfile.Option.OPTIONAL)}
    self.__itb_defaults = {
      'ress_servers': 'https://osg-ress-4.fnal.gov:8443/ig/services/CEInfoCollector[OLD_CLASSAD]',
      'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],http://is2.grid.iu.edu:14001[RAW]',
      'ce_collectors': 'collector-itb.opensciencegrid.org:%d' % HTCONDOR_CE_COLLECTOR_PORT}
    self.__production_defaults = {
      'ress_servers': 'https://osg-ress-1.fnal.gov:8443/ig/services/CEInfoCollector[OLD_CLASSAD]',
      'bdii_servers': 'http://is1.grid.iu.edu:14001[RAW],http://is2.grid.iu.edu:14001[RAW]',
      'ce_collectors': 'collector1.opensciencegrid.org:%d,collector2.opensciencegrid.org:%d' % (
        HTCONDOR_CE_COLLECTOR_PORT, HTCONDOR_CE_COLLECTOR_PORT)}
    self.bdii_servers = {}
    self.ress_servers = {}
    self.copy_host_cert_for_service_cert = False

    self.ois_required_rpms_installed = utilities.gateway_installed() and utilities.rpm_installed('osg-info-services')

    # for htcondor-ce-info-services:
    self.ce_collectors = []
    self.ce_collector_required_rpms_installed = utilities.rpm_installed('htcondor-ce')
    self.osg_resource = ""
    self.osg_resource_group = ""
    self.enabled_batch_systems = []
    self.htcondor_gateway_enabled = None

    self.log("InfoServicesConfiguration.__init__ completed")

  def __set_default_servers(self, configuration):
    group = utilities.config_safe_get(configuration, 'Site Information', 'group')
    for key in ['ress_servers', 'bdii_servers', 'ce_collectors']:
      if group == 'OSG-ITB':
        self.options[key].default_value = self.__itb_defaults[key]
      else:
        self.options[key].default_value = self.__production_defaults[key]

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or SafeConfigParser object given
    by configuration and write recognized settings to attributes dict
    """

    self.log('InfoServicesConfiguration.parseConfiguration started')

    self.checkConfig(configuration)

    if not configuration.has_section(self.config_section) and self.ois_required_rpms_installed:
      self.log('Section missing and on a CE, autoconfiguring')
      self.__auto_configure(configuration)
      self.log('InfoServicesConfiguration.parseConfiguration completed')
      return True
    elif not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('InfoServicesConfiguration.parseConfiguration completed')
      return

    if not self.setStatus(configuration):
      self.log('InfoServicesConfiguration.parseConfiguration completed')
      return True

    self.__set_default_servers(configuration)

    self.getOptions(configuration,
                    ignore_options=['itb-ress-servers',
                                    'itb-bdii-servers',
                                    'osg-ress-servers',
                                    'osg-bdii-servers',
                                    'enabled'])

    self.ress_servers = self.__parse_servers(self.options['ress_servers'].value)
    self.bdii_servers = self.__parse_servers(self.options['bdii_servers'].value)
    self.ce_collectors = self.options['ce_collectors'].value.split(',')

    def csg(section, option):
      return utilities.config_safe_get(configuration, section, option, None)
    def csgbool(section, option):
      return utilities.config_safe_getboolean(configuration, section, option, False)

    # We get some values for HTCondor-CE from the Site Information section
    self.osg_resource = csg('Site Information', 'resource')
    self.osg_resource_group = csg('Site Information', 'resource_group')
    # and the enabled batch systems from their respective sections
    self.enabled_batch_systems = [bs for bs in BATCH_SYSTEMS if csgbool(bs, 'enabled')]

    self.copy_host_cert_for_service_cert = csgbool('Misc Services', 'copy_host_cert_for_service_certs')
    self.htcondor_gateway_enabled = csgbool('Gateway', 'htcondor_gateway_enabled')



# pylint: disable-msg=W0613
  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log("InfoServicesConfiguration.configure started")

    if self.ignored:
      self.log("%s configuration ignored" % self.config_section,
               level=logging.WARNING)
      self.log('InfoServicesConfiguration.configure completed')
      return True

    if not self.enabled:
      self.log("Not enabled")
      self.log("InfoServicesConfiguration.configure completed")
      return True

    if self.copy_host_cert_for_service_cert:
      if not self.create_missing_service_cert_key(SERVICECERT_PATH, SERVICEKEY_PATH, 'tomcat'):
        self.log("Could not create service cert/key", level=logging.ERROR)
        return False

    if self.ce_collector_required_rpms_installed and self.htcondor_gateway_enabled:
      self.__configure_ce_collector()

    self.log("InfoServicesConfiguration.configure completed")
    return True

  def checkAttributes(self, attributes):
    """Check configuration and make sure things are setup correctly"""
    self.log("InfoServicesConfiguration.checkAttributes started")

    if not self.enabled:
      self.log("Not enabled")
      self.log("InfoServicesConfiguration.checkAttributes completed")
      return True

    if self.ignored:
      self.log('Ignored, returning True')
      self.log("InfoServicesConfiguration.checkAttributes completed")
      return True

    valid = True
    self.log("Checking BDII subscriptions")
    for subscription in self.bdii_servers:
      valid &= self.__checkSubscription(subscription,
                                        self.bdii_servers[subscription])

    self.log("Checking ReSS subscriptions")
    for subscription in self.ress_servers:
      valid &= self.__checkSubscription(subscription,
                                        self.ress_servers[subscription])

    self.log("InfoServicesConfiguration.checkAttributes completed")
    return valid

  def moduleName(self):
    """Return a string with the name of the module"""
    return "Infoservices"

  def separatelyConfigurable(self):
    """Return a boolean that indicates whether this module can be
    configured separately"""
    return False

  def __checkSubscription(self, subscription, dialect):
    """
    Check a subscription and dialect to make sure it's valid, return True if
    that's the case, otherwise false.

    subscription must be a uri and dialect must be CLASSAD, RAW, or OLD_CLASSAD
    """

    valid = True
    # check for valid uri
    result = urlparse.urlsplit(subscription)
    if result[1] == '':
      self.log("Subscription must be a uri, got %s" % subscription,
               level=logging.ERROR)
      valid = False

    # check to see if host resolves
    server = result[1]
    if ':' in server:
      server = server.split(':')[0]
    if not validation.valid_domain(server, True):
      self.log("Host in subscription does not resolve: %s" % server,
               level=logging.ERROR)
      valid = False

    # check to make sure dialect is correct
    if dialect not in ('CLASSAD', 'RAW', 'OLD_CLASSAD'):
      self.log("Dialect for subscription %s is not valid: %s" % (server, dialect),
               level=logging.ERROR)
      valid = False
    return valid

  @classmethod
  def __parse_servers(cls, servers):
    """
    Take a list of servers and parse it into a list of
    (server, subscription_type) tuples
    """
    server_list = {}
    if servers.lower() == 'ignore':
      # if the server list is set to ignore, then don't use any servers
      # this allows cemon to be send ress information but not bdii or vice versa
      return server_list

    server_regex = re.compile(r'(.*)\[(.*)\]')
    for entry in servers.split(','):
      match = server_regex.match(entry)
      if match is None:
        raise exceptions.SettingError('Invalid subscription: %s' % entry)
      server_list[match.group(1).strip()] = match.group(2)
    return server_list

  def __auto_configure(self, configuration):
    """
    Method to configure cemon without any cemon section on a CE
    """

    self.enabled = True
    if configuration.has_option('Site Information', 'group'):
      group = configuration.get('Site Information', 'group')
    else:
      self.log('No group defined in Site Information, this is required on a CE',
               level=logging.ERROR)
      raise exceptions.SettingError('In Site Information, group needs to be set')
    if group == 'OSG':
      ress_servers = self.__production_defaults['ress_servers']
      bdii_servers = self.__production_defaults['bdii_servers']
    elif group == 'OSG-ITB':
      ress_servers = self.__itb_defaults['ress_servers']
      bdii_servers = self.__itb_defaults['bdii_servers']
    else:
      self.log('Group must be OSG or OSG-ITB',
               level=logging.ERROR)
      raise exceptions.SettingError('In Site Information, group needs to be OSG or OSG-ITB')

    self.options['ress_servers'].value = ress_servers
    self.options['bdii_servers'].value = bdii_servers
    self.ress_servers = self.__parse_servers(ress_servers)
    self.bdii_servers = self.__parse_servers(bdii_servers)

  def enabledServices(self):
    """
    Return a list of  system services needed for module to work
    """
    services = set()
    if self.ois_required_rpms_installed:
      services.add('osg-info-services')
    if self.ce_collector_required_rpms_installed and self.htcondor_gateway_enabled:
      services.add('condor-ce')
    return services

  def __configure_ce_collector(self):
    for filename, description, writer_func in [
      (CE_COLLECTOR_ATTRIBUTES_FILE, "attributes file", self.__write_ce_collector_attributes_file),
      (CE_COLLECTOR_CONFIG_FILE, "CE collector config file", self.__write_ce_collector_file)
    ]:
      if not writer_func(filename):
        self.log("Writing %s %r failed" % (description, filename),
                 level=logging.ERROR)
        return False

  def __write_ce_collector_attributes_file(self, attributes_file):
    """Write config file that contains the osg attributes for the
    CE-Collector to advertise

    """
    schedd_exprs_list = ["$(SCHEDD_EXPRS)"]
    attributes_file_lines = []

    for name, value in [
      ('OSG_Resource', self.osg_resource),
      ('OSG_ResourceGroup', self.osg_resource_group),
      ('OSG_BatchSystems', ",".join(self.enabled_batch_systems))
    ]:
      attributes_file_lines.append("%s = %s" % (name, utilities.classad_quote(value)))
      schedd_exprs_list.append(name)

    attributes_file_contents = (
        "# Do not edit - file generated by osg-configure\n"
        + "\n".join(attributes_file_lines) + "\n"
        + "SCHEDD_EXPRS = " + " ".join(schedd_exprs_list) + "\n"
    )

    return utilities.atomic_write(attributes_file, attributes_file_contents)

  def __write_ce_collector_file(self, info_services_file):
    """Write CE-Collector configuration file which specifies which
    host(s) to forward ads to

    """
    view_hosts = []
    for host in self.ce_collectors:
      if host.find(':') == -1:
        view_hosts.append("%s:%d" % (host, HTCONDOR_CE_COLLECTOR_PORT))
      else:
        view_hosts.append(host)
    info_services_file_contents = """\
# Do not edit - file generated by osg-configure
CONDOR_VIEW_HOST = %s
""" % ",".join(view_hosts)

    return utilities.atomic_write(info_services_file, info_services_file_contents)

