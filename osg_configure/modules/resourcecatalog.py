import re
import utilities


class ResourceCatalog(object):
  """Class for building an OSG_ResourceCatalog attribute in condor-ce configs for the ce-collector"""

  def __init__(self):
    self.entries = {}

  def add_entry(self, name, cpus, memory, allowed_vos=None, max_wall_time=None, extra_requirements=None, extra_transforms=None):
    """Composes an entry for a single resource and adds it to the list of entries in the ResourceCatalog
    :param name: name of the resource
    :type name: str
    :param cpus: number of cores per node
    :type cpus: int
    :param memory: megabytes of memory per node
    :type memory: int
    :param allowed_vos: a list or string containing the names of all the VOs that are allowed to run on this resource.
      Optional; if not specified, all VOs can run on this resource.
    :type allowed_vos: str or list or None
    :param max_wall_time: max run time of job on these nodes in minutes
    :type max_wall_time: int or None
    :param extra_requirements: optional string of extra requirements clauses (which are ANDed together)
    :type extra_requirements: str or None
    :param extra_transforms; optional string of transform attributes (which are appended)
    :type extra_transforms: str or None
    """
    if not name:
      raise ValueError("Required parameter 'name' must be specified")
    # These statements can raise TypeError or ValueError but that's ok
    cpus = int(cpus)
    memory = int(memory)
    if not cpus > 0:
      raise ValueError("Parameter 'cpus' out of range at %r; must be > 0" % cpus)
    if not memory > 0:
      raise ValueError("Parameter 'memory' out of range at %r; must be > 0" % memory)

    attributes = {'Name': utilities.classad_quote(name),
                  'CPUs': cpus,
                  'Memory': memory}

    if max_wall_time is not None:
      max_wall_time = int(max_wall_time)
      if not max_wall_time > 0:
        raise ValueError("Parameter 'max_wall_time' out of range at %r; must be > 0" % max_wall_time)
      attributes['MaxWallTime'] = max_wall_time

    requirements_clauses = ['TARGET.RequestCPUs <= CPUs', 'TARGET.RequestMemory <= Memory']
    if extra_requirements:
      requirements_clauses.append(extra_requirements)

    if allowed_vos:
      if isinstance(allowed_vos, str):
        allowed_vos = re.split('[ ,]+', allowed_vos)
      allowed_vos = "{ " + ", ".join([utilities.classad_quote(vo) for vo in allowed_vos]) + " }"
      attributes['AllowedVOs'] = allowed_vos
      requirements_clauses.append("member(TARGET.VO, AllowedVOs)")

    attributes['Requirements'] = ' && '.join(requirements_clauses)

    transform_attributes = ['set_RequestCpus = %d' % cpus, 'set_MaxMemory = %d' % memory]
    if extra_transforms:
      transform_attributes.append(extra_transforms)
    attributes['Transform'] = '[ ' + '; '.join(transform_attributes) + '; ]'

    self.entries[name] = attributes

    return self

  def compose_text(self):
    """Return the OSG_ResourceCatalog classad attribute made of all the entries in this object"""
    if not self.entries:
      catalog = '{}'
    else:
      entry_texts = []
      for entrykey in sorted(self.entries):
        entry = self.entries[entrykey]
        entry_text = '  [ \\\n'
        for attribkey in sorted(entry):
          entry_text += '    %s = %s; \\\n' % (attribkey, entry[attribkey])
        entry_text += '  ]'
        entry_texts.append(entry_text)
      catalog = ( '{ \\\n'
                + ', \\\n'.join(entry_texts)
                + ' \\\n}' )

    return 'OSG_ResourceCatalog = ' + catalog
