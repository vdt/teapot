"""
tea-party 'attendee' class.
"""

import os
import json
import errno

from tea_party.log import LOGGER
from tea_party.source import make_sources
from tea_party.path import mkdir, rmdir


def make_attendees(party, data):
    """
    Build a list of attendees from an attendees data dictionary.
    """

    return [
        make_attendee(party, name, attributes)
        for name, attributes
        in data.items()
    ]


def make_attendee(party, name, attributes):
    """
    Create an attendee from a name a dictionary of attributes.
    """

    return Attendee(
        party=party,
        name=name,
        sources=make_sources(attributes.get('source')),
        depends=make_depends(attributes.get('depends')),
    )


def make_depends(depends):
    """
    Create a list of dependencies.

    `depends` can either be a single dependency name or a list of dependencies.

    If `depends` is False, an empty list is returned.
    """

    if not depends:
        return []

    elif isinstance(depends, basestring):
        return [depends]

    return depends


class Attendee(object):

    """
    An `Attendee` instance holds information about an attendee (third-party
    software).
    """

    CACHE_FILE = 'cache.json'

    def __init__(self, party, name, sources, depends):
        """
        Create an attendee associated to a `party`.

        `sources` is a list of Source instances.
        `depends` is a list of Attendee names to depend on.
        """

        if not party:
            raise ValueError('An attendee must be associated to a party.')

        if not sources:
            raise ValueError('A list one source must be specified for %s' % name)

        self.party = party
        self.name = name
        self.sources = sources
        self.depends = depends

    def __unicode__(self):
        """
        Get a unicode representation of the attendee.
        """

        return self.name

    def __str__(self):
        """
        Get the name of the attendee.
        """

        return self.name

    def __repr__(self):
        """
        Get a representation of the source.
        """

        return '<%s.%s(party=%r, name=%r, sources=%r, depends=%r)>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            self.party,
            self.name,
            self.sources,
            self.depends,
        )

    @property
    def cache_path(self):
        """
        The path of the cache of this attendee.
        """

        return os.path.join(self.party.cache_path, self.name)

    def clean_cache(self):
        """
        Clean the cache directory.
        """

        rmdir(self.cache_path)

    def create_cache(self):
        """
        Create the cache directory.
        """

        mkdir(self.cache_path)

    def fetch(self, context):
        """
        Fetch the attendee archive by trying all its sources.

        If the fetching suceeds, the succeeding source is returned.
        If the fetching fails, a RuntimeError is raised.
        """

        self.create_cache()

        for source in self.sources:
            archive_info = source.fetch(root_path=self.cache_path, context=context)
            archive_info['archive_path'] = os.path.relpath(archive_info['archive_path'], self.cache_path)

            with open(os.path.join(self.cache_path, self.CACHE_FILE), 'w') as cache_file:
                return json.dump(archive_info, cache_file)

            return source

        raise RuntimeError('All sources failed for %s' % self.name)

    def get_archive_info(self):
        """
        Get the associated archive info.

        Returns a dict containing the archive information.

        If the archive information or the archive does not exist, nothing is
        returned.
        """

        try:
            with open(os.path.join(self.cache_path, self.CACHE_FILE)) as cache_file:
                return json.load(cache_file)

        except IOError as ex:
            if ex.errno != errno.ENOENT:
                raise
        except ValueError:
            pass

    def needs_fetching(self):
        """
        Check if the attendee needs fetching.
        """

        archive_info = self.get_archive_info()

        if archive_info:
            if os.path.isfile(os.path.join(self.cache_path, archive_info.get('archive_path'))):
                LOGGER.debug('%s does not need fetching.', self)
                return False

        LOGGER.debug('%s needs fetching.', self)

        return True
