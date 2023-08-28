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
    """Fixture for DpdApiClient."""
    return DpdApiClient(dpd_api_endpoint)


@patch("ska_pst_send.dpd_api_client.requests.get")
def test_metadata_exists_found(mock_get: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Test metadata_exists method when metadata is found."""
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


@patch("ska_pst_send.dpd_api_client.requests.get")
def test_metadata_exists_not_found(mock_get: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Test metadata_exists method when metadata is not found."""
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


@patch("ska_pst_send.dpd_api_client.requests.get")
def test_reindex_dataproducts_error(mock_get: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Test reindex_dataproducts method with an error status code."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    # Explicitly raise an exception when requests.get is called
    mock_get.side_effect = Exception("Failed to make GET request")

    # Perform the reindex
    with pytest.raises(Exception) as excinfo:
        dpd_api_client.reindex_dataproducts()

    # Check that the expected exception is raised
    assert str(excinfo.value) == "Failed to make GET request"


@patch("ska_pst_send.dpd_api_client.requests.get")
def test_reindex_dataproducts_success(mock_get: MagicMock, dpd_api_client: DpdApiClient) -> None:
    """Test reindex_dataproducts method with a successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    # Call the reindex_dataproducts method
    dpd_api_client.reindex_dataproducts()

    # Check that the POST request was made with the correct URL
    mock_get.assert_called_once_with(
        "http://example.com:8080/reindexdataproducts", headers={"accept": "application/json"}
    )


def test_set_endpoint(dpd_api_client: DpdApiClient) -> None:
    """Test the setter method for the endpoint property."""
    # Set a new endpoint
    dpd_api_client.endpoint = "http://new-example.com:8081"

    # Check that the endpoint has been updated correctly
    assert dpd_api_client.endpoint == "http://new-example.com:8081"
