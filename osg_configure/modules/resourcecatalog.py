from __future__ import absolute_import
import classad
import re
from . import utilities


class RCEntry(object):
    """Contains the data in a ResourceCatalog entry
    :var name: name of the resource
    :var cpus: number of cores per node
    :var memory: megabytes of memory per node
    :var allowed_vos: a list or string containing the names of all the VOs that are allowed to run on this resource.
      Optional; if not specified, all VOs can run on this resource.
    :type allowed_vos: str or list or None
    :var max_wall_time: optional max run time of job on these nodes in minutes
    :var queue: optional remote queue name
    :var subclusters: optional list of subclusters connected to this resource
    :var vo_tag: optional
    :var extra_requirements: optional string of extra requirements clauses (which are ANDed together)
    :var extra_transforms; optional string of transform attributes (which are appended)
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', '')
        self.cpus = kwargs.get('cpus', 0)
        self.memory = kwargs.get('memory', 0)
        self.allowed_vos = kwargs.get('allowed_vos', None)
        self.max_wall_time = kwargs.get('max_wall_time', None)
        self.queue = kwargs.get('queue', '')
        self.subclusters = kwargs.get('subclusters', None)
        self.vo_tag = kwargs.get('vo_tag', None)
        self.extra_requirements = kwargs.get('extra_requirements', '')
        self.extra_transforms = kwargs.get('extra_transforms', '')

    def validate(self):
        """Check that the values of the RCEntry fields match the requirements for a resource catalog entry.
        Some fields must be specified; some fields must be convertable to
        ints if specified; some fields must be in a certain range.

        :raise ValueError, TypeError: in case validation fails
        :return self:

        """
        # Several of these can raise TypeError or ValueError but that's expected
        if not self.name:
            raise ValueError("'name' not specified")
        if int(self.cpus) <= 0:
            raise ValueError("'cpus' out of range at %s; must be > 0" % self.cpus)
        if int(self.memory) <= 0:
            raise ValueError("'memory' out of range at %s; must be > 0" % self.cpus)

        if self.max_wall_time is not None:
            if not int(self.max_wall_time) >= 0:
                raise ValueError("'max_wall_time' out of range at %s; must be >= 0" % self.max_wall_time)

        if self.allowed_vos is not None:
            if not isinstance(self.allowed_vos, (list, tuple, set, str)):
                raise TypeError("'allowed_vos' is a %s; must be a string or a list/tuple/set" % type(self.allowed_vos))

        if self.subclusters is not None:
            if not isinstance(self.subclusters, (list, tuple, set, str)):
                raise TypeError("'subclusters' is a %s; must be a string or a list/tuple/set" % type(self.subclusters))

        return self

    def normalize(self):
        """Convert the vaules in the RCEntry fields to their most useful form.
        For example, integers are parsed, and comma or space-separated strings
        are split up into lists.
        :return self:

        """
        self.cpus = int(self.cpus)
        self.memory = int(self.memory)
        if self.max_wall_time is not None:
            self.max_wall_time = int(self.max_wall_time)
        if self.allowed_vos is not None and isinstance(self.allowed_vos, str):
            self.allowed_vos = filter(None, re.split('[ ,]+', self.allowed_vos))
        if self.subclusters is not None and isinstance(self.subclusters, str):
            self.subclusters = filter(None, re.split(r'\s*,\s*', self.subclusters))

        return self

    def as_attributes(self):
        """Return this entry as a list of classad attributes"""
        attributes = {'Name': utilities.classad_quote(self.name),
                      'CPUs': self.cpus,
                      'Memory': self.memory}

        if self.max_wall_time is not None:
            attributes['MaxWallTime'] = self.max_wall_time

        requirements_clauses = ['TARGET.RequestCPUs <= CPUs', 'TARGET.RequestMemory <= Memory']
        if self.extra_requirements:
            requirements_clauses.append(self.extra_requirements)

        if self.allowed_vos:
            allowed_vos = "{ " + ", ".join([utilities.classad_quote(vo) for vo in self.allowed_vos]) + " }"
            attributes['AllowedVOs'] = allowed_vos
            requirements_clauses.append("member(TARGET.VO, AllowedVOs)")

        if self.subclusters:
            subclusters = "{ " + ", ".join([utilities.classad_quote(sc) for sc in self.subclusters]) + " }"
            attributes['Subclusters'] = subclusters

        transform_classad = classad.parseOne('[set_xcount = RequestCPUs; set_MaxMemory = RequestMemory]')

        if self.vo_tag:
            quoted_vo_tag = utilities.classad_quote(self.vo_tag)
            attributes['VOTag'] = quoted_vo_tag
            requirements_clauses.append("TARGET.VOTag == " + quoted_vo_tag)
            transform_classad['set_VOTag'] = quoted_vo_tag

        attributes['Requirements'] = ' && '.join(requirements_clauses)

        if self.queue:
            transform_classad['set_remote_queue'] = utilities.classad_quote(self.queue)
        if self.extra_transforms:
            try:
                extra_transforms_classad = classad.parseOne(self._munge_extra_transforms(self.extra_transforms))
            except SyntaxError as e:
                raise ValueError("Unable to parse 'extra_transforms': %s" % e)
            transform_classad.update(extra_transforms_classad)
        attributes['Transform'] = '['
        for key in sorted(transform_classad.keys()):
            attributes['Transform'] += " %s = %s;" % (key, transform_classad[key])
        attributes['Transform'] += ' ]'

        return attributes

    @staticmethod
    def _munge_extra_transforms(extra_transforms):
        """Ensure extra_transforms is surrounded by exactly one pair of brackets
        so it can be parsed as a classad
        """
        return '[' + extra_transforms.lstrip('[ \t').rstrip('] \t') + ']'


class ResourceCatalog(object):
    """Class for building an OSG_ResourceCatalog attribute in condor-ce configs for the ce-collector"""

    def __init__(self):
        self.entries = {}

    def add_rcentry(self, rcentry):
        self.entries[rcentry.name] = rcentry.normalize().validate().as_attributes()

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
            catalog = ('{ \\\n'
                       + ', \\\n'.join(entry_texts)
                       + ' \\\n}')

        return 'OSG_ResourceCatalog = ' + catalog
