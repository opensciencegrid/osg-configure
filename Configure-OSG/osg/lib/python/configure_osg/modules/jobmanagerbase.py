#!/usr/bin/python

""" Base class for all job manager configuration classes """

from configure_osg.modules.configurationbase import BaseConfiguration
from configure_osg.modules import exceptions
from configure_osg.modules import utilities


__all__ = ['JobManagerConfiguration']


class JobManagerConfiguration(BaseConfiguration):
  """Base class for inheritance by jobmanager configuration classes"""
  def __init__(self, *args, **kwargs):
    # pylint: disable-msg=W0142
    super(JobManagerConfiguration, self).__init__(*args, **kwargs)
    self.attributes = {}
      

# pylint: disable-msg=R0201
  def get_sudo_text(self, globus_location, using_prima = False):
    """
    Generate text for sudoers file assuming the location of globus is given
    by the globus_location variable (i.e. globus_location should be the same
    as GLOBUS_LOCATION in the environment )    
    """
    
    if utilities.valid_user('globus'):
      # globus is the default user if present
      user = 'globus'
    else:
      user = 'daemon'
      
    text = "Runas_Alias GLOBUSUSERS = ALL, !root\n"
    text += "\n"
    if using_prima:
      text += "%s   ALL=(GLOBUSUSERS) \\\n" % user
      text += "     NOPASSWD: \\\n"
      text += "     %s/libexec/globus-job-manager-script.pl * \n" % globus_location
      text += "\n"
      text += "%s   ALL=(GLOBUSUSERS) \\\n" % user
      text += "     NOPASSWD: \\\n"
      text += "     %s/libexec/globus-gram-local-proxy-tool * \n" % globus_location
      text += "\n"
    else:
      text += "%s   ALL=(GLOBUSUSERS) \\\n" % user 
      text += "     NOPASSWD: %s/libexec/globus-gridmap-and-execute \\\n" % globus_location
      text += "     -g /etc/grid-security/grid-mapfile \\\n"
      text += "     %s/libexec/globus-job-manager-script.pl * \n" % globus_location
      text += "\n"
      text += "%s   ALL=(GLOBUSUSERS) \\\n" % user 
      text += "     NOPASSWD: %s/libexec/globus-gridmap-and-execute \\\n" % \
                      globus_location
      text += "     -g /etc/grid-security/grid-mapfile \\\n"
      text += "     %s/libexec/globus-gram-local-proxy-tool * \n" % globus_location
      text += "\n"
    return text

  def writeSudoExample(self, sudo_file, globus_location, using_prima = False):
    """
    Write an example sudo entries to sudoers file for admin
    """
    
    self.logger.debug("JobManagerConfiguration.writeSudoExample started")
    
    try:
      self.logger.debug("Writing to %s" % sudo_file)
      sudo_file = open(sudo_file, 'w')
      sudo_file.write(self.get_sudo_text(globus_location, using_prima))

    except IOError:
      self.logger.error("Can't write to sudo example file: %s" % sudo_file)
      raise exceptions.ConfigureError("Can't write to %s" % sudo_file)
    self.logger.debug("JobManagerConfiguration.writeSudoExample completed")
    
    
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
        return utilities.valid_domain(host)
      except ValueError:
        return False
    else:
      return utilities.valid_domain(host_part)

    return True
  
