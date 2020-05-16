# Importing  constants modules
from constants import *

# Importing libraries
from web3 import Web3
import bit
from eth_account import Account
from web3.middleware import geth_poa_middleware
from web3.gas_strategies.time_based import medium_gas_price_strategy
import os
from dotenv import load_dotenv
import subprocess
import json
load_dotenv()

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Add PoA algorithm support to web3.py
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
w3.eth.setGasPriceStrategy(medium_gas_price_strategy)

def derive_wallets(mnemonic, coin, numderive):
    '''This function uses the subprocess library to call the ./derive script from Python.  It returns a tree 
    of wallets(child keys) for specific mnemonic phrase and coin name.'''
    command = f'php derive -g --mnemonic="{mnemonic}" --numderive={numderive} --coin="{coin}" --format=json'
    
    # Creating child process
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    
    # Capture output and error
    (output, error) = process.communicate()
    
    # Wait for child process to terminate before proceeding
    process_status = process.wait()
    
    # Parse output into a JSON object
    output = json.loads(output)
    return output

# Creating list of coin names
coin_names = [ETH, BTCTEST]
coin_names

# Create an object that derives wallets from coin_names
coins = {coin: derive_wallets(os.getenv('MNEMONIC'), coin,3) for coin in coin_names}

def key_to_account(coin, priv_key): 
    '''Converts the private key string in a child key to an account object that bit or web3.py can use 
    to do transactions'''
    if coin == ETH: 
        return Account.from_key(priv_key)
    elif coin == BTCTEST:
        return bit.PrivateKeyTestnet(priv_key)

def create_tx(coin, account, recipient, amount):
    ''' This function creates a raw, unsigned transactions that contains all the metadata needed to transact.
    '''
    if coin == ETH:
        gasEstimate= w3.eth.estimateGas({'from':account.address, 'to':recipient,'value':amount})
        return {
            'to': recipient,
            'from': account.address,
            'value': amount,
            'gas': gasEstimate,
            'gasPrice': w3.eth.gasPrice,
            'nonce': w3.eth.getTransactionCount(account.address),
            #'chainID': w3.eth.chainId   
            }
    elif coin == BTCTEST:
        return bit.PrivateKeyTestnet.prepare_transaction(account.address, [(recipient.address, amount, BTC)])

def send_tx(coin, account, recipient, amount):
    '''This function calls the create_tx function, then sends metadata to the designated network .'''
    raw_txn = create_tx(coin, account, recipient, amount)
    if coin == ETH:        
        # Sign the transaction to validate
        signed_tx = account.sign_transaction(raw_txn)
        return w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    elif coin == BTCTEST:
        signed_tx = account.sign_transaction(raw_txn)
        return bit.network.NetworkAPI.broadcast_tx_testnet(signed_tx)

  