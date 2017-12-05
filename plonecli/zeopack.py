# -*- coding: utf-8 -*-
from ZEO.ClientStorage import ClientStorage
from ZEO.Exceptions import ClientDisconnected

import logging
import os
import socket
import sys


def _main(host, port, unix=None, days=1, username=None, password=None,
          realm=None, blob_dir=None, storage='1', shared_blob_dir=True):
    if unix is not None:
        addr = unix
    else:
        if host is None:
            host = socket.gethostname()
        addr = host, int(port)

    if blob_dir:
        blob_dir = os.path.abspath(blob_dir)

    cs = None
    logger = logging.getLogger(__name__)
    try:
        # We do not want to wait until a zeoserver is up and running; it
        # should already be running, so wait=False
        cs = ClientStorage(
            addr, storage=storage, wait=False, read_only=True,
            username=username, password=password, realm=realm,
            blob_dir=blob_dir, shared_blob_dir=shared_blob_dir,
        )
        if not cs.is_connected():
            logger.error("Could not connect to zeoserver. Please make sure it "
                         "is running.")
            sys.exit(1)
        try:
            # The script should not exit until the packing is done.
            # => wait=True
            cs.pack(wait=True, days=int(days))
        except ClientDisconnected:
            logger.error("Disconnected from zeoserver. Please make sure it "
                         "is still running.")
            sys.exit(1)
    finally:
        if cs is not None:
            cs.close()


def main(*args, **kw):
    root_logger = logging.getLogger()
    old_level = root_logger.getEffectiveLevel()
    logging.getLogger().setLevel(logging.WARNING)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(name)s %(levelname)s %(message)s"))
    logging.getLogger().addHandler(handler)
    try:
        _main(*args, **kw)
    finally:
        logging.getLogger().setLevel(old_level)
        logging.getLogger().removeHandler(handler)


if __name__ == "__main__":
    main()
