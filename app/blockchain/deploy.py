from web3 import Web3
from app.blockchain.web3 import w3
from app.blockchain.abi import ELECTION_ABI
from app.config import settings
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="blockchain.deploy")

BYTECODE = "0x..."  # from compiled Solidity

def deploy_election(candidate_names: list[str]) -> str:
    contract = w3.eth.contract(abi=ELECTION_ABI, bytecode=BYTECODE)

    tx = contract.constructor(candidate_names).build_transaction({
        "from": settings.ADMIN_ADDRESS,
        "nonce": w3.eth.get_transaction_count(settings.ADMIN_ADDRESS),
        "gas": 3000000,
        "gasPrice": w3.eth.gas_price
    })

    signed = w3.eth.account.sign_transaction(tx, settings.ADMIN_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    logger.info("Contract deployed", contract_address=receipt.contractAddress, tx_hash=tx_hash.hex())

    return receipt.contractAddress
