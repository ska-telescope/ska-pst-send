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
from typing import Any, Callable, Generator, List

import pytest

from ska_pst_send.scan import Scan
from ska_pst_send.voltage_recorder_scan import VoltageRecorderScan


def create_scan(product: pathlib.Path, scan: pathlib.Path) -> Scan:
    full_path = product / scan
    full_path.mkdir(mode=0o777, parents=True)
    return Scan(product, scan)


def create_voltage_recorder_scan(product: pathlib.Path, scan: pathlib.Path) -> VoltageRecorderScan:
    full_path = product / scan
    full_path.mkdir(mode=0o777, parents=True)
    return VoltageRecorderScan(product, scan)


def remove_product(product_path: pathlib.Path) -> None:
    shutil.rmtree(product_path)


@pytest.fixture
def local_product_path() -> pathlib.Path:
    return pathlib.Path("/tmp/local/product")


@pytest.fixture
def prepare_local_product() -> pathlib.Path:
    return pathlib.Path("/tmp/local/product")


@pytest.fixture
def remote_product_path() -> pathlib.Path:
    return pathlib.Path("/tmp/remote/product")


@pytest.fixture
def scan_id_factory() -> str:
    def _factory() -> str:
        return uuid.uuid4()
    return _factory


@pytest.fixture
def eb_id() -> str:
    return "eb-m001-20191031-12345"


@pytest.fixture
def ss_id() -> str:
    return "pst-low"


@pytest.fixture
def scan_path(eb_id: str, ss_id: str, scan_id_factory: str) -> pathlib.Path:
    return pathlib.Path(f"{eb_id}/{ss_id}/{scan_id_factory()}")


@pytest.fixture
def scan_path_factory(eb_id: str, ss_id: str, scan_id_factory: str) -> pathlib.Path:
    def _factory() -> pathlib.Path:
        return pathlib.Path(f"{eb_id}/{ss_id}/{scan_id_factory()}")
    return _factory


@pytest.fixture
def data_files() -> List[str]:
    return [
        "data/2023-03-15-03:41:29_0000000000000000_000000.dada",
        "data/2023-03-15-03:41:29_0000000176947200_000001.dada",
        "data/2023-03-15-03:41:29_0000000353894400_000002.dada",
        "data/2023-03-15-03:41:29_0000000530841600_000003.dada",
    ]


@pytest.fixture
def weights_files() -> List[str]:
    return [
        "weights/2023-03-15-03:41:29_0000000000000000_000000.dada",
        "weights/2023-03-15-03:41:29_0000000001497600_000001.dada",
        "weights/2023-03-15-03:41:29_0000000002995200_000002.dada",
        "weights/2023-03-15-03:41:29_0000000004492800_000003.dada",
    ]


@pytest.fixture
def stats_files() -> List[str]:
    return [
        "stats/2023-03-15-03:41:29_0000000000000000_000000.h5",
        "stats/2023-03-15-03:41:29_0000000176947200_000001.h5",
        "stats/2023-03-15-03:41:29_0000000353894400_000002.h5",
        "stats/2023-03-15-03:41:29_0000000530841600_000003.h5",
    ]


@pytest.fixture
def scan_files(data_files: List[str], weights_files: List[str]) -> List[str]:
    return data_files + weights_files


@pytest.fixture
def scan(local_product_path: pathlib.Path, scan_path: pathlib.Path) -> Scan:
    """Creates a simulated scan in the specified directories."""
    scan = create_scan(local_product_path, scan_path)
    scan._scan_config_file.touch()
    yield scan
    remove_product(local_product_path)


@pytest.fixture
def voltage_recording_scan(
    local_product_path: pathlib.Path, scan_path: pathlib, scan_files: List[str]
) -> Generator[VoltageRecorderScan, None, None]:
    """Creates a simulated voltage recording in the specified directories."""
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
    """Creates a simulated voltage recording in the specified directories."""
    def _factory():
        scan = create_voltage_recorder_scan(local_product_path, scan_path_factory())
        scan._scan_config_file.touch()
        for scan_file in scan_files:
            full_scan_file_path = scan.full_scan_path / scan_file
            full_scan_file_path.mkdir(mode=0o777, parents=True, exist_ok=True)
            full_scan_file_path.touch(mode=0o777)
        return scan
    yield _factory
    # remove_product(local_product_path)


@pytest.fixture
def local_remote_scans(
    local_product_path: pathlib.Path,
    remote_product_path: pathlib.Path,
    scan_path: pathlib,
    scan_files: List[str],
) -> (VoltageRecorderScan, VoltageRecorderScan):
    """Creates a simulated local scan and an empty remote scan in the specified directories."""
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
    """Generate a list of 3 VoltageRecorderScans."""
    scans = []
    scans.append(voltage_recording_scan_factory())
    scans.append(voltage_recording_scan_factory())
    scans.append(voltage_recording_scan_factory())
    data_product_path = scans[0].data_product_path

    yield scans

    remove_product(data_product_path)
 

# @pytest.fixture
# def scan_manager_with_scans(voltage_recording_scan_factory: VoltageRecorderScan, ss_id: str) -> ScanManager:
#     """Creates 3 random scans and returns a scan_manager instance."""
#     scans = []
#     scans.append(voltage_recording_scan_factory())
#     scans.append(voltage_recording_scan_factory())
#     scans.append(voltage_recording_scan_factory())

#     data_product_path = scans[0].data_product_path
#     scan_manager = ScanManager(data_product_path, ss_id)

#     yield scan_manager
#     remove_product(data_product_path)
