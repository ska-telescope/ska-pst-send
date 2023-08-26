# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for interacting with the DPD API Pod."""
from __future__ import annotations

import logging

import requests

API_REINDEX_DATA_PRODUCTS: str = "reindexdataproducts"
API_DATA_PRODUCT_LIST: str = "dataproductlist"
API_SEARCH_TERM: str = "metadata_file"


class DpdApiClient:
    """Class used for interacting with the DataProduct Dashboard API."""

    def __init__(
        self: DpdApiClient,
        endpoint: str,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the DpdApiClient with API endpoint.

        :param endpoint: The endpoint of the API server. Consists of domain name and port number
        :param logger: the logger instance to use.
        """
        self._endpoint = endpoint
        self._api_reindex_dataproducts = API_REINDEX_DATA_PRODUCTS
        self._api_dataproductlist = API_DATA_PRODUCT_LIST
        self._api_search_term = API_SEARCH_TERM
        self.logger = logger or logging.getLogger(__name__)

    def reindex_dataproducts(self: DpdApiClient) -> None:
        """Execute a cURL API call to reindex data products.

        This method sends a POST request to the API endpoint for reindexing data products.
        """
        self.logger.debug("Calling DPD reindex dataproducts API")
        url = f"{self._endpoint}/{self._api_reindex_dataproducts}"
        response = requests.get(url, headers={"accept": "application/json"})
        if response.ok:
            self.logger.debug(
                f"DPD reindex dataproducts API successful return code. response={response.json()}"
            )
        else:
            self.logger.error(f"Failed DPD reindexing dataproducts API call. response={response.json()}")
            raise Exception(f"Failed to reindex data products. Status code: {response.status_code}")

    def metadata_exists(self: DpdApiClient, search_value: str) -> bool:
        """Check if metadata with a given search value exists.

        This method sends a GET request to the API endpoint for searching data products
        and checks if metadata with the specified search value exists.

        Returns:
            bool: True if metadata exists, False otherwise.
        """
        url = f"{self._endpoint}/{self._api_dataproductlist}"
        response = requests.get(url, headers={"accept": "application/json"})
        if response.ok:
            # Parse the JSON response into a list of dictionaries
            metadata_list = response.json()
            self.logger.debug("DPD reindex dataproducts API successful return code.")
            self.logger.debug(f"metadata_list={metadata_list}")
            self.logger.debug(f"api_search_term={self._api_search_term}")
            # Iterate through the dictionaries in the list
            for metadata_dict in metadata_list:
                # Check if "api_search_term" key exists and its value matches search_value
                if (
                    self._api_search_term in metadata_dict
                    and metadata_dict[self._api_search_term] == search_value
                ):
                    self.logger.debug(f"Metadata found={metadata_dict}")
                    return True  # Found a match, return True

            # If we reach here, search_value was not found in any "metadata_file" key
            self.logger.error(
                "Metadata not found",
            )
            self.logger.debug(f"metadata_list={metadata_list}")
            return False
        else:
            raise Exception(f"Failed to search for data products. Status code: {response.status_code}")

    # Property and setter for the API endpoint
    @property
    def endpoint(self) -> str:
        """Getter method for the API endpoint."""
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value: str) -> None:
        """Setter method for the API endpoint."""
        self._endpoint = value
