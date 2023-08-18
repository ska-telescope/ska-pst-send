# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""This module defines elements of the pytest test harness shared by all tests."""

import pathlib
import shutil
import uuid
from typing import Callable, Generator, List

import pytest

from ska_pst_send import Scan, VoltageRecorderScan


def create_scan(product: pathlib.Path, scan: pathlib.Path) -> Scan:
    """Return a Scan and associated directory structure."""
    full_path = product / scan
    full_path.mkdir(mode=0o777, parents=True)
    return Scan(product, scan)


def create_voltage_recorder_scan(product: pathlib.Path, scan: pathlib.Path) -> VoltageRecorderScan:
    """Return a VoltageRecorderScan and asscoiated directory structure."""
    full_path = product / scan
    full_path.mkdir(mode=0o777, parents=True)
    return VoltageRecorderScan(product, scan)


def remove_product(product_path: pathlib.Path) -> None:
    """Recursively delete the all file system elements at the path."""
    shutil.rmtree(product_path)


@pytest.fixture
def local_product_path() -> pathlib.Path:
    """Return a local data product path."""
    return pathlib.Path("/tmp/local/product")


@pytest.fixture
def remote_product_path() -> pathlib.Path:
    """Return a remote data product path."""
    return pathlib.Path("/tmp/remote/product")


@pytest.fixture
def scan_id_factory() -> Callable[..., str]:
    """Return a dynamically generated scan_id consisting of a UUID version 4 string."""

    def _factory() -> str:
        return uuid.uuid4()

    return _factory


@pytest.fixture
def eb_id() -> str:
    """Return a valid execution block id."""
    return "eb-m001-20191031-12345"


@pytest.fixture
def ss_id() -> str:
    """Return a valid sub-system id."""
    return "pst-low"


@pytest.fixture
def scan_path(eb_id: str, ss_id: str, scan_id_factory: str) -> pathlib.Path:
    """Return a valid relative scan path."""
    return pathlib.Path(f"{eb_id}/{ss_id}/{scan_id_factory()}")


@pytest.fixture
def scan_path_factory(eb_id: str, ss_id: str, scan_id_factory: str) -> Callable[..., pathlib.Path]:
    """Return a dynamically created relative scan path."""

    def _factory() -> pathlib.Path:
        return pathlib.Path(f"{eb_id}/{ss_id}/{scan_id_factory()}")

    return _factory


@pytest.fixture
def data_files() -> List[str]:
    """Return a list of 4 data filenames."""
    return [
        "data/2023-03-15-03:41:29_0000000000000000_000000.dada",
        "data/2023-03-15-03:41:29_0000000176947200_000001.dada",
        "data/2023-03-15-03:41:29_0000000353894400_000002.dada",
        "data/2023-03-15-03:41:29_0000000530841600_000003.dada",
    ]


@pytest.fixture
def weights_files() -> List[str]:
    """Return a list of 4 weights filenames."""
    return [
        "weights/2023-03-15-03:41:29_0000000000000000_000000.dada",
        "weights/2023-03-15-03:41:29_0000000001497600_000001.dada",
        "weights/2023-03-15-03:41:29_0000000002995200_000002.dada",
        "weights/2023-03-15-03:41:29_0000000004492800_000003.dada",
    ]


@pytest.fixture
def stats_files() -> List[str]:
    """Return a list of 4 stats filenames."""
    return [
        "stats/2023-03-15-03:41:29_0000000000000000_000000.h5",
        "stats/2023-03-15-03:41:29_0000000176947200_000001.h5",
        "stats/2023-03-15-03:41:29_0000000353894400_000002.h5",
        "stats/2023-03-15-03:41:29_0000000530841600_000003.h5",
    ]


@pytest.fixture
def scan_files(data_files: List[str], weights_files: List[str]) -> List[str]:
    """Return a list of data and weights file names, 4 of each."""
    return data_files + weights_files


@pytest.fixture
def scan(local_product_path: pathlib.Path, scan_path: pathlib.Path) -> Scan:
    """Return a Scan fixture, which deletes data paths on finalisation."""
    scan = create_scan(local_product_path, scan_path)
    scan._scan_config_file.touch()
    yield scan
    remove_product(local_product_path)


@pytest.fixture
def scan_factory(local_product_path: pathlib.Path, scan_path_factory: pathlib.Path) -> Callable[..., Scan]:
    """Return a Scan with dynamically generated scan_id."""

    def _factory():
        scan = create_scan(local_product_path, scan_path_factory())
        scan._scan_config_file.touch()
        return scan

    yield _factory


@pytest.fixture
def voltage_recording_scan(
    local_product_path: pathlib.Path, scan_path: pathlib, scan_files: List[str]
) -> Generator[VoltageRecorderScan, None, None]:
    """
    Return a VoltageRecorderScan, initiailsed with 4 data and weights files.

    Fixture deletes data, wieghts and paths on finalisation.
    """
    scan = create_voltage_recorder_scan(local_product_path, scan_path)
    scan._scan_config_file.touch()
    for scan_file in scan_files:
        full_scan_file_path = scan.full_scan_path / scan_file
        full_scan_file_path.mkdir(mode=0o777, parents=True, exist_ok=True)
        full_scan_file_path.touch(mode=0o777)

    yield scan
    remove_product(local_product_path)


@pytest.fixture
def voltage_recording_scan_factory(
    local_product_path: pathlib.Path, scan_path_factory: pathlib, scan_files: List[str]
) -> Generator[VoltageRecorderScan, None, None]:
    """Return a Voltage RecorderScan, with dynamically generated scan_id and 4 data and weights files."""

    def _factory():
        scan = create_voltage_recorder_scan(local_product_path, scan_path_factory())
        scan._scan_config_file.touch()
        for scan_file in scan_files:
            full_scan_file_path = scan.full_scan_path / scan_file
            full_scan_file_path.mkdir(mode=0o777, parents=True, exist_ok=True)
            full_scan_file_path.touch(mode=0o777)
        return scan

    yield _factory


@pytest.fixture
def local_remote_scans(
    local_product_path: pathlib.Path,
    remote_product_path: pathlib.Path,
    scan_path: pathlib,
    scan_files: List[str],
) -> (VoltageRecorderScan, VoltageRecorderScan):
    """
    Return a local and remote VoltageRecorderScan.

    The local scan is initiailsed with 4 data and weights files, the remote scan with nothing.
    The fixture removes the local and remote files and directories on finalisation.
    """
    local_scan = create_voltage_recorder_scan(local_product_path, scan_path)
    local_scan._scan_config_file.touch()
    for scan_file in scan_files:
        full_scan_file_path = local_scan.full_scan_path / scan_file
        full_scan_file_path.parent.mkdir(mode=0o777, parents=True, exist_ok=True)
        full_scan_file_path.touch(mode=0o777)

    remote_scan = create_voltage_recorder_scan(remote_product_path, scan_path)

    yield (local_scan, remote_scan)
    remove_product(local_product_path)
    remove_product(remote_product_path)


@pytest.fixture
def three_local_scans(voltage_recording_scan_factory: VoltageRecorderScan) -> List[VoltageRecorderScan]:
    """
    Return 3 VoltageRecorderScans that are dyanmically generated with unique scan_ids.

    The fixture deletes the data files and paths upon finalisation.
    """
    scans = []
    scans.append(voltage_recording_scan_factory())
    scans.append(voltage_recording_scan_factory())
    scans.append(voltage_recording_scan_factory())
    data_product_path = scans[0].data_product_path

    yield scans

    remove_product(data_product_path)
