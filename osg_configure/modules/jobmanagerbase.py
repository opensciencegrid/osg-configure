#!/usr/bin/python

""" Base class for all job manager configuration classes """

import re

from osg_configure.modules.configurationbase import BaseConfiguration
from osg_configure.modules import exceptions
from osg_configure.modules import utilities
from osg_configure.modules import validation



__all__ = ['JobManagerConfiguration']


class JobManagerConfiguration(BaseConfiguration):
  """Base class for inheritance by jobmanager configuration classes"""
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(JobManagerConfiguration, self).__init__(*args, **kwargs)
    self.attributes = {}
        

  def validContact(self, contact, jobmanager):
    """
    Check a contact string to make sure that it's valid, e.g. host[:port]/jobmanager
    returns True or False  
    """
    
    if len(contact.split('/')) != 2:
      return False
    (host_part, jobmanager_part) = contact.split('/')
    
    if '-' in jobmanager_part and jobmanager_part.split('-')[1] != jobmanager:
      # invalid jobmanager
      return False
    
    if ':' in host_part:
      (host, port) = host_part.split(':')
      try:
        # test to make sure port is an integer
        int(port)
        return validation.valid_domain(host)
      except ValueError:
        return False
    else:
      return validation.valid_domain(host_part)

    return True

  def enable_accept_limited(self, filename):
    """
    Update the globus jobmanager configuration so that it allows limited proxies
    
    Returns:
    True if config successfully updated 
    """
    buffer = open(filename).read()
    if 'accept_limited' not in buffer:
      buffer = 'accept_limited,' + buffer
      if utilities.atomic_write(filename, buffer):
        return True
      else:
        self.logger.error('Error writing to enabling accept_limited')
        return False

  def disable_accept_limited(self, filename):
    """
    Update the globus jobmanager configuration so that it does not allow limited proxies
    
    Returns:
    True if config successfully updated 
    """
    buffer = open(filename).read()
    if buffer.startswith('accept_limited,'):
      buffer = buffer.replace('accept_limited,','',1)
      if utilities.atomic_write(filename, buffer):
        return True
      else:
        self.logger.error('Error disabling accept_limited')
        return False
      
    if ',accept_limited' in buffer:
      buffer = buffer.replace(',accept_limited','',1)
      if utilities.atomic_write(filename, buffer):
        return True
      else:
        self.logger.error('Error disabling accept_limited')
        return False
      
    return True

  def set_default_jobmanger(self, default = 'fork'):
    """
    Set the default jobmanager
    
    Arguments:
    default - Indicates the default jobmanger, currently 
              either 'fork' or 'managed-fork' 
    """
    self.logger.debug("JobManager.set_default_jobmanager started")

    if default == 'fork': 
      self.logger.debug("Setting regular fork manager to be the default jobmanager")
      result = utilities.run_script(['/usr/sbin/globus-gatekeeper-admin',
                                     '-e',
                                     'jobmanager-fork-poll',
                                     '-n',
                                     'jobmanager'])    
      if not result:
        self.logger.error("Could not set the jobmanager-fork-poll to the default jobmanager")
        return False
    elif default == 'managed-fork':
      self.logger.debug("Setting regular fork manager to be the default jobmanager")
      result = utilities.run_script(['/usr/sbin/globus-gatekeeper-admin',
                                     '-e',
                                     'jobmanager-managedfork',
                                     '-n',
                                     'jobmanager'])    
      if not result:
        self.logger.error("Could not set the jobmanager-fork-poll to the default jobmanager")
        return False
    else:
      self.logger.error("Invalid jobamanger type specified as the default jobmanger: %s" % default)
      return False

    
    self.logger.debug("JobManager.set_default_jobmanager completed")
