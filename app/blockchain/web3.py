from web3 import Web3
from app.config import settings
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="blockchain.web3")

w3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_RPC_URL))

if not w3.is_connected():
    logger.error("Blockchain not connected", rpc_url=settings.BLOCKCHAIN_RPC_URL)
    raise RuntimeError("Blockchain not connected")
else:
    logger.info("Connected to blockchain", rpc_url=settings.BLOCKCHAIN_RPC_URL)
