import re
import utilities


class ResourceCatalog(object):
  """Class for building an OSG_ResourceCatalog attribute in condor-ce configs for the ce-collector"""

  def __init__(self):
    self.entries = []

  def add_entry(self, name, cpus, memory, allowed_vos=None):
    """Composes an entry for a single resource and adds it to the list of entries in the ResourceCatalog
    :param name: name of the resource
    :type name: str
    :param cpus: number of cores per node
    :type cpus: int
    :param memory: megabytes of memory per node
    :type memory: int
    :param allowed_vos: a list or string containing the names of all the VOs that are allowed to run on this resource.
      Optional; if not specified, all VOs can run on this resource.
    :type allowed_vos: str or list
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

    if isinstance(allowed_vos, str):
      allowed_vos = re.split('[ ,]+', allowed_vos)

    lines = ['  [',
             '    Name = %s;' % utilities.classad_quote(name),
             '    CPUs = %d;' % cpus,
             '    Memory = %d;' % memory]

    requirements_clauses = ['RequestCPUs <= CPUs', 'RequestMemory <= Memory']

    if allowed_vos:
      vo_clauses = ['VO == %s' % utilities.classad_quote(vo) for vo in allowed_vos if vo]
      requirements_clauses.append("(%s)" % " || ".join(vo_clauses))

    if requirements_clauses:
      lines.append('    Requirements = %s;' % ' && '.join(requirements_clauses))

    lines.append('  ]')

    self.entries.append(' \\\n'.join(lines))

    return self

  def compose_text(self):
    """Return the OSG_ResourceCatalog classad attribute made of all the entries in this object"""
    if not self.entries:
      catalog = '{}'
    else:
      catalog = ( '{ \\\n'
                + ', \\\n'.join(self.entries)
                + ' \\\n}' )

    return 'OSG_ResourceCatalog = ' + catalog
