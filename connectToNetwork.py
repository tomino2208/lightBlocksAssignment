import pickle
import subprocess
import sys

from web3 import Web3, HTTPProvider, IPCProvider
from web3.middleware import geth_poa_middleware
from hexbytes import HexBytes
from jsonrpcclient import request
from geth import LiveGethProcess
import json
import requests



class Data:
    web3_obj: Web3.HTTPProvider
    last_block:int
    range_blocks:list
    def __init__(self):
        self.web3_obj = Web3(HTTPProvider('https://rpc.testnet.eoracle.network'))
        self.web3_obj.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.last_block = self.web3_obj.eth.block_number
        self.range_blocks = list(range(0, 210000, 10000))
    def getBlocks(self, start, end):
        '''This function takes three inputs, a starting block number, ending block number
        and an Ethereum address. The function loops over the transactions in each block and
        checks if the address in the to field matches the one we set in the blockchain_address.
        Additionally, it will write the found transactions to a pickle file for quickly serializing and de-serializing
        a Python object.'''
        print(f"Started searching through block number {start} to {end}...")
        # create an empty dictionary we will add transaction data to
        block_dictionary = {}
        with open(f"blocks/blocks_{start}_{end}.pkl", "wb") as f:
            for x in range(start, end+1):
                block = self.web3_obj.eth.get_block(x, True)
                block_dictionary[HexBytes(block['hash']).hex()] = block
        #json.dump(tx_dictionary, open(f"blocks/transactionData_{start}_{end}.json", 'w'))
            pickle.dump(block_dictionary, f)
        f.close()
        print(f"Finished searching blocks {start} through {end} and found {len(block_dictionary)} blocks")

    def fromBlocksTotransactions(self,start, end):
        blocks = pickle.load(open(f'blocks/blocks_{start}_{end}.pkl','rb'))
        transactionsDictTimestamp = {}
        transactionsDictHash = {}
        with open(f"transactions/transactionsDictTimestamp_{start}_{end}.pkl", "wb") as f:
            for blockHash in blocks.keys():
                block = blocks[blockHash]
                if 'transactions' in block.keys() and len(block['transactions'])>0:
                    transactionsDictTimestamp[block['timestamp']] = block['transactions']
            pickle.dump(transactionsDictTimestamp, f)
        f.close()
        with open(f"transactions/transactionsDictHash_{start}_{end}.pkl", "wb") as f:
            for timestamp in transactionsDictTimestamp.keys():
                transactions = transactionsDictTimestamp[timestamp]
                for transaction in transactions:
                    transactionsDictHash[HexBytes(transaction['hash']).hex()] = transaction
            pickle.dump(transactionsDictHash, f)
        f.close()
    def readTransactionsHash(self, start, end):
        transactions = pickle.load(open(f"transactions/transactionsDictHash_{start}_{end}.pkl", "rb"))
        return transactions
    def readTransactionsReceipts(self, start, end):
        receipts = pickle.load(open(f"transactionsReceipts/transactionsReceiptsDictHash_{start}_{end}.pkl", "rb"))
        return receipts
    def readTransactionsTimestamp(self, start, end):
        transactions = pickle.load(open(f"transactions/transactionsDictTimestamp_{start}_{end}.pkl", "rb"))
        return transactions
    def readBlocks(self, start, end):
        blocks = pickle.load(open(f"blocks/blocks_{start}_{end}.pkl", "rb"))
        return blocks
    def createAccountsLists(self):
        accounts = []
        accountsDictTimeStamp = {}
        accountsDictHash = {}
        accountsDictHashOnlySent = {}
        accountsDictHashOnlySentFailed = {}
        accountsDictHashOnlySentReceipts = {}

        with open(f"accounts/accountsList.txt", "w") as f:
            for pos in range(len(self.range_blocks) - 1):
                start = self.range_blocks[pos] + 1
                if start == 1:
                    start = 0
                end = self.range_blocks[pos + 1]
                transactions = self.readTransactionsHash(start, end)
                blocks = self.readBlocks(start, end)
                transactionsReceipts = self.readTransactionsReceipts(start, end)
                print(f'at start {start}')
                for transactionHash in transactions:
                    transaction = transactions[transactionHash]
                    transactionReceipt = transactionsReceipts[transactionHash]
                    timestamp = f"{blocks[HexBytes(transaction['blockHash']).hex()]['timestamp']}"
                    if isinstance(transaction['from'], str):
                        if transaction['from'] not in accounts:
                            accounts.append(transaction['from'])
                        if transaction['from'] not in accountsDictTimeStamp.keys():
                            accountsDictTimeStamp[transaction['from']] ={}
                            accountsDictHash[transaction['from']] = {}
                            accountsDictHashOnlySent[transaction['from']] = {}
                            accountsDictHashOnlySentReceipts[transaction['from']] = {}
                        accountsDictTimeStamp[transaction['from']][timestamp] = transaction
                        accountsDictHash[transaction['from']][transactionHash] = transaction
                        accountsDictHashOnlySentReceipts[transaction['from']][transactionHash] = transactionReceipt
                        if transactionReceipt['status'] == 0:
                            if transaction['from'] not in accountsDictHashOnlySentFailed.keys():
                                accountsDictHashOnlySentFailed[transaction['from']] = {}
                            accountsDictHashOnlySentFailed[transaction['from']][transactionHash] = transaction
                        accountsDictHashOnlySent[transaction['from']][transactionHash] = transaction
                    if isinstance(transaction['to'], str):
                        if transaction['to'] not in accounts:
                            accounts.append(transaction['to'])
                        if transaction['to'] not in accountsDictTimeStamp.keys():
                            accountsDictTimeStamp[transaction['to']] ={}
                            accountsDictHash[transaction['to']] ={}
                        accountsDictTimeStamp[transaction['to']][timestamp] = transaction
                        accountsDictHash[transaction['to']][transactionHash] = transaction
            f.write(f'{accounts}')
        f.close()

        with open(f"accounts/accountsDictTimestamp.pkl", "wb") as f:
            pickle.dump(accountsDictTimeStamp, f)
        f.close()
        with open(f"accounts/accountsDictHash.pkl", "wb") as f:
            pickle.dump(accountsDictHash, f)
        f.close()
        with open(f"accounts/accountsDictHashOnlySentReceipts.pkl", "wb") as f:
            pickle.dump(accountsDictHashOnlySentReceipts, f)
        f.close()

        with open(f"accounts/accountsDictHashOnlySent.pkl", "wb") as f:
            pickle.dump(accountsDictHashOnlySent, f)
        f.close()

        with open(f"accounts/accountsDictHashOnlySentFailed.pkl", "wb") as f:
            pickle.dump(accountsDictHashOnlySentFailed, f)
        f.close()
        return

    def getAccountsTransactionsReceipts(self):
        accountsTransactions = pickle.load(open(f"accounts/accountsDictHashOnlySent.pkl", "rb"))
        accountsTransactionsReceipts = {}
        accountsTransactionsFailed = {}
        with open(f"accounts/accountsDictHashOnlySentReceipts.pkl", "wb") as f:
            for account in accountsTransactions:
                print('new account')
                accountsTransactionsReceipts[account] = {}
                for transactionHash in accountsTransactions[account].keys():
                        blockNumber = accountsTransactions[account][transactionHash]['blockNumber']
                        start = blockNumber - (blockNumber % 10000) + 1
                        end = start + 9999
                        if start == 1:
                            start = 0
                            end = start + 10000

                        receipts = pickle.load(open(f"transactions/transactionsDictHash_{start}_{end}.pkl", "rb"))
                        receipt = receipts[transactionHash]
                        if receipt['status'] == 0:
                            if account not in accountsTransactionsFailed.keys():
                                accountsTransactionsFailed[account] = {}
                            accountsTransactionsFailed[account][transactionHash] = accountsTransactions[account][transactionHash]
                        accountsTransactionsReceipts[account][transactionHash] = receipt
            pickle.dump(accountsTransactionsReceipts,f)
        f.close()
        with open(f"accounts/accountsDictHashOnlySentFailedTransactions.pkl", "wb") as f:
            pickle.dump(accountsTransactionsFailed, f)
        f.close()
        return

    def getTransactionsReceipts(self,start, end):
        print(f' starting from {start} to {end}')
        transactions = pickle.load(open(f"transactions/transactionsDictHash_{start}_{end}.pkl", "rb"))
        transactionsReceipts = {}
        with open(f"transactionsReceipts/transactionsReceiptsDictHash_{start}_{end}.pkl", "wb") as f:
            for transactionHash in transactions:
                transactionsReceipts[transactionHash] = self.web3_obj.eth.get_transaction_receipt(transactionHash)
            pickle.dump(transactionsReceipts,f)
        f.close()
        print(f'finished from {start} to {end}')
        return

    def correctTransactionsReceipts(self,start,end):
        transactionsReceipts = self.readTransactionsReceipts(start,end)
        block = self.web3_obj.eth.get_block(end, True)
        for transaction in block['transactions']:
            transactionHash = HexBytes(transaction['hash']).hex()
            transactionsReceipts[transactionHash] = self.web3_obj.eth.get_transaction_receipt(transactionHash)
        with open(f"transactionsReceipts/transactionsReceiptsDictHash_{start}_{end}.pkl", "wb") as f:
            pickle.dump(transactionsReceipts, f)
        f.close()




if __name__ == '__main__':
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    data_obj = Data()
    data_obj.createAccountsLists()
    print('hello')