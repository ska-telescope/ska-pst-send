# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for main PST to SDP Transfer application."""
from __future__ import annotations

import logging
import pathlib
import threading
from signal import SIGINT, SIGTERM, signal
from types import FrameType
from typing import Any, Optional

import backoff
from ska_ser_logging import configure_logging

from .dpd_api_client import DpdApiClient
from .scan import Scan
from .scan_manager import ScanManager
from .scan_process import ScanProcess
from .scan_transfer import ScanTransfer
from .voltage_recorder_scan import VoltageRecorderScan


class SdpTransfer:
    """Class to manage the main execution loop of the PST to SDP transfer."""

    def __init__(
        self: SdpTransfer,
        local_path: pathlib.Path,
        remote_path: pathlib.Path,
        ska_subsystem: str,
        data_product_dashboard: str,
        scan_timeout: float,
        verbose: bool = False,
    ) -> None:
        """
        Initialise an SdpTransfer object.

        :param local_path: absolute path to the local (PST) data product directory
        :param remote_path: absolute path to the remote (SDP) data product directory
        :param subsystem: the PST instance, one of pst-low or pst-mid
        :param data_product_dashboard: the URI for connection to the SDP Data Product Dashboard API.
        :param logger: the logger instance to use.
        :param verbose: verbosity flag for logging, if true use logging.DEBUG
        """
        self.local_path = local_path
        self.remote_path = remote_path
        self.ska_subsystem = ska_subsystem
        self.data_product_dashboard = data_product_dashboard
        self.scan_timeout = scan_timeout
        if self.data_product_dashboard != "disabled":
            self._dpd_api_client = DpdApiClient(endpoint=self.data_product_dashboard)

        logging_level = logging.DEBUG if verbose else logging.INFO
        configure_logging(level=logging_level)

        self.logger = logging.getLogger(__name__)
        self._cond = threading.Condition()
        self._cond_timeout = 10
        self._persist = True

    def interrrupt_processing(self: SdpTransfer) -> None:
        """Interrupt the processing and transferring of the scan."""
        self._persist = False
        with self._cond:
            self._cond.notify_all()

    def _ensure_scan_indexed_in_dpd(self: SdpTransfer, local_scan: Scan, remote_scan: Scan) -> None:
        assert local_scan.data_product_file_exists(), f"Expected {local_scan.data_product_file} to exist"
        assert remote_scan.data_product_file_exists(), f"Expected {remote_scan.data_product_file} to exist"

        self.logger.debug(f"SDP Data Product Dashboard endpoint={self.data_product_dashboard}")
        self._dpd_api_client.reindex_dataproducts()

        search_value = str(remote_scan.data_product_file.relative_to(self.remote_path))
        self.logger.debug(f"search_value={search_value}")

        def _on_giveup(*args: Any, **kwargs: Any) -> None:
            self.logger.error(f"Metadata not found. Retaining {local_scan.full_scan_path}")

        def _on_success(*args: Any, **kwargs: Any) -> None:
            self.logger.debug("Metadata found. Calling local_scan.delete_scan()")
            local_scan.delete_scan()

        @backoff.on_predicate(
            backoff.expo,
            on_giveup=_on_giveup,
            on_success=_on_success,
            max_time=120.0,
        )
        def _check_scan_indexed() -> bool:
            return self._dpd_api_client.metadata_exists(search_value=search_value)

        _check_scan_indexed()

    def _proccess_voltage_recorder_scan(self: SdpTransfer, local_scan: VoltageRecorderScan) -> None:
        # construct a remote scan object for comparison
        remote_scan = VoltageRecorderScan(self.remote_path, local_scan.relative_scan_path, logger=self.logger)

        # reset processing and transfer states needs to be done before threads are started
        local_scan.processing_failed = False
        local_scan.transfer_failed = False

        # perform post-processing on the scan to generate output files for transfer
        scan_process = ScanProcess(local_scan, self._cond, logger=self.logger)
        scan_process.start()

        # perform the file transfer of output files to the remote storage
        scan_transfer = ScanTransfer(local_scan, remote_scan, self._cond, logger=self.logger)
        scan_transfer.start()

        self.logger.info(f"Processing scan {local_scan.relative_scan_path}")
        scan_process.join()
        scan_transfer.join()

        if scan_process.completed and scan_transfer.completed:
            self.logger.info(f"Completed processing and transfer of scan {local_scan.relative_scan_path}")

            if self.data_product_dashboard == "disabled":
                self.logger.info(f"deleting local copy of {local_scan.relative_scan_path}")
                local_scan.delete_scan()
            else:
                self._ensure_scan_indexed_in_dpd(local_scan=local_scan, remote_scan=remote_scan)

        local_scan.update_modified_time()

    def process(self: SdpTransfer) -> None:
        """Primary processing method for the PST to SDP transfer."""
        self.logger.debug(f"local_path={self.local_path} remote_path={self.remote_path}")
        scan_manager = ScanManager(
            self.local_path, self.ska_subsystem, scan_timeout=self.scan_timeout, logger=self.logger
        )

        self._persist = True
        while self._persist:
            # get next scan to process
            local_scan = scan_manager.next_unprocessed_scan()

            if local_scan is not None:
                self._proccess_voltage_recorder_scan(local_scan)

            if self._persist:
                with self._cond:
                    if self._cond.wait(timeout=self._cond_timeout):
                        self.logger.info("SDPTransfer exiting on command")
                        return

    @property
    def dpd_api_client(self: SdpTransfer) -> Optional[DpdApiClient]:
        """Returns DpdApiClient or None if data_product_dashboard is 'disabled'."""
        return self._dpd_api_client


def main() -> None:
    """Parse command line arguments and execute the main processing loop."""
    import argparse
    import sys
    import traceback

    # do arg parsing here
    p = argparse.ArgumentParser()
    p.add_argument(
        "local_path",
        type=pathlib.Path,
        help="local/source filesystem path in which PST data products are found",
    )
    p.add_argument(
        "remote_path",
        type=pathlib.Path,
        help="remote/dest filesystem path to which PST data products should be written",
    )
    p.add_argument("ska_subsystem", type=str, default="pst-low", help="ska-subsystem")
    p.add_argument(
        "--data_product_dashboard",
        type=str,
        default="disabled",
        help="endpoint for the SDP Data Product Dashboard REST API [e.g. http://127.0.0.1:8888]",
    )
    p.add_argument(
        "--scan-timeout",
        type=float,
        help="time out, in seconds, to mark scan as being inactive. Default is 300s",
        default=300.0,
    )
    p.add_argument("-v", "--verbose", action="store_true")

    args = vars(p.parse_args())

    sdp_transfer = SdpTransfer(**args)

    # handle SIGINT gracefully to prevent partially transferred files
    def signal_handler(signal: int, frame: FrameType | None) -> None:
        sys.stderr.write("CTRL + C pressed\n")
        sdp_transfer.interrrupt_processing()

    signal(SIGINT, signal_handler)
    signal(SIGTERM, signal_handler)

    try:
        sdp_transfer.process()
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
