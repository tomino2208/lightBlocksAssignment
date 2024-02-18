Welcome

The results spawn between block 0 to 200 000 (included).
The results were computed using the rpc provided in the task.

Blocks folder contains the raw data for the blocks
as a dict where the block hash is the key.

Transactions folder contains the raw data for the transactions organised in two different ways:
one as a dict where the key is the transaction hash
one as a dict where the key is the timestamp of the transaction. Since timestamp is not using the value may be multiple transactions.
block timestamps with no transactions where not kept as a key.

Transactions receipts folder contains the raw data for the transactions receipts.
The data is a dict where the transaction hash is the key
This data served to confirmed wherever the transactions failed

Accounts folder contains various interesting organizations of the data where the primary key is 
the account emitting the transaction and the second the transaction hash or the timestamp
Variations include transaction receipts instead of transactions or accounting for both the transactions 
emitted and received by an account.

Stats folder contains all the final data required by the task.
The functions can be run to obtain the different aspects of data and will print accordingly. 
To make the stats modulable they require no change to be done on all the blocks of the network.
An application could run to publish those stats in real time by loading the previous results and adding the few blocks 
that are added every second


