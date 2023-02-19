"""REST client handling, including ZammadStream base class."""

from datetime import timedelta
from pathlib import Path

from memoization import cached
from singer_sdk.authenticators import SimpleAuthenticator
from singer_sdk.streams import RESTStream

from tap_zammad.paginators import ZammadAPIPaginator

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ZammadStream(RESTStream):
    """Zammad stream class."""

    MAX_PER_PAGE = (
        200  # Seems that currently Zammad allows a maximum of 200 results per page
    )

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config["api_base_url"]

    @property
    @cached
    def authenticator(self):
        return SimpleAuthenticator(
            stream=self,
            auth_headers={
                "Authorization": f"Token token={self.config.get('auth_token')}",
            },
        )

    def get_new_paginator(self):
        """Return a custom paginator for the Zammad API."""
        return ZammadAPIPaginator(
            start_value=None,
            records_jsonpath=self.records_jsonpath,
            max_per_page=self.MAX_PER_PAGE,
        )

    def get_url_params(self, context, next_page_token) -> dict:
        """Create the initial URL parameters if `next_page_token` is `None`,
        or use its value for the next iteration (value from the paginator).

        Args:
            context: A dictionary containing information about the execution context
                of the plugin.
            next_page_token: A dictionary containing the url params to be used
                for the current iteration, or `None` if it's the first iteration.

        Returns:
            A dictionary containing the URL parameters to be used for the current iteration.

        """
        if next_page_token is not None:
            return next_page_token

        params = {}

        params["per_page"] = self.MAX_PER_PAGE

        params["page"] = 1

        params["query"] = "updated_at:>0"
        since = self.get_starting_timestamp(context)
        # Zammad seems to treat a timestamp as if it was
        # one hour in the past (eg. 11H00 is treat as 10:00)
        # so we have to add one hour to UTC timestamp to have the desired datetime filter
        if since is not None:
            zammad_since = since - timedelta(days=1)
            params["query"] = f"updated_at:>{zammad_since:%Y-%m-%d}"

        if self.replication_key:
            params["order_by"] = "asc"
            params["sort_by"] = self.replication_key

        return params
