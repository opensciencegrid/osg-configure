""" Module to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
"""
import logging

try:
  import classad
except ImportError:
  classad = None

from osg_configure.modules import configfile
from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.modules import utilities

__all__ = ['GatewayConfiguration']

HTCONDOR_ATTRIBUTES_FILE = '/etc/condor-ce/config.d/50-osg-attributes.conf'

class GatewayConfiguration(BaseConfiguration):
  """ Class to handle configuration of the job gateway services (globus-gatekeeper and condor-ce)
  """

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(GatewayConfiguration, self).__init__(*args, **kwargs)
    self.log('GatewayConfiguration.__init__ started')
    self.options = {'gram_gateway_enabled':
                      configfile.Option(name='gram_gateway_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=True),
                    'htcondor_gateway_enabled':
                      configfile.Option(name='htcondor_gateway_enabled',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=bool,
                                        default_value=False),
                    'job_envvar_path' :
                      configfile.Option(name='job_envvar_path',
                                        required=configfile.Option.OPTIONAL,
                                        opt_type=str,
                                        default_value='/bin:/usr/bin:/sbin:/usr/sbin',
                                        mapping='PATH')}
    self.gram_gateway_enabled = True
    self.htcondor_gateway_enabled = False
    self.config_section = "Gateway"
    
    # We get these from the Site Information section
    self.osg_resource = None
    self.osg_resource_group = None
    # Some bits of configuration are skipped if enabled is False (which is the default in BaseConfiguration)
    self.enabled = True # XXX This needs to be True for mappings to work
    self.log('GatewayConfiguration.__init__ completed')

  def parseConfiguration(self, configuration):
    """
    Try to get configuration information from ConfigParser or
    SafeConfigParser object given by configuration and write recognized settings
    to attributes dict
    """
    self.log('GatewayConfiguration.parseConfiguration started')
    if not configuration.has_section(self.config_section):
      self.enabled = False
      self.log("%s section not in config file" % self.config_section)
      self.log('GatewayConfiguration.parseConfiguration completed')
      return

    self.getOptions(configuration)

    self.gram_gateway_enabled = self.options['gram_gateway_enabled'].value
    self.htcondor_gateway_enabled = self.options['htcondor_gateway_enabled'].value
    
    # We get some values for HTCondor-CE from the Site Information section
    if configuration.has_section('Site Information'):
      if configuration.has_option('Site Information', 'resource'):
        self.osg_resource = configuration.get('Site Information', 'resource')
      if configuration.has_option('Site Information', 'resource_group'):
        self.osg_resource_group = configuration.get('Site Information', 'resource_group')
      
    self.log('GatewayConfiguration.parseConfiguration completed')

  # Not overriding enabledServices -- only job manager modules need the gateways enabled
  #def enabledServices(self):

  # Not overriding checkAttributes -- all attributes are independent.
  #def checkAttributes(self, attributes):

  def configure(self, attributes):
    """Configure installation using attributes"""
    self.log('GatewayConfiguration.configure started')
    attributes_ok = True
    
    if self.htcondor_gateway_enabled and utilities.ce_installed():
      attributes_ok = attributes_ok and self.configure_htcondor_ce()

    self.log('GatewayConfiguration.configure completed')
    return attributes_ok

  def configure_htcondor_ce(self):
    if not classad:
      self.log("classad library not present; "
               "HTCondor-CE configuration requires the HTCondor Python bindings (condor-python package)",
               level=logging.ERROR)
      return False
    if not self.write_htcondor_attributes_file(HTCONDOR_ATTRIBUTES_FILE):
      self.log("Writing attributes file %r failed" % HTCONDOR_ATTRIBUTES_FILE,
               level=logging.ERROR)
      return False

  def write_htcondor_attributes_file(self, attributes_file):
    """Write config file that causes htcondor-ce to advertise certain
    OSG attributes

    """
    # SOFTWARE-1592
    schedd_exprs_list = ["$(SCHEDD_EXPRS)"]
    attributes_file_lines = []

    for name, value in [('OSG_Resource', self.osg_resource),
                        ('OSG_ResourceGroup', self.osg_resource_group)]:

      attributes_file_lines.append("%s = %s" % (name, classad.quote(str(value))))
      schedd_exprs_list.append(name)

    attributes_file_contents = (
        "# Do not edit - file generated by osg-configure\n"
        + "\n".join(attributes_file_lines) + "\n"
        + "SCHEDD_EXPRS = " + " ".join(schedd_exprs_list) + "\n"
    )

    return utilities.atomic_write(attributes_file, attributes_file_contents)

  def moduleName(self):
    """A string with the name of the module"""
    return self.config_section

  def separatelyConfigurable(self):
    """A boolean that indicates whether this module can be configured separately"""
    return False
