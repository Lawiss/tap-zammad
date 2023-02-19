from typing import TypeVar
from datetime import datetime, timedelta

from requests import Response
from singer_sdk.pagination import BaseAPIPaginator
from singer_sdk.helpers.jsonpath import extract_jsonpath

from urllib.parse import ParseResult, urlparse, parse_qs

TPageToken = TypeVar("TPageToken")


class ZammadAPIPaginator(BaseAPIPaginator):
    def __init__(
        self, start_value: TPageToken, records_jsonpath: str, max_per_page: int
    ) -> None:
        super().__init__(start_value)

        self.records_jsonpath = records_jsonpath
        self.max_per_page = max_per_page

    def get_next_url_params(self, response: Response) -> dict | None:
        """Override this method to extract a HATEOAS link from the response.

        Args:
            response: API response object.
        """
        parsed_url = urlparse(response.url)
        query = parsed_url.query
        params = parse_qs(query)
        params = {k: v[0] for k, v in params.items()}

        current_page = int(params["page"])
        next_page = current_page + 1

        updated_at_filter = params["query"]

        if (current_page * self.max_per_page) % 10_000 == 0:
            last_datetime = self.get_last_updated_at_from_response(
                response
            ) - timedelta(days=1)
            next_page = 1
            updated_at_filter = f"updated_at:>{last_datetime:%Y-%m-%d}"

        params["page"] = next_page
        params["query"] = updated_at_filter

        return params

    def get_next(self, response: Response) -> ParseResult | None:
        """Get the next pagination token or index from the API response.

        Args:
            response: API response object.

        Returns:
            A parsed HATEOAS link if the response has one, otherwise `None`.
        """
        next_url_params = self.get_next_url_params(response)
        return next_url_params

    def has_more(self, response: Response) -> bool:
        return self.get_response_length(response) == self.max_per_page

    def get_response_length(self, response: Response) -> int:
        return len(list(extract_jsonpath(self.records_jsonpath, input=response.json())))

    def get_last_updated_at_from_response(self, response: Response) -> datetime:
        """Get the value of the updated_at field of the last object in the response"""
        json = response.json()
        records = list(extract_jsonpath(self.records_jsonpath, input=json))
        last_datetime = records[-1]["updated_at"]
        last_datetime = datetime.strptime(
            last_datetime.split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )
        return last_datetime
