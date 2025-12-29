from app.blockchain.web3 import w3
from app.blockchain.abi import ELECTION_ABI

def get_results(contract_address: str, candidate_count: int):
    contract = w3.eth.contract(
        address=contract_address,
        abi=ELECTION_ABI
    )

    results = []

    for i in range(candidate_count):
        name, votes = contract.functions.getCandidate(i).call()
        results.append({
            "candidate": name,
            "votes": votes
        })

    return results
