"""
The tea-party main script.
"""

import os
import sys
import argparse
import logging

from functools import wraps

from tea_party.log import LOGGER
from tea_party.party import load_party_file


def main():
    """
    The script entry point.
    """

    parser = argparse.ArgumentParser(
        description='Manage third-party software.'
    )

    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output.')

    command_parser = parser.add_subparsers(help='The available commands.')
    parser.add_argument('-p', '--party-file', default=None, help='The party-file to read.')

    # The clean command
    clean_command_parser = command_parser.add_parser('clean', help='Clean the party.')
    clean_subcommand_parser = clean_command_parser.add_subparsers(help='The available commands.')

    #  The clean cache subcommand
    clean_cache_command_parser = clean_subcommand_parser.add_parser('cache', help='Clean the party cache.')
    clean_cache_command_parser.set_defaults(func=clean_cache)
    clean_cache_command_parser.add_argument('attendees', metavar='attendee', nargs='*', default=[], help='The attendees to clean.')

    #  The clean build subcommand
    clean_build_command_parser = clean_subcommand_parser.add_parser('build', help='Clean the party build.')
    clean_build_command_parser.set_defaults(func=clean_build)
    clean_build_command_parser.add_argument('attendees', metavar='attendee', nargs='*', default=[], help='The attendees to clean.')

    #  The clean all subcommand
    clean_all_command_parser = clean_subcommand_parser.add_parser('all', help='Clean the party cache and build.')
    clean_all_command_parser.set_defaults(func=clean_all)
    clean_all_command_parser.add_argument('attendees', metavar='attendee', nargs='*', default=[], help='The attendees to clean.')

    # The fetch command
    fetch_command_parser = command_parser.add_parser('fetch', help='Fetch all the archives.')
    fetch_command_parser.set_defaults(func=fetch)
    fetch_command_parser.add_argument('attendees', metavar='attendee', nargs='*', default=[], help='The attendees to fetch.')
    fetch_command_parser.add_argument('-f', '--force', action='store_true', help='Fetch archives even if they already exist in the cache.')

    # The unpack command
    unpack_command_parser = command_parser.add_parser('unpack', help='Unpack all the fetched archives.')
    unpack_command_parser.set_defaults(func=unpack)
    unpack_command_parser.add_argument('attendees', metavar='attendee', nargs='*', default=[], help='The attendees to unpack.')
    unpack_command_parser.add_argument('-f', '--force', action='store_true', help='Unpack archives even if they already exist in the build.')

    # The build command
    build_command_parser = command_parser.add_parser('build', help='Build the archives.')
    build_command_parser.set_defaults(func=build)
    build_command_parser.add_argument('attendees', metavar='attendee', nargs='*', default=[], help='The attendees to build.')
    build_command_parser.add_argument('-t', '--tags', metavar='tag', action='append', default=[], help='The tags to build.')
    build_command_parser.add_argument('-f', '--force', action='store_true', help='Clean build directories before trying to build. archives even if they already exist in the build.')

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.getLogger('requests').setLevel(logging.WARNING)

    if args.party_file is None:
        args.party_file = os.path.join(os.getcwd(), 'party.yaml')

    try:
        party = load_party_file(args.party_file)

    except IOError:
        LOGGER.error('No party-file was found. (Searched path: "%s")', args.party_file)

        return 1

    if not args.func(party, args):
        return 2

def command(func):
    """
    Provides exception handling for commands.
    """

    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            func(*args, **kwargs)

            return True
        except Exception as ex:
            LOGGER.exception(ex)

            return False

    return decorated

@command
def clean_cache(party, args):
    """
    Clean the party cache.
    """

    party.clean_cache(
        attendees=args.attendees,
    )

@command
def clean_build(party, args):
    """
    Clean the party build.
    """

    party.clean_build(
        attendees=args.attendees,
    )

@command
def clean_all(party, args):
    """
    Clean the party cache and build.
    """

    party.clean_cache(
        attendees=args.attendees,
    )
    party.clean_build(
        attendees=args.attendees,
    )

@command
def fetch(party, args):
    """
    Fetch the archives.
    """

    party.fetch(
        attendees=args.attendees,
        force=args.force,
    )

@command
def unpack(party, args):
    """
    Unpack the archives.
    """

    party.unpack(
        attendees=args.attendees,
        force=args.force,
    )

@command
def build(party, args):
    """
    Build the archives.
    """

    party.build(
        attendees=args.attendees,
        tags=args.tags,
        force=args.force,
    )
