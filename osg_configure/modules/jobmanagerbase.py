""" Base class for all job manager configuration classes """

import re
import os
import logging

from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.modules import utilities
from osg_configure.modules import validation



__all__ = ['JobManagerConfiguration']


class JobManagerConfiguration(BaseConfiguration):
  """Base class for inheritance by jobmanager configuration classes"""
  MISSING_JOBMANAGER_CONF_MSG = ("Unable to load the jobmanager configuration at %s: %s.\n"
                                 "Ensure the Globus jobmanagers for all enabled batch systems are installed.")

  BLAH_CONFIG = '/etc/blah.config'

  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(JobManagerConfiguration, self).__init__(*args, **kwargs)
    self.attributes = {}
    self.lrms = ['pbs', 'sge', 'lsf', 'condor']
    self.seg_admin_path = '/usr/sbin/globus-scheduler-event-generator-admin'
    self.gram_gateway_enabled = False
    self.htcondor_gateway_enabled = True

  def parseConfiguration(self, configuration):
    super(JobManagerConfiguration, self).parseConfiguration(configuration)
    self.log('JobManagerConfiguration.parseConfiguration started')
    if configuration.has_section('Gateway'):
      if configuration.has_option('Gateway', 'htcondor_gateway_enabled'):
        self.htcondor_gateway_enabled = configuration.getboolean('Gateway', 'htcondor_gateway_enabled')
      if configuration.has_option('Gateway', 'gram_gateway_enabled'):
        self.gram_gateway_enabled = configuration.getboolean('Gateway', 'gram_gateway_enabled')
    self.log('JobManagerConfiguration.parseConfiguration completed')

  def gatewayServices(self):
    services = set([])
    if self.htcondor_gateway_enabled:
      services.add('condor-ce')
    if self.gram_gateway_enabled:
      services.add('globus-gatekeeper')
    return services
  
  def enable_accept_limited(self, filename):
    """
    Update the globus jobmanager configuration so that it allows limited proxies
    
    Returns:
    True if config successfully updated 
    """
    if filename is None:
      return False

    try:
      contents = open(filename).read()
    except EnvironmentError, err:
      self.log(self.MISSING_JOBMANAGER_CONF_MSG % (filename, err), level=logging.ERROR)
      return False

    if 'accept_limited' not in contents:
      contents = 'accept_limited,' + contents
      if utilities.atomic_write(filename, contents):
        return True
      else:
        self.log('Error writing to %s enabling accept_limited' % filename,
                 level = logging.ERROR)
        return False
    # accept limited already enabled, do nothing
    return True
  
  def disable_accept_limited(self, filename):
    """
    Update the globus jobmanager configuration so that it does not allow 
    limited proxies
    
    Returns:
    True if config successfully updated 
    """
    if filename is None:
      return False

    try:
      contents = open(filename).read()
    except EnvironmentError, err:
      self.log(self.MISSING_JOBMANAGER_CONF_MSG % (filename, err), level=logging.ERROR)
      return False

    if contents.startswith('accept_limited,'):
      contents = contents.replace('accept_limited,', '', 1)
      if utilities.atomic_write(filename, contents):
        return True
      else:
        self.log('Error disabling accept_limited',
                 level = logging.ERROR)
        return False
      
    if ',accept_limited' in contents:
      contents = contents.replace(',accept_limited', '', 1)
      if utilities.atomic_write(filename, contents):
        return True
      else:
        self.log('Error disabling accept_limited',
                 level = logging.ERROR)
        return False
    
    # accept limited already disabled, don't do anything
    return True
  
  def enable_seg(self, seg_module, filename):
    """
    Update the globus jobmanager configuration so that it uses the SEG 
    
    Returns:
    True if config successfully updated 
    """
    if filename is None or seg_module is None:
      return False
    
    if seg_module not in self.lrms:
      return False
    
    try:
      contents = open(filename).read()
    except EnvironmentError, err:
      self.log(self.MISSING_JOBMANAGER_CONF_MSG % (filename, err), level=logging.ERROR)
      return False

    if '-seg-module' not in contents:
      contents = contents + '-seg-module ' + seg_module
      if utilities.atomic_write(filename, contents):
        return True
      else:
        self.log('Error enabling SEG in ' + filename,
                 level = logging.ERROR)
        return False

    if not utilities.run_script([self.seg_admin_path, '-e', seg_module]):
      return False

    return True
  
  def disable_seg(self, seg_module, filename):
    """
    Update the globus jobmanager configuration so that it does not allow use the SEG
    
    Returns:
    True if config successfully updated 
    """
    if filename is None or seg_module is None:
      return False
    
    if seg_module not in self.lrms:
      return False

    try:
      contents = open(filename).read()
    except EnvironmentError, err:
      self.log(self.MISSING_JOBMANAGER_CONF_MSG % (filename, err), level=logging.ERROR)
      return False

    if '-seg-module' in contents:
      contents = re.sub(r'-seg-module\s+.*?\s', '', contents, 1)
      if utilities.atomic_write(filename, contents):
        return True
      else:
        self.log('Error disabling SEG in ' + filename,
                 level = logging.ERROR)                 
        return False
            
    if not utilities.run_script([self.seg_admin_path, '-d', seg_module]):
      return False
    
    return True

  def set_default_jobmanager(self, default = 'fork'):
    """
    Set the default jobmanager
    
    Arguments:
    default - Indicates the default jobmanger, currently 
              either 'fork' or 'managed-fork' 
    """
    self.log("JobManager.set_default_jobmanager started")

    gatekeeper_admin = "/usr/sbin/globus-gatekeeper-admin"
    if not validation.valid_executable(gatekeeper_admin):
      self.log("%s not found. Ensure the Globus Gatekeeper is installed." % gatekeeper_admin, level=logging.ERROR)
      return False

    if default == 'fork': 
      self.log("Setting regular fork manager to be the default jobmanager")
      result = utilities.run_script([gatekeeper_admin,
                                     '-e',
                                     'jobmanager-fork-poll',
                                     '-n',
                                     'jobmanager'])    
      if not result:
        self.log("Could not set the jobmanager-fork-poll to the default " +
                 "jobmanager",
                 level = logging.ERROR)
        return False
      result = utilities.run_script([gatekeeper_admin,
                                     '-e',
                                     'jobmanager-fork-poll',
                                     '-n',
                                     'jobmanager-fork'])    
      if not result:
        self.log("Could not set the jobmanager-fork-poll to the default " +
                 "jobmanager",
                 level = logging.ERROR)
        return False
    elif default == 'managed-fork':
      self.log("Setting managed fork manager to be the default jobmanager")
      result = utilities.run_script([gatekeeper_admin,
                                     '-e',
                                     'jobmanager-managedfork',
                                     '-n',
                                     'jobmanager'])    
      if not result:
        self.log("Could not set the jobmanager-managedfork to the default " +
                 "jobmanager",
                 level = logging.ERROR)
        return False
      result = utilities.run_script([gatekeeper_admin,
                                     '-e',
                                     'jobmanager-managedfork',
                                     '-n',
                                     'jobmanager-fork'])    
      if not result:
        self.log("Could not set the jobmanager-managedfork to the default " +
                 "jobmanager",
                 level = logging.ERROR)
        return False
    else:
      self.log("Invalid jobamanger type specified as the default " +
               "jobmanger: %s" % default,
               level = logging.ERROR)
      return False

    
    self.log("JobManager.set_default_jobmanager completed")
    return True

  def write_binpaths_to_blah_config(self, jobmanager, submit_binpath):
    """
    Change the *_binpath variables in /etc/blah.config for the given
    jobmanager to point to the locations specified by the user in the
    config for that jobmanager. Does not do anything if /etc/blah.config
    is missing (e.g. if blahp is not installed).
    :param jobmanager: The name of a job manager that has a _binpath
      variable in /etc/blah.config
    :param submit_binpath: The fully-qualified path to the submit
      executables for that jobmanager
    """
    if os.path.exists(self.BLAH_CONFIG):
      contents = utilities.read_file(self.BLAH_CONFIG)
      contents = utilities.add_or_replace_setting(contents, jobmanager + "_binpath", submit_binpath, quote_value=False)
      utilities.atomic_write(self.BLAH_CONFIG, contents)

  def write_blah_disable_wn_proxy_renewal_to_blah_config(self):
    if os.path.exists(self.BLAH_CONFIG):
      contents = utilities.read_file(self.BLAH_CONFIG)
      contents = utilities.add_or_replace_setting(contents, "blah_disable_wn_proxy_renewal", "yes", quote_value=False)
      utilities.atomic_write(self.BLAH_CONFIG, contents)

