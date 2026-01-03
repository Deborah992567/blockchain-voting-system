from web3 import Web3
from app.config import settings
from app.utils.logger import logger as base_logger
import os

logger = base_logger.bind(context="blockchain.web3")

# Resolve a safe rpc url (backwards compat with BLOCKCHAIN_RPC_URL)
rpc_url = getattr(settings, "BLOCKCHAIN_RPC_URL", getattr(settings, "RPC_URL", os.getenv("RPC_URL", "http://127.0.0.1:7545")))

w3 = Web3(Web3.HTTPProvider(rpc_url))

# During tests or when using an in-memory DB, skip the live connection check
if os.getenv("TESTING") == "1" or os.getenv("DATABASE_URL", "").startswith("sqlite"):
    logger.info("Skipping blockchain connectivity check in test mode", rpc_url=rpc_url)
else:
    if not w3.is_connected():
        logger.error("Blockchain not connected", rpc_url=rpc_url)
        raise RuntimeError("Blockchain not connected")
    else:
        logger.info("Connected to blockchain", rpc_url=rpc_url)
