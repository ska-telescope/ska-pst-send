# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module contains the pytest tests for the DpdApiClient."""

from unittest.mock import Mock, patch

import pytest

from ska_pst_send.dpd_api_client import DpdApiClient


@pytest.fixture
def dpd_api_client():
    """Fixture for DpdApiClient."""
    return DpdApiClient("http://example.com:8080")


@patch("requests.get")
def test_search_metadata_found(mock_get, dpd_api_client):
    """Mock the GET request and response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"metadata_file": "file1"},
        {"metadata_file": "file2"},
    ]
    mock_get.return_value = mock_response

    # Perform the search
    result = dpd_api_client.search_metadata("file1")

    # Check that the GET request was made with the correct URL
    mock_get.assert_called_once_with(
        "http://example.com:8080/dataproductlist", headers={"accept": "application/json"}
    )

    # Check that the result is True since "file1" was found in the response
    assert result is True


@patch("requests.get")
def test_search_metadata_not_found(mock_get, dpd_api_client):
    """Mock the GET request and response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"metadata_file": "file1"},
        {"metadata_file": "file2"},
    ]
    mock_get.return_value = mock_response

    # Perform the search for a non-existent file
    result = dpd_api_client.search_metadata("file3")

    # Check that the GET request was made with the correct URL
    mock_get.assert_called_once_with(
        "http://example.com:8080/dataproductlist", headers={"accept": "application/json"}
    )

    # Check that the result is False since "file3" was not found in the response
    assert result is False


@patch("requests.get")
def test_search_metadata_error(mock_get, dpd_api_client):
    """Mock the GET request and response with an error status code."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    # Perform the search
    with pytest.raises(Exception) as excinfo:
        dpd_api_client.search_metadata("file1")

    # Check that an exception is raised due to the error response
    assert "Failed to search for data products. Status code: 500" in str(excinfo.value)


@patch("requests.post")
def test_reindex_dataproducts_success(mock_post, dpd_api_client):
    """Mock the POST request and response for a successful reindex."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    # Call the reindex_dataproducts method
    result = dpd_api_client.reindex_dataproducts()

    # Check that the POST request was made with the correct URL
    mock_post.assert_called_once_with("http://example.com:8080/reindexdataproducts")

    # Check that the result is the JSON response from the API
    assert result == mock_response.json()


@patch("requests.post")
def test_reindex_dataproducts_error(mock_post, dpd_api_client):
    """Mock the POST request and response with an error status code."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_post.return_value = mock_response

    # Perform the reindex
    with pytest.raises(Exception) as excinfo:
        dpd_api_client.reindex_dataproducts()

    # Check that an exception is raised due to the error response
    assert "Failed to reindex data products. Status code: 500" in str(excinfo.value)


def test_set_endpoint(dpd_api_client):
    """Test the setter method for the endpoint property."""
    # Set a new endpoint
    dpd_api_client.endpoint = "http://new-example.com:8081"

    # Check that the endpoint has been updated correctly
    assert dpd_api_client.endpoint == "http://new-example.com:8081"


def test_set_api_search_term(dpd_api_client):
    """Test the setter method for the api_search_term property."""
    # Set a new api_search_term
    dpd_api_client.api_search_term = "new_metadata_file"

    # Check that the api_search_term has been updated correctly
    assert dpd_api_client.api_search_term == "new_metadata_file"
