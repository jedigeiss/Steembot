# Steembot
A bot for the Steempunk-net MMORPG executing payouts for delegations of Steem Power 


## What does it do?
If you are already familiar with the Steem Blockchain it is quite easy to explain. This Bot monitors an account, in the given case it is the account steempunknet and it calculates all current delegations to that account. 
This data gets only refreshed if there are new operations done and the distribution might have changed. If nothings happend nothing will change.
As a second step the bot then calculates the relative percentage of everyone in comparison with the total amount of delegations.

This is then used to distribute all the SBD that is lying within the wallet of the above mentioned account to compensate the delegators for the SP lended to the account.
Currently, 80% of the SBD are given out to the delegators, while 20% are sent to the steempunksnet account for safets reasons.
Payout only starts if there is more than 1 SBD to distribute.


## Can I use it for my own purpose?

Sure you can, there are some config variables you need to change though.
The most important one is the NAME_ACCOUNT variable that specifies the account to be monitored.


## What do I need to install?

You need a instance of Python, I am running 3.6, but lower version numbers should do fine as well since we are not using asyncs here.
Then you need to install beem with pip3, this is the module I am using to connect to the steem blockchain.
Apart from that nothing fancy is used.

## What do I need to setup?

The only additional thing you need to setup is a sqlite3 database called punk.db with the following tables ( I will create a short python proggie doing this for you later)

- CREATE TABLE "config" ( `maxop` INTEGER )
- CREATE TABLE "delegations" ( `ID` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, `delegator` TEXT NOT NULL, `steempower` INTEGER NOT NULL, `datum` timestamp, `prozent` INTEGER )
