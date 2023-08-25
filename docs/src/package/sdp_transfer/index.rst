SDP Transfer App
=================

::

    usage: sdp_transfer [-h] [--data_product_dashboard DATA_PRODUCT_DASHBOARD] [-v] local_path remote_path ska_subsystem

    positional arguments:
      local_path            local/source filesystem path in which PST data products are found
      remote_path           remote/dest filesystem path to which PST data products should be written
      ska_subsystem         ska-subsystem

    options:
      -h, --help            show this help message and exit
      --data_product_dashboard DATA_PRODUCT_DASHBOARD
                            endpoint for the SDP Data Product Dashboard REST API [e.g. http://127.0.0.1:8888]
      -v, --verbose

Classes
-------

.. autoclass:: ska_pst_send.sdp_transfer.SdpTransfer
  :members:

.. autoclass:: ska_pst_send.scan_manager.ScanManager
  :members:

.. autoclass:: ska_pst_send.scan_process.ScanProcess
  :members:

.. autoclass:: ska_pst_send.scan_transfer.ScanTransfer
  :members:

.. autoclass:: ska_pst_send.scan.Scan
  :members:

.. autoclass:: ska_pst_send.voltage_recorder_scan.VoltageRecorderScan
  :members:

.. autoclass:: ska_pst_send.voltage_recorder_file.VoltageRecorderFile
  :members:
