"""REST client handling, including ZammadStream base class."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from memoization import cached
from singer_sdk.authenticators import SimpleAuthenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.streams import RESTStream
import requests

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

    def get_next_page_token(
        self, response: requests.Response, previous_token: Optional[Any]
    ) -> Optional[Any]:
        """Return a token for identifying next page or None if no more pages.
        As Zammad limit the number of results to 10k, a strategy is adopted to
        be able to continue the extraction even if the limit has been reached.
        """

        if previous_token is None:
            return 2

        if self.get_response_length(response) < self.MAX_PER_PAGE:
            return None

        # Zammad search is limited to 10k results, thus if we reach this limit,
        # we take the "updated_at" value of the last ticket at the last page as new
        # incremental filter value and we reset the page number to start new iteration.
        if (
            isinstance(previous_token, int)
            and ((previous_token * self.MAX_PER_PAGE) % 10_000) == 0
        ):
            last_datetime = self.get_last_updated_at_from_reponse(response) - timedelta(
                days=1
            )

            return (last_datetime.strftime("%Y-%m-%d"), 1)
        elif isinstance(previous_token, tuple):
            current_updated_at, current_page = previous_token
            if ((current_page * self.MAX_PER_PAGE) % 10_000) == 0:

                last_datetime = self.get_last_updated_at_from_reponse(
                    response
                ) - timedelta(days=1)
                return (last_datetime.strftime("%Y-%m-%d"), 1)

            else:
                return (current_updated_at, current_page + 1)

        return previous_token + 1

    def get_last_updated_at_from_reponse(self, response: requests.Response) -> datetime:
        """Get the value of the updated_at field of the last object in the response"""
        json = response.json()
        records = list(extract_jsonpath(self.records_jsonpath, input=json))
        last_datetime = records[-1]["updated_at"]
        last_datetime = datetime.strptime(
            last_datetime.split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )
        return last_datetime

    def get_response_length(self, response: requests.Response) -> int:
        return len(list(extract_jsonpath(self.records_jsonpath, input=response.json())))
