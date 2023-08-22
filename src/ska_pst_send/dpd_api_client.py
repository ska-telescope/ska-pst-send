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


class DpdApiClient:
    """Class used for interacting with the DataProduct Dashboard API."""

    def __init__(
        self: DpdApiClient,
        endpoint: str,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the DpdApiClient with API endpoint.

        :param str endpoint: The endpoint of the API server. Consists of domain name and port number
        :param logging.Logger logger: The logger instance to use.
        """
        self._endpoint = endpoint
        self._api_reindex_dataproducts = "reindexdataproducts"
        self._api_dataproductlist = "dataproductlist"
        self._api_search_term = "metadata_file"
        self.logger = logger or logging.getLogger(__name__)

    def reindex_dataproducts(self: DpdApiClient) -> None:
        """Execute a cURL API call to reindex data products.

        This method sends a POST request to the API endpoint for reindexing data products.
        """
        self.logger.debug("Calling DPD reindex dataproducts API")
        url = f"{self._endpoint}/{self._api_reindex_dataproducts}"
        response = requests.post(url)
        if response.status_code == 200:
            self.logger.debug(
                f"DPD reindex dataproducts API successful return code. response={response.json()}"
            )
            return response.json()
        else:
            raise Exception(f"Failed to reindex data products. Status code: {response.status_code}")

    def search_metadata(self: DpdApiClient, search_value: str) -> bool:
        """Execute a GET API call to search for data products.

        This method sends a GET request to the API endpoint for searching data products.
        The default search key is the 'metadata_file' where its value follows the format of
        $EXECUTION_BLOCK_ID/$SUBSYSTEM_ID/$SCAN_ID/ska-data-product.yaml
        """
        url = f"{self._endpoint}/{self._api_dataproductlist}"
        response = requests.get(url, headers={"accept": "application/json"})
        if response.status_code == 200:
            # Parse the JSON response into a list of dictionaries
            metadata_list = response.json()
            self.logger.debug("DPD reindex dataproducts API successful return code.")
            self.logger.debug(f"metadata_list={metadata_list}")
            self.logger.debug(f"api_search_term={self.api_search_term}")
            # Iterate through the dictionaries in the list
            for metadata_dict in metadata_list:
                # Check if "api_search_term" key exists and its value matches search_value
                if (
                    self.api_search_term in metadata_dict
                    and metadata_dict[self.api_search_term] == search_value
                ):
                    return True  # Found a match, return True

            # If we reach here, search_value was not found in any "metadata_file" key
            return False
        else:
            raise Exception(f"Failed to search for data products. Status code: {response.status_code}")

    # Property and setter for the API endpoint
    @property
    def endpoint(self) -> str:
        """Getter method for the API endpoint."""
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value) -> None:
        """Setter method for the API endpoint."""
        self._endpoint = value

    # Property and setter for search term used in search_metadata
    @property
    def api_search_term(self) -> int:
        """Getter method for the api_search_term."""
        return self._api_search_term

    @api_search_term.setter
    def api_search_term(self, value) -> None:
        """Setter method for the api_search_term."""
        self._api_search_term = value
