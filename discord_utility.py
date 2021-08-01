from web3 import Web3
from web3 import exceptions
from web3.middleware import geth_poa_middleware

import time
import re


# hex contract address for pancake router v2
x_pcs_routerV2_contract_addr = '0x10ed43c718714eb63d5aa57b78b54704e256024e'

# hex contract address for pancake bunny zap
x_pcb_zap_contract_addr = '0xdc2bbb0d33e0e7dea9f5b98f46edbac823586a0c'

# hex contract address for qbt without 0x
qbt_contract_addr = '17b7163cf1dbd286e262ddc68b553d899b93f526'

# pcs qbt / bnb liq. pair contract address without 0x
pcs_qbt_bnb_pair_contract = '67efef66a55c4562144b9acfcfbc62f9e4269b3e'

# each paramter is 64 bytes
param_len = 64

# method id len
method_id_len = 10

def wait_and_get_transaction(w3, transaction):
    retries = 20
    while transaction.to is None and retries > 0:
        time.sleep(1)
        transaction = w3.eth.get_transaction(transaction.hash.hex())
        retries = retries - 1
        print('waiting pending transaction: ' + transaction.hash.hex())

    return transaction

def get_transaction_input_param(transaction, param_index):
    param_start_index = (param_len * param_index) + method_id_len
    param = transaction.input[param_start_index : param_start_index + param_len]
    return param

def get_transaction_input_last_param(transaction):
    return transaction.input[param_len * -1 :]

def get_pcs_exact_token_for_token_swap_info(transaction, token_addr):
    method_id = '0x38ed1739'
    if not (transaction.to is not None 
            and transaction.to.lower() == x_pcs_routerV2_contract_addr.lower()
            and re.search(method_id, transaction.input, re.IGNORECASE) 
            and re.search(token_addr, transaction.input, re.IGNORECASE)):
        return None

    from_token = get_transaction_input_param(transaction, 6)
    to_token = get_transaction_input_last_param(transaction)

    # convert hex number to decimal and delete by the decimals after the delimiter - 18
    amount = int(get_transaction_input_param(transaction, 0), 16) / pow(10, 18)

    operation = 'sell'
    if re.search(token_addr, to_token, re.IGNORECASE):
        operation = 'buy'

    return (operation, amount)

def get_pcs_token_for_exact_token_swap_info(transaction, token_addr):
    method_id = '0x8803dbee'
    if not (transaction.to is not None 
            and transaction.to.lower() == x_pcs_routerV2_contract_addr.lower()
            and re.search(method_id, transaction.input, re.IGNORECASE) 
            and re.search(token_addr, transaction.input, re.IGNORECASE)):
        return None

    from_token = get_transaction_input_param(transaction, 6)
    to_token = get_transaction_input_last_param(transaction)

    # convert hex number to decimal and delete by the decimals after the delimiter - 18
    amount = int(get_transaction_input_param(transaction, 1), 16) / pow(10, 18)

    operation = 'sell'
    if re.search(token_addr, to_token, re.IGNORECASE):
        operation = 'buy'

    return (operation, amount)

def get_pcs_token_for_eth_swap_info(transaction, token_addr):
    method_id = '0x18cbafe5'
    if not (transaction.to is not None 
            and transaction.to.lower() == x_pcs_routerV2_contract_addr.lower()
            and re.search(method_id, transaction.input, re.IGNORECASE) 
            and re.search(token_addr, transaction.input, re.IGNORECASE)):
        return None
    
     # convert hex number to decimal and delete by the decimals after the delimiter - 18
    amount = int(get_transaction_input_param(transaction, 0), 16) / pow(10, 18)

    return ('sell', amount)

def get_pcs_eth_for_token_swap_info(transaction, token_addr):
    method_id = '0xfb3bdb41'
    if not (transaction.to is not None 
            and transaction.to.lower() == x_pcs_routerV2_contract_addr.lower()
            and re.search(method_id, transaction.input, re.IGNORECASE) 
            and re.search(token_addr, transaction.input, re.IGNORECASE)):
        return None
    
     # convert hex number to decimal and delete by the decimals after the delimiter - 18
    amount = int(get_transaction_input_param(transaction, 0), 16) / pow(10, 18)

    return ('buy', amount)

def get_pcb_zap_in_info(transaction, token_addr):
    method_id = '0x1c4009f9'
    if not (transaction.to is not None 
            and transaction.to.lower() == x_pcb_zap_contract_addr.lower() 
            and re.search(method_id, transaction.input, re.IGNORECASE) 
            and re.search(token_addr, transaction.input, re.IGNORECASE)):
        return None

    from_token = get_transaction_input_param(transaction, 0)
    to_token = get_transaction_input_param(transaction, 2)
    amount = int(get_transaction_input_param(transaction, 1), 16) / pow(10, 18)

    operation = 'sell'
    if re.search(token_addr, to_token, re.IGNORECASE):
        operation = 'buy'
    elif re.search(pcs_qbt_bnb_pair_contract, to_token, re.IGNORECASE):
        operation = 'sell for LP'

    return (operation, amount)

def get_pcb_zap_out_info(transaction, token_addr):
    method_id = '0xd9139f63'
    if not (transaction.to is not None 
            and transaction.to.lower() == x_pcb_zap_contract_addr.lower() 
            and re.search(method_id, transaction.input, re.IGNORECASE) 
            and re.search(token_addr, transaction.input, re.IGNORECASE)):
        return None

    from_token = get_transaction_input_param(transaction, 0)    
    amount = int(get_transaction_input_param(transaction, 1), 16) / pow(10, 18)
    to_token = 'wbnb'

    operation = 'sell'
    return (operation, amount)

def test():
    w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    transaction = w3.eth.get_transaction('0xc3d6e67a2b1a834e15a2d8de2203cd1531fd3216039406e8afcf11d740122797')
    info = get_pcs_exact_token_for_token_swap_info(transaction, qbt_contract_addr)
    if info is None:
        info = get_pcs_token_for_exact_token_swap_info(transaction, qbt_contract_addr)
    if info is None:
        info = get_pcs_token_for_eth_swap_info(transaction, qbt_contract_addr)
    if info is None:
        info = get_pcs_eth_for_token_swap_info(transaction, qbt_contract_addr)
    if info is None:
        info = get_pcb_zap_in_info(transaction, qbt_contract_addr)
    if info is None:
        info = get_pcb_zap_out_info(transaction, qbt_contract_addr)

    (operation, amount) = info        

    print(operation + " " + str(amount) + " " + transaction.hash.hex())

    #print(info)

    return None

def main():
    w3 = Web3(Web3.HTTPProvider("https://bsc-dataseed.binance.org/"))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    new_blocks_filter = w3.eth.filter("latest")

    while True:
        time.sleep(3)
        blocks = []

        try:
            blocks = new_blocks_filter.get_new_entries()
        except:
            print('filter failed')
            new_blocks_filter = w3.eth.filter("latest")
            blocks = new_blocks_filter.get_new_entries()

        for block in blocks:
            block_hash = block.hex()
            block = None
            try:
                block = w3.eth.getBlock(block_hash, True)
            except exceptions.BlockNotFound:
                print('failed to find block: ' + block_hash)

            if block is not None:
                for transaction in block.transactions:
                        info = get_pcs_exact_token_for_token_swap_info(transaction, qbt_contract_addr)
                        if info is None:
                            info = get_pcs_token_for_exact_token_swap_info(transaction, qbt_contract_addr)
                        if info is None:
                            info = get_pcs_token_for_eth_swap_info(transaction, qbt_contract_addr)
                        if info is None:
                            info = get_pcs_eth_for_token_swap_info(transaction, qbt_contract_addr)
                        if info is None:
                            info = get_pcb_zap_in_info(transaction, qbt_contract_addr)
                        if info is None:
                            info = get_pcb_zap_out_info(transaction, qbt_contract_addr)
                    
                        if info is not None:
                            (operation, amount) = info        
                            print("op: " + operation + ", amount: " + str(amount) + ", tx: " + transaction.hash.hex())

main()

