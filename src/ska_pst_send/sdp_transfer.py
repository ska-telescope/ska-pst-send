# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

"""Module class for main PST to SDP Transfer application."""
import logging
import pathlib
import sys
import threading
from signal import SIGINT, signal
from typing import Any

from .scan_manager import ScanManager
from .scan_process import ScanProcess
from .scan_transfer import ScanTransfer
from .voltage_recorder_scan import VoltageRecorderScan


def process_scans(
    local_path: pathlib.Path, remote_path: pathlib.Path, ska_subsystem: str, verbose: bool, **kwargs: Any
) -> None:
    """Primary processing method for the PST to SDP transfer."""
    LOGGING_LEVEL = logging.DEBUG if verbose else logging.INFO
    LOG_FORMAT = "%(asctime)s : %(levelname)5s : %(msg)s : %(filename)s:%(lineno)s %(funcName)s()"
    logging.basicConfig(format=LOG_FORMAT, level=LOGGING_LEVEL)

    logger = logging.getLogger(__name__)

    cond = threading.Condition()
    persist = True

    # handle SIGINT gracefully to prevent partially transferred files
    def signal_handler(sig, frame):
        sys.stderr.write("CTRL + C pressed\n")
        persist = False
        with cond:
            cond.notify_all()

    signal(SIGINT, signal_handler)

    logger.debug(f"local_path={local_path} remote_path={remote_path}")
    scan_manager = ScanManager(local_path, ska_subsystem, logger)

    while persist:

        # get the oldest available scan
        local_scan = scan_manager.get_oldest_scan()

        if local_scan is not None:

            # construct a remote scan object for comparison
            remote_scan = VoltageRecorderScan(remote_path, local_scan.relative_scan_path, logger)

            # perform post-processing on the scan to generate output files for transfer
            scan_process = ScanProcess(local_scan, cond, logger)
            scan_process.start()

            # perform the file transfer of output files to the remote storage
            scan_transfer = ScanTransfer(local_scan, remote_scan, cond, logger)
            scan_transfer.start()

            logger.info(f"Processing {local_scan.relative_scan_path}")
            scan_process.join()
            scan_transfer.join()

            if scan_process.completed and scan_transfer.completed:
                logger.debug(
                    f"scan={local_scan.relative_scan_path} processed={scan_process.completed} "
                    + f"transferred={scan_transfer.completed}"
                )

                logger.debug(f"notifying data product dashbord for {remote_scan.relative_scan_path}")

                # TODO notify the data product dashboard via the client API
                dashboard_upload = False
                if dashbaord_upload:
                    local_scan.delete_scan()

            else:
                persist = False

        with cond:
            if cond.wait(timeout=10):
                # condition variable was triggered
                logger.info("SDPTransfer exiting on command")
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
        default="http://127.0.0.1:8888",
        help="endpoint for the SDP Data Product Dashboard REST API",
    )
    p.add_argument("-v", "--verbose", action="store_true")

    args = p.parse_args()
    try:
        process_scans(
            pathlib.Path(args.local_path), pathlib.Path(args.remote_path), args.ska_subsystem, args.verbose
        )
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
