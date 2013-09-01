"""
tea-party 'party' class.
"""

import os
import imp
import yaml

from functools import wraps

from tea_party.log import LOGGER
from tea_party.attendee import Attendee, make_attendees
from tea_party.path import read_path, rmdir
from tea_party.defaults import *
from tea_party.fetchers.callbacks import ProgressBarFetcherCallback
from tea_party.unpackers.callbacks import ProgressBarUnpackerCallback


def load_party_file(path):
    """
    Create a Party instance from a party-file.

    `path` must be a valid party-file name.
    """

    LOGGER.debug('Opening party-file at %s...' % path)

    with open(path) as party_file:
        data = party_file.read()

    values = yaml.load(data)

    extension_modules = values.get('extension_modules', {})

    # We import the extension modules.
    #
    # This has to be done first, or the things defined in those extension
    # modules won't be accessible to the parsing functions.
    for name, module_path in extension_modules.items():
        abs_module_path = os.path.join(os.path.dirname(path), module_path)

        try:
            imp.load_source(name, abs_module_path)
        except Exception as ex:
            LOGGER.error('Unable to load the extension module "%s" at "%s": %s', name, abs_module_path, ex)

    party = Party(
        path=path,
        cache_path=values.get('cache'),
        build_path=values.get('build'),
    )

    party.attendees = make_attendees(party, values.get('attendees'))

    return party


class NoSuchAttendeeError(ValueError):

    """
    The specified attendee does not exist.
    """

    def __init__(self, attendee):
        """
        Create an NoSuchAttendeeError for the specified `attendee`.
        """

        super(NoSuchAttendeeError, self).__init__(
            'No such attendee: %s' % attendee
        )


def has_attendees(func):
    """
    Ensures the function has real attendees instances as its `attendees`
    parameter.
    """

    @wraps(func)
    def result(self, *args, **kwargs):
        attendees = kwargs.get('attendees', [])

        if not attendees:
            attendees = self.enabled_attendees
        else:
            attendees = map(self.get_attendee_by_name, attendees)

        kwargs['attendees'] = attendees

        return func(self, *args, **kwargs)

    return result


class Party(object):

    """
    A party object is the root object that stores all the information about the
    different attendees (third-party softwares), and the party options.
    """

    def __init__(self, path, cache_path, build_path, **kwargs):
        """
        Create a Party instance.

        `path` is the path to the party file.
        `cache_path` is the root of the cache.
        `build_path` is the root of the build.
        """

        self.path = os.path.abspath(path)
        self.attendees = []
        self.cache_path = read_path(cache_path, os.path.dirname(self.path), DEFAULT_CACHE_PATH)
        self.build_path = read_path(build_path, os.path.dirname(self.path), DEFAULT_BUILD_PATH)
        self.auto_fetch = True
        self.fetcher_callback_class = ProgressBarFetcherCallback
        self.unpacker_callback_class = ProgressBarUnpackerCallback

    @property
    def enabled_attendees(self):
        """
        Get the list of the enabled attendees.
        """

        return [attendee for attendee in self.attendees if attendee.enabled]

    def get_attendee_by_name(self, name):
        """
        Get an attendee by name, if it exists.

        If no attendee has the specified name, a NoSuchAttendeeError is raised.
        """

        if isinstance(name, Attendee):
            return name

        for attendee in self.attendees:
            if attendee.name == name:
                return attendee

        raise NoSuchAttendeeError(attendee=attendee)

    @has_attendees
    def clean_cache(self, attendees=[]):
        """
        Clean the cache, optionally for a given list of `attendees` to recover
        disk space.
        """

        LOGGER.info('Cleaning the cache directory for: %s', ', '.join(map(str, attendees)))

        map(Attendee.clean_cache, attendees)

        LOGGER.info('Done cleaning the cache directory.')

    @has_attendees
    def clean_build(self, attendees=[]):
        """
        Clean the build, optionally for a given list of `attendees` to recover
        disk space.
        """

        LOGGER.info('Cleaning the build directory for: %s', ', '.join(map(str, attendees)))

        map(Attendee.clean_build, attendees)

        LOGGER.info('Done cleaning the build directory.')

    @has_attendees
    def fetch(self, attendees=[], force=False):
        """
        Fetch the archives.
        """

        if force:
            map(lambda x: x.clean_cache(), attendees)

        attendees_to_fetch = [x for x in attendees if not x.fetched]

        if not attendees_to_fetch:
            if len(attendees) == 1:
                LOGGER.info('%s was already fetched.', attendees[0])
            else:
                LOGGER.info('None of the %s archives needs fetching.', len(attendees))

        else:
            LOGGER.info("Fetching %s/%s archive(s)...", len(attendees_to_fetch), len(self.enabled_attendees))

            map(Attendee.fetch, attendees_to_fetch)

            LOGGER.info("Done fetching archives.")

    @has_attendees
    def unpack(self, attendees=[], force=False):
        """
        Unpack the archives.
        """

        if self.auto_fetch:
            self.fetch(attendees=attendees)

        if force:
            map(lambda x: x.clean_build(), self.enabled_attendees)

        attendees_to_unpack = [x for x in attendees if not x.unpacked]

        if not attendees_to_unpack:
            if len(attendees) == 1:
                LOGGER.info('%s was already unpacked.', attendees[0])
            else:
                LOGGER.info('None of the %s archive(s) needs unpacking.', len(attendees))

        else:
            LOGGER.info("Unpacking %s/%s archive(s)...", len(attendees_to_unpack), len(self.enabled_attendees))

            map(Attendee.unpack, attendees_to_unpack)

            LOGGER.info("Done unpacking archives.")

    @has_attendees
    def build(self, attendees=[], tags=[], force=False):
        """
        Build the archives.
        """

        if self.auto_fetch:
            self.unpack(attendees=attendees, force=force)

        LOGGER.info("Building %s archive(s)...", len(attendees))

        for attendee in attendees:
            attendee.build(tags=tags)

        LOGGER.info("Done building archives.")
