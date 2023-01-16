"""Zammad tap class."""

from typing import List

from singer_sdk import Stream, Tap
from singer_sdk import typing as th

from tap_zammad.streams import GroupsStream, TagsStream, TicketsStream, UsersStream

STREAM_TYPES = [TicketsStream, TagsStream, UsersStream, GroupsStream]


class TapZammad(Tap):
    """Zammad tap class."""

    name = "tap-zammad"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType,
            required=True,
            description="The token to authenticate against the Zammad API",
            secret=True,
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            description="The earliest record date to sync",
        ),
        th.Property(
            "api_base_url",
            th.StringType,
            description="The base url of the Zammad API",
            required=True,
        ),
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]


if __name__ == "__main__":
    TapZammad.cli()
