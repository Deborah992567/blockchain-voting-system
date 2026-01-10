from web3 import Web3
from app.config import settings
from app.utils.logger import logger as base_logger
import os

logger = base_logger.bind(context="blockchain.web3")

# Resolve a safe rpc url (backwards compat with BLOCKCHAIN_RPC_URL)
rpc_url = getattr(settings, "BLOCKCHAIN_RPC_URL", getattr(settings, "RPC_URL", os.getenv("RPC_URL", "http://127.0.0.1:7545")))

w3 = Web3(Web3.HTTPProvider(rpc_url))

# During tests, development, or when using an in-memory DB, skip the live connection check
is_testing = os.getenv("TESTING") == "1"
is_sqlite = os.getenv("DATABASE_URL", "").startswith("sqlite")
is_dev = os.getenv("ENV", "development") == "development"

if is_testing or is_sqlite or is_dev:
    logger.info(f"Skipping blockchain connectivity check (testing={is_testing}, sqlite={is_sqlite}, dev={is_dev})", rpc_url=rpc_url)
else:
    if not w3.is_connected():
        logger.warning("Blockchain not connected, but proceeding anyway (blockchain operations will fail)", rpc_url=rpc_url)
    else:
        logger.info("Connected to blockchain", rpc_url=rpc_url)

