# -*- coding: utf-8 -*-
#
# This file is part of the SKA PST SEND project
#
# Distributed under the terms of the BSD 3-clause new license.
# See LICENSE for more info.

import logging
import pathlib
import sys
import threading
import time
from signal import SIGINT, signal
from typing import Any

from .scan_manager import ScanManager
from .scan_process import ScanProcess
from .scan_transfer import ScanTransfer
from .scan import VoltageRecorderScan


def process_scans(args: Any) -> None:

    LOGGING_LEVEL = logging.INFO
    LOG_FORMAT = "%(asctime)s : %(levelname)5s : %(msg)s : %(filename)s:%(lineno)s %(funcName)s()"
    logging.basicConfig(format=LOG_FORMAT, level=LOGGING_LEVEL)

    logger = logging.getLogger(__name__)

    # handle SIGINT gracefully to prevent partially transferred files
    quit_event = threading.Event()

    def signal_handler(sig, frame):
        sys.stderr.write("CTRL + C pressed\n")
        quit_event.set()

    signal(SIGINT, signal_handler)

    local_path = pathlib.Path(args["local_path"])
    remote_path = pathlib.Path(args["remote_path"])
    ska_subsystem = args["ska_subsystem"]
    logger.debug(f"local_path={local_path} remote_path={remote_path}")

    scan_manager = ScanManager(local_path, ska_subsystem, logger)

    while not quit_event.isSet():

        # refresh the list of scans
        scan_manager.refresh_scans()

        # get the oldest scan in the list
        local_scan = scan_manager.get_oldest_scan()

        # construct a remote scan object for comparison
        remote_scan = VoltageRecorderScan(remote_path, local_scan.relative_scan_path, logger)

        # perform post-processing on the scan to generate output files for transfer
        scan_process = ScanProcess(local_scan, quit_event, logger)
        scan_process.start()

        # perform the file transfer of output files to the remote storage
        scan_transfer = ScanTransfer(local_scan, remote_scan, quit_event, logger)
        scan_transfer.start()

        # wait for all processing of the scan to be completed, could exit early if the quit_event has been set
        while scan_process.is_alive():
            time.sleep(1)
        scan_process.join()

        # wait for the scan transfer to be completed, could exit early if quit_event has been set
        while scan_transfer.is_alive():
            time.sleep(1)
        scan_transfer.join()

        all_processed = scan_process.get_unprocessed_file() == None
        all_transferred = len(scan_transfer.get_untransferred_files()) == 0
        logger.debug(
            f"scan={local_scan.relative_scan_path} processed={all_processed} "
            + f"transferred={all_transferred} quit_event={quit_event.isSet()}"
        )

        if quit_event.isSet():
            return

        # if all_processed and all_transferred:
        # TODO notify the data product dashboard via the client API


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

    args = vars(p.parse_args())
    try:
        process_scans(args)
        sys.exit(0)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
