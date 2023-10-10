from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse
import logging

from requests import Response
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator


logger = logging.getLogger(__name__)


class ZammadAPIPaginator(BaseAPIPaginator):
    """
    A paginator class for paginating through Zammad API responses.
    As Zammad API has an internal limit of 10k results per requests,
    this paginator use an offset-strategy on the replication key (`updated_at`)
    to be able to retrieve all the results.

    Args:
        start_value (dict): The initial pagination value to start pagination from.
        Its a dict of url params.
        records_jsonpath (str): The JSONPath to the list of records in the API response.
        max_per_page (int): The maximum number of records that are returned per page.

    """

    def __init__(
        self, start_value: Dict[str, Any], records_jsonpath: str, max_per_page: int
    ) -> None:
        super().__init__(start_value)

        self.records_jsonpath = records_jsonpath
        self.max_per_page = max_per_page

    def get_next_url_params(self, response: Response) -> Optional[dict]:
        """Use received response to update url parameters with next page
        and `updated_at` offset if necessary

        Args:
            response: API response object.

        Returns:
            A dict with updated url params for next iteration.
        """
        parsed_url = urlparse(response.url)
        query = parsed_url.query
        params = parse_qs(query)
        params = {k: v[0] for k, v in params.items()}

        current_page = int(params["page"])
        next_page = current_page + 1

        updated_at_filter = params["query"]
        updated_at_datetime = datetime.strptime(params["query"][12:], "%Y-%m-%d")
        if (current_page * self.max_per_page) % 10_000 == 0:
            last_datetime = self.get_last_updated_at_from_response(
                response
            ) - timedelta(days=1)

            if last_datetime.date() == updated_at_datetime.date():
                logger.warning(
                    (
                        "It seems that there was too much update the same day."
                        "Currently, due to API limitation is it not possible to retrieve more than 10 000 updates the same day,"
                        " thus the paginator will move forward to the next day"
                    )
                )
                last_datetime += timedelta(days=1)

            next_page = 1
            updated_at_filter = f"updated_at:>{last_datetime:%Y-%m-%d}"

        params["page"] = next_page
        params["query"] = updated_at_filter

        return params

    def get_next(self, response: Response) -> Optional[Dict[str, Any]]:
        """Get the next pagination params from the API response.

        Args:
            response: API response object.

        Returns:
            A dict with the url parameters to get next page.
        """
        next_url_params = self.get_next_url_params(response)
        return next_url_params

    def has_more(self, response: Response) -> bool:
        """Check if the API endpoint has more results to return.

        Args:
            response: API response object.

        Returns:
            Boolean that indicates if there is more results.

        """
        return self.get_response_length(response) == self.max_per_page

    def get_response_length(self, response: Response) -> int:
        """Get number of objects returned in the response.

        Args:
            response: API response object.

        Returns:
            The length of the response as an integer.

        """
        return len(list(extract_jsonpath(self.records_jsonpath, input=response.json())))

    def get_last_updated_at_from_response(self, response: Response) -> datetime:
        """Get the value of the updated_at field of the last object in the response

        Args:
            response: API response object.

        Returns:
            A datetime with the value of the `updated_at` field
            of the last object returned.
        """

        json = response.json()
        records = list(extract_jsonpath(self.records_jsonpath, input=json))
        last_datetime = records[-1]["updated_at"]
        last_datetime = datetime.strptime(
            last_datetime.split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )
        return last_datetime
