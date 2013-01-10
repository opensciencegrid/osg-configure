""" Module to hold various xml related functions """

import xml.dom.minidom
import xml.parsers

__all__ = ['get_elements']


def get_elements(element=None, filename=None):
  """Get values for selected element from xml file specified in filename"""
  if filename is None or element is None:
    return []
  try:
    dom = xml.dom.minidom.parse(filename)
  except IOError:
    return []
  except xml.parsers.expat.ExpatError:
    return []
  values = dom.getElementsByTagName(element)
  return values
