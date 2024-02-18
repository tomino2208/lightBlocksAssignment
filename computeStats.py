import pickle

from hexbytes import HexBytes

from connectToNetwork import Data
import pandas
from collections import Counter
class Stats:
    numberTransactions:int
    last_block:int
    data: Data
    def __init__(self):
        data = Data()
        return

    def calculateAccountsNumberTransactions(self):
        accountsTransactionsHash = pickle.load(open(f"accounts/accountsDictHashOnlySent.pkl", "rb"))
        numberTransactionsAccounts = {}

        for account in accountsTransactionsHash.keys():
            accountTransactions = accountsTransactionsHash[account]
            numTransactionsAccount = len(accountTransactions.keys())
            if f'{numTransactionsAccount}' not in numberTransactionsAccounts.keys():
                numberTransactionsAccounts[f'{numTransactionsAccount}'] = []
            numberTransactionsAccounts[f'{numTransactionsAccount}'] += [account]
        with open(f'stats/accountsNumberTransactions.pkl','wb') as f:
            pickle.dump(numberTransactionsAccounts,f)
        return
    def accountsWithBiggestNumberOfTransactions(self, numOfTopSenders=-1):
        numberTransactionsAccounts = pickle.load(open(f"stats/accountsNumberTransactions.pkl", "rb"))
        numberAccounts = 0
        numbersTransactions = []
        for key in numberTransactionsAccounts.keys():
            numbersTransactions.append(int(key))
            numberAccounts += len(numberTransactionsAccounts[key])
        if numOfTopSenders < 0:
            numOfTopSenders = numberAccounts
        sum = min(numOfTopSenders,numberAccounts)
        index = 0
        numbersTransactions.sort(reverse=True)

        topAccounts = []
        numberTransactionsTopAccounts = []
        while(sum > 0):
            sum -= len(numberTransactionsAccounts[f'{numbersTransactions[index]}'])
            topAccounts+= numberTransactionsAccounts[f'{numbersTransactions[index]}']
            index += 1
        #print(f'the top accounts are {topAccounts[:numOfTopSenders]}')
        for i in range(len(numberTransactionsTopAccounts[:numOfTopSenders])):
            print(f'the number of transactions for account {topAccounts[i]} is {numberTransactionsTopAccounts[i]}.')
        return
    def getBlocksSeriesAccounts(self):
        accountsTransactionsHash = pickle.load(open(f"accounts/accountsDictHashOnlySent.pkl", "rb"))
        blocksSerie = {}
        with open(f'stats/accountsBlocksSeries.pkl','wb') as f:
            for account in accountsTransactionsHash:
                blocksAccount = self.getBlocksSerieAccount(accountsTransactionsHash[account])
                blocksSerie[account] = blocksAccount
            pickle.dump(blocksSerie, f)
        f.close()
        return

    def getBlocksSerieAccount(self, accountTransactions):
        blocksSerie = []
        for transactionHash in accountTransactions:
            blocksSerie.append(accountTransactions[transactionHash]['blockNumber'])
        blocksSerie.sort()
        return blocksSerie

    def findPatternBlocksSeries(self):
        blocksSeries = pickle.load(open(f"stats/accountsBlocksSeries.pkl", "rb"))
        blocksSeriesCounter = {}
        with open(f'stats/accountsBlocksSeriesCounter.pkl', 'wb') as f:
            for blocksSerieAccount in blocksSeries:
                blockSerie = blocksSeries[blocksSerieAccount]
                differenceBetweenBlocks = []
                for i in range(len(blockSerie)-1):
                    differenceBetweenBlocks.append(blockSerie[i+1] - blockSerie[i])
                differenceBetweenBlocks_counts = Counter(differenceBetweenBlocks)
                blocksSeriesCounter[blocksSerieAccount] = differenceBetweenBlocks_counts
            pickle.dump(blocksSeriesCounter, f)
                #df = pandas.DataFrame.from_dict(differenceBetweenBlocks_counts, orient='index')
        f.close()
        return

    def printPatterns(self):
        blocksSeries = pickle.load(open(f"stats/accountsBlocksSeries.pkl", "rb"))
        blocksSeriesCounter = pickle.load(open(f"stats/accountsBlocksSeriesCounter.pkl", "rb"))
        for account in blocksSeries:
            blockSerie = blocksSeries[account]
            keys = list(blocksSeriesCounter[account].keys())
            values = list(blocksSeriesCounter[account].values())
            print(f"for {account} the most common space in blocks between transactions is {keys[values.index(max(values))]}")
            if 1 in keys and (values[keys.index(0)]+values[keys.index(1)])>0.95*(sum(values)):
                concerned_blocks = []
                for i in range(len(blockSerie) - 1):
                    differenceBetweenBlocks = blockSerie[i + 1] - blockSerie[i]
                    if differenceBetweenBlocks > 1:
                        concerned_blocks += [f'between block {blockSerie[i]} and block {blockSerie[i+1]}\n']
                print(f'account {account} generally never misses a block for transactions '
                      f'but he did in less than 5% of the cases here.\n The concerned blocks are: {concerned_blocks}\n')
        return

    def failedTransactionsStats(self):
        accountsTransactions = pickle.load(open(f"accounts/accountsDictHashOnlySentFailed.pkl", "rb"))
        miners = {}
        accounts = {}
        blocksNumbers = {}
        blocks = {}
        range_blocks = list(range(0, 210000, 10000))
        for pos in range(len(range_blocks) - 1):
            start = range_blocks[pos] + 1
            if start == 1:
                start = 0
            end = range_blocks[pos + 1]
            blocks = {**blocks, **pickle.load(open(f"blocks/blocks_{start}_{end}.pkl", "rb"))}

        for account in accountsTransactions:
            for transactionHash in accountsTransactions[account]:
                blockNumber = accountsTransactions[account][transactionHash]['blockNumber']
                blockHash = HexBytes(accountsTransactions[account][transactionHash]['blockHash']).hex()
                miner = blocks[blockHash]['miner']
                if miner not in miners:
                    miners[miner] = 0
                miners[miner] += 1
                if account not in accounts:
                    accounts[account] = 0
                accounts[account] += 1
                if blockNumber not in blocksNumbers:
                    blocksNumbers[blockNumber] = 0
                blocksNumbers[blockNumber] += 1
        intervals = []
        blocksNumbersList = list(blocksNumbers.keys())
        blocksNumbersList.sort()
        for index in range(len(blocksNumbersList)-1):
            intervals.append(blocksNumbersList[index+1]-blocksNumbersList[index])

        print('The following miners are responsible for at least 10% of failed transactions.\n')
        for miner in miners:
            if miners[miner]>0.1*sum(miners.values()):
                print(f'The miner {miner} is mining {100* miners[miner]/sum(miners.values())}% of the failed transactions.')
        print('The following accounts are responsible for at least 10% of failed transactions.\n')
        for account in accounts:
            if accounts[account]>0.1*sum(accounts.values()):
                print(f'The account {account} is creating {100* accounts[account] / sum(accounts.values())}% of the failed transactions.')
        print('The following intervals between 2 blocks with failed transactions is a pattern seen in at least 10% of the cases.\n')
        counter_interval = Counter(intervals)
        for interval in counter_interval:
            if counter_interval[interval]>0.1*sum(counter_interval.values()):
                print(f'The interval of {interval} blocks between 2 failed transactions is present in  {100* counter_interval[interval]/sum(counter_interval.values())}% of the time.')
        return

    def payloadNewContractCalls(self):
        accounts =  pickle.load(open(f"accounts/accountsDictHashOnlySent.pkl", "rb"))
        accountsNewContractCall = {}
        numNewTransactions = 0
        for account in accounts:
            for transaction in accounts[account]:
                if accounts[account][transaction]['type']==0:
                    accountsNewContractCall[account]= accounts[account][transaction]
                    numNewTransactions+=1

        print(f'The following accounts are responsible for at least 10% of the new contracts calls')
        for account in accountsNewContractCall.keys():
            if len(accountsNewContractCall[account])>0.1*numNewTransactions:
                print(f'The account {account} is responsible for '
                      f'{100*len(accountsNewContractCall[account])/numNewTransactions}% of the new contracts calls')
        return

    def payloadSourceID(self):
        blocks = {}
        range_blocks = list(range(0, 210000, 10000))
        for pos in range(len(range_blocks) - 1):
            start = range_blocks[pos] + 1
            if start == 1:
                start = 0
            end = range_blocks[pos + 1]
            blocks = {**blocks, **pickle.load(open(f"blocks/blocks_{start}_{end}.pkl", "rb"))}
        accounts = pickle.load(open(f"accounts/accountsDictHashOnlySent.pkl", "rb"))
        methods = {}
        accountsMethods = {}
        methodsAccounts = {}
        accountsMethodsTimestamp = {}
        accountsMethodsValue = {}
        for  account in accounts:
            transactions = accounts[account]
            for transactionHash in transactions:
                if transactions[transactionHash]['type']==2:
                    if account not in accountsMethods.keys():
                        accountsMethods[account] = {}
                        accountsMethodsTimestamp[account] = {}
                        accountsMethodsValue[account] = {}
                    methodID = HexBytes(transactions[transactionHash]['input']).hex()[:10]
                    methods[methodID] = transactions[transactionHash]
                    if methodID not in methodsAccounts:
                        methodsAccounts[methodID] = {}
                    if account not in methodsAccounts[methodID].keys():
                        methodsAccounts[methodID][account] = {}
                    if methodID not in accountsMethods[account].keys():
                        accountsMethods[account][methodID] = {}
                        accountsMethodsTimestamp[account][methodID] = {}
                        accountsMethodsValue[account][methodID] = {}
                    blockHash =  HexBytes(transactions[transactionHash]['blockHash']).hex()
                    timestamp = blocks[blockHash]['timestamp']
                    value = (1e-18)*transactions[transactionHash]['value']

                    accountsMethods[account][methodID][transactionHash] = transactions[transactionHash]
                    methodsAccounts[methodID][account][transactionHash] = transactions[transactionHash]
                    if timestamp not in accountsMethodsTimestamp[account][methodID].keys():
                        accountsMethodsTimestamp[account][methodID][timestamp] = []
                    accountsMethodsTimestamp[account][methodID][timestamp] += [transactionHash]
                    if value not in accountsMethodsValue[account][methodID].keys():
                        accountsMethodsValue[account][methodID][value] = []
                    accountsMethodsValue[account][methodID][value] += [transactionHash]
        with open(f'stats/dictMethods.pkl','wb') as f:
            pickle.dump(methods,f)
        f.close()
        with open(f'stats/accountsDictMethodsTransactionHash.pkl','wb') as f:
            pickle.dump(accountsMethods,f)
        f.close()
        with open(f'stats/accountsDictMethodsTimestamp.pkl','wb') as f:
            pickle.dump(accountsMethodsTimestamp,f)
        f.close()
        with open(f'stats/accountsDictMethodsValue.pkl','wb') as f:
            pickle.dump(accountsMethodsValue,f)
        f.close()
        with open(f'stats/methodsDictAccountsTransactionHash.pkl','wb') as f:
            pickle.dump(methodsAccounts,f)
        f.close()
        return

    # No transactions with same from and method ID have the same timestamp more than twice
    def payloadStats(self):
        timestamp = pickle.load(open(f"stats/accountsDictMethodsTimestamp.pkl", "rb"))
        value = pickle.load(open(f"stats/accountsDictMethodsValue.pkl", "rb"))
        methodsAccounts = pickle.load(open(f"stats/methodsDictAccountsTransactionHash.pkl", "rb"))
        print(f'There are {len(methodsAccounts.keys())} different methods used and they are {methodsAccounts.keys()}.')
        for account in timestamp.keys():
            for method in timestamp[account]:
                for time in  timestamp[account][method]:
                    nbr = len(timestamp[account][method][time])
                    if nbr>2:
                        print(f'The method {method} is used by account {account} at timestamp {time} more than 3 times.')

        return












if __name__ == '__main__':
    stats = Stats()
    stats.accountsWithBiggestNumberOfTransactions()
    #stats.printPatterns()
    #stats.failedTransactionsStats()
    #stats.payloadNewContractCalls()
    #stats.payloadStats()