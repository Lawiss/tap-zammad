"""REST client handling, including ZammadStream base class."""

from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from memoization import cached
from singer_sdk.authenticators import SimpleAuthenticator
from singer_sdk.streams import RESTStream

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

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""
        params: dict = {}

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

        if isinstance(next_page_token, int):
            params["page"] = next_page_token
        elif isinstance(next_page_token, tuple):
            current_updated_at, next_page = next_page_token
            params["query"] = f"updated_at:>{current_updated_at}"
            params["page"] = next_page

        if self.replication_key:
            params["order_by"] = "asc"
            params["sort_by"] = self.replication_key

        return params
