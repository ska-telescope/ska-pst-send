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
from signal import SIGINT, signal

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
        verbose: bool,
    ) -> None:
        """Initialise an SdpTransfer object."""
        self.local_path = local_path
        self.remote_path = remote_path
        self.ska_subsystem = ska_subsystem
        self.data_product_dashboard = data_product_dashboard

        logging_level = logging.DEBUG if verbose else logging.INFO
        log_format = "%(asctime)s : %(levelname)5s : %(msg)s : %(filename)s:%(lineno)s %(funcName)s()"
        logging.basicConfig(format=log_format, level=logging_level)
        self.logger = logging.getLogger(__name__)
        self.cond = threading.Condition()
        self.cond_timeout = 10
        self.persist = True

    def process(self: SdpTransfer) -> None:
        """Primary processing method for the PST to SDP transfer."""
        self.logger.debug(f"local_path={self.local_path} remote_path={self.remote_path}")
        scan_manager = ScanManager(self.local_path, self.ska_subsystem, self.logger)

        self.persist = True
        while self.persist:

            # get the oldest available scan
            local_scan = scan_manager.get_oldest_scan()

            if local_scan is not None:

                # construct a remote scan object for comparison
                remote_scan = VoltageRecorderScan(
                    self.remote_path, local_scan.relative_scan_path, self.logger
                )

                # perform post-processing on the scan to generate output files for transfer
                scan_process = ScanProcess(local_scan, self.cond, self.logger)
                scan_process.start()

                # perform the file transfer of output files to the remote storage
                scan_transfer = ScanTransfer(local_scan, remote_scan, self.cond, self.logger)
                scan_transfer.start()

                self.logger.info(f"Processing {local_scan.relative_scan_path}")
                scan_process.join()
                scan_transfer.join()

                if scan_process.completed and scan_transfer.completed:
                    self.logger.debug(
                        f"scan={local_scan.relative_scan_path} processed={scan_process.completed} "
                        + f"transferred={scan_transfer.completed}"
                    )

                    self.logger.debug(f"notifying data product dashbord for {remote_scan.relative_scan_path}")

                    if self.data_product_dashboard == "disabled":
                        local_scan.delete_scan()
                        self.persist = False
                    else:
                        # TODO notify the data product dashboard via the client API
                        self.logger.warning("SDP Data Product Dashboard notification not yet implemented")
                else:
                    self.persist = False

            if self.persist:
                with self.cond:
                    if self.cond.wait(timeout=self.cond_timeout):
                        # condition variable was triggered
                        self.logger.info("SDPTransfer exiting on command")
                        return


def main() -> None:
    """Parse command line arguments and execute the main processing loop."""
    import argparse
    import sys
    import traceback

    # do arg parsing here
    p = argparse.ArgumentParser()
    p.add_argument(
        "local_path",
        type=str,
        help="local/source filesystem path in which PST data products are found",
    )
    p.add_argument(
        "remote_path",
        type=str,
        help="remote/dest filesystem path to which PST data products should be written",
    )
    p.add_argument("ska_subsystem", type=str, default="pst-low", help="ska-subsystem")
    p.add_argument(
        "--data_product_dashboard",
        type=str,
        default="disabled",
        help="endpoint for the SDP Data Product Dashboard REST API [e.g. http://127.0.0.1:8888/api]",
    )
    p.add_argument("-v", "--verbose", action="store_true")

    args = p.parse_args()

    sdp_transfer = SdpTransfer(
        pathlib.Path(args.local_path),
        pathlib.Path(args.remote_path),
        args.ska_subsystem,
        args.data_product_dashboard,
        args.verbose,
    )

    # handle SIGINT gracefully to prevent partially transferred files
    def signal_handler(sig, frame):
        sys.stderr.write("CTRL + C pressed\n")
        sdp_transfer.persist = False
        with sdp_transfer.cond:
            sdp_transfer.cond.notify_all()

    signal(SIGINT, signal_handler)

    try:
        sdp_transfer.process()
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
