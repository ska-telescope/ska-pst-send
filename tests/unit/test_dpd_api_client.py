# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the DpdApiClient."""

from unittest.mock import MagicMock, patch

import pytest

from ska_pst_send.dpd_api_client import DpdApiClient


@pytest.fixture
def dpd_api_endpoint() -> str:
    """Fixture for DPD endpoint."""
    return "http://example.com:8080"


@pytest.fixture
def dpd_api_client(dpd_api_endpoint: str) -> DpdApiClient:
    return DpdApiClient(dpd_api_endpoint)


@patch("requests.get")
def test_metadata_exists_found(mock_get: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Mock the GET request and response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"metadata_file": "file1"},
        {"metadata_file": "file2"},
    ]
    mock_get.return_value = mock_response

    # Perform the metadata_exists check
    result: bool = dpd_api_client.metadata_exists("file1")

    # Check that the GET request was made with the correct URL
    mock_get.assert_called_once_with(
        "http://example.com:8080/dataproductlist", headers={"accept": "application/json"}
    )

    # Check that the result is True since "file1" was found in the response
    assert result is True


@patch("requests.get")
def test_metadata_exists_not_found(mock_get: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Mock the GET request and response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"metadata_file": "file1"},
        {"metadata_file": "file2"},
    ]
    mock_get.return_value = mock_response

    # Perform the metadata_exists check for a non-existent file
    result: bool = dpd_api_client.metadata_exists("file3")

    # Check that the GET request was made with the correct URL
    mock_get.assert_called_once_with(
        "http://example.com:8080/dataproductlist", headers={"accept": "application/json"}
    )

    # Check that the result is False since "file3" was not found in the response
    assert result is False


@patch("requests.post")
def test_reindex_dataproducts_error(mock_post: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Mock the POST request and response with an error status code."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    # Explicitly raise an exception when requests.post is called
    mock_post.side_effect = Exception("Failed to make POST request")

    # Perform the reindex
    with pytest.raises(Exception) as excinfo:
        dpd_api_client.reindex_dataproducts()

    # Check that the expected exception is raised
    assert str(excinfo.value) == "Failed to make POST request"


@patch("requests.post")
def test_reindex_dataproducts_success(mock_post: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Mock the POST request and response for a successful reindex."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Call the reindex_dataproducts method
    dpd_api_client.reindex_dataproducts()

    # Check that the POST request was made with the correct URL
    mock_post.assert_called_once_with("http://example.com:8080/reindexdataproducts")


def test_set_endpoint(dpd_api_client: DpdApiClient) -> None:
    """Test the setter method for the endpoint property."""
    # Set a new endpoint
    dpd_api_client.endpoint = "http://new-example.com:8081"

    # Check that the endpoint has been updated correctly
    assert dpd_api_client.endpoint == "http://new-example.com:8081"


def test_set_api_search_term(dpd_api_client: DpdApiClient) -> None:
    """Test the setter method for the api_search_term property."""
    # Set a new api_search_term
    dpd_api_client.api_search_term = "new_metadata_file"

    # Check that the api_search_term has been updated correctly
    assert dpd_api_client.api_search_term == "new_metadata_file"


@patch("ska_pst_send.dpd_api_client.DpdApiClient.metadata_exists")
def test_get_metadata(mock_metadata_exists: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Test the get_metadata method."""
    # Mock metadata_exists to return True
    mock_metadata_exists.return_value = True

    # Call get_metadata
    result: dict = dpd_api_client.get_metadata("file1")

    # Check that the result is a dictionary with "metadata_found" set to True
    assert result == {"metadata_found": True}
