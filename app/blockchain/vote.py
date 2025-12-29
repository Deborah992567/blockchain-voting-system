from app.blockchain.web3 import w3
from app.blockchain.abi import ELECTION_ABI
from app.utils.logger import logger as base_logger

logger = base_logger.bind(context="blockchain.vote")

def cast_vote(contract_address: str, voter_private_key: str, candidate_id: int):
    voter_address = w3.eth.account.from_key(voter_private_key).address

    contract = w3.eth.contract(
        address=contract_address,
        abi=ELECTION_ABI
    )

    tx = contract.functions.vote(candidate_id).build_transaction({
        "from": voter_address,
        "nonce": w3.eth.get_transaction_count(voter_address),
        "gas": 200000,
        "gasPrice": w3.eth.gas_price
    })

    signed = w3.eth.account.sign_transaction(tx, voter_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    logger.info("Vote transaction sent", tx_hash=tx_hash.hex(), contract_address=contract_address, candidate_id=candidate_id)
    return tx_hash.hex()
