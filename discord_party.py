#!/usr/bin/env python3
"""
Deprecated launcher shim.

The party runtime has been unified into discord_main.py.
This file remains as a compatibility entrypoint so existing service scripts
fail fast with a clear migration message.
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EH_PartyLauncher")


if __name__ == "__main__":
    logger.error(
        "discord_party.py is retired. Start the unified bot with: python discord_main.py"
    )
    raise SystemExit(1)
