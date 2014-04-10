"""
A source class.
"""

from .filters import FilteredObject
from .fetchers import Fetcher


class Source(FilteredObject):

    """
    Represents a project to build.
    """

    def __init__(self, resource, mimetype=None, fetcher=None, *args, **kwargs):
        """
        Create a source that maps on the specified resource.
        """

        super(Source, self).__init__(*args, **kwargs)

        self.resource = resource
        self.mimetype = mimetype
        self._fetcher = fetcher
        self._parsed_source = None

    def __str__(self):
        """
        Get a string representation of the source.
        """

        return self.resource

    @property
    def fetcher(self):
        if not self._fetcher:
            self._fetcher = Fetcher.get_instance_for(source=self)

        if isinstance(self._fetcher, basestring):
            self._fetcher = Fetcher.get_instance_or_fail(name=self._fetcher)

        return self._fetcher

    @property
    def parsed_source(self):
        if self._parsed_source is None:
            self._parsed_source = self.fetcher.parse_source(source=self)

        return self._parsed_source

    def fetch(self, target_path):
        """
        Fetches the source.
        """

        return self.fetcher.fetch(
            parsed_source=self.parsed_source,
            target_path=target_path,
        )
