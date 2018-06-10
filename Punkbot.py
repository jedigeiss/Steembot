#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  9 23:31:29 2018

@author: jan
"""

import datetime
import time
import sqlite3
from beem import Steem
from beem.account import Account
from beem.exceptions import AccountDoesNotExistsException



DB = sqlite3.connect("punk.db",
                     detect_types=sqlite3.PARSE_DECLTYPES)
CURSOR = DB.cursor()

#STEEMPOSTINGKEY = os.environ.get('steemPostingKey')
#S = Steem(wif=STEEMPOSTINGKEY)
S = Steem()
NAME_ACCOUNT = "steempunknet"

def get_max_ops():
    """get the max count of the virtual operations from the blockchain
    Arguments:
        none
    Returns:    -1 for failure or no new virtual operations
                max_op_count in case of new virtual operations
    """
    try:
        acc = Account(NAME_ACCOUNT)
    except TypeError as err:
        print(err)
        return -1
    except AccountDoesNotExistsException:
        print("account does not exist")
        return-1
    CURSOR.execute("SELECT maxop FROM config")
    config_maxop = CURSOR.fetchone()
    max_op_count = acc.virtual_op_count()
    if max_op_count > config_maxop[0]:
        return max_op_count
    return -1


def get_delegations():
    """provide information about the delegation to a steem account
    and update the table in SQLITE that contains the current data
    Arguments:
        none
    Returns:    -1 for failure
                 0 for success
    """
    name_account = "steempunknet"
    try:
        acc = Account(NAME_ACCOUNT)
    except TypeError as err:
        print(err)
        return -1
    except AccountDoesNotExistsException:
        print("account does not exist")
        return-1

    CURSOR.execute("SELECT maxop FROM config")
    config_maxop = CURSOR.fetchone()
    max_op_count = acc.virtual_op_count()
    print("Delegationen an %s" % name_account)

    ratio = S.get_steem_per_mvest(time_stamp=None)
    ratio = round(ratio, 2)
    print("Neue Transaktionen gefunden -- "
          "Intervall von %s bis %s" %(config_maxop[0], max_op_count))
   # c.execute("SELECT * FROM delegations")
   # delegations = c.fetchall()
    #print (delegations)
    for row in acc.history_reverse(start=max_op_count, stop=config_maxop[0],
                                   only_ops=["delegate_vesting_shares"], use_block_num=False):
        if row["delegatee"] == name_account:
            delegator = row["delegator"]
            vests = row["vesting_shares"]
            vests = vests.replace("\'", "")
            vests = vests.replace(" VESTS", "")
            vests = round(float(vests), 4)
            mvests = vests / 1000000
            mvests = round(mvests, 4)
            steem_power = mvests * ratio
            steem_power = round(steem_power, 2)
            timestamp = row["timestamp"]
            timestamp = timestamp.replace("T", " ")
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

            CURSOR.execute("SELECT * FROM delegations WHERE delegator = ?", (delegator,))
            result = CURSOR.fetchone()
            #print (result)
            if result is not None and timestamp > result[3]:
                CURSOR.execute("UPDATE delegations SET steempower = ?,"
                               " datum = ? WHERE delegator = ?", (steem_power,
                                                                  timestamp, delegator,))
                DB.commit()
                print("update")
                print("von: %s Vests: %s Sp: %s Datum: %s " % (delegator, mvests,
                                                               steem_power, timestamp))
            elif result is None:
                print("insert")
                print("von: %s Vests: %s Sp: %s Datum: %s " % (delegator, mvests, steem_power,
                                                               timestamp))
                CURSOR.execute("INSERT INTO delegations (delegator, steempower, datum)"
                               " VALUES (?,?,?)", (delegator, steem_power, timestamp))
                DB.commit()
    CURSOR.execute("UPDATE config SET maxop = ?", (max_op_count,))
    DB.commit()
    return 0


def calculate_percentage():
    """calculates the percentage for each delegator in comparison to the
    total delegation
    Arguments:
        none
    Returns:
        none
    """
    CURSOR.execute("SELECT Sum(steempower) FROM delegations")
    result = CURSOR.fetchone()
    gesamt_sp = result[0]
    CURSOR.execute("SELECT * FROM delegations")
    rows = CURSOR.fetchall()
    for row in rows:
        percentage = (row[2] / gesamt_sp) * 100
        percentage = round(percentage, 2)
        CURSOR.execute("UPDATE delegations SET prozent = ? WHERE delegator = ?"
                       , (percentage, row[1],))
        DB.commit()
        print("User %s hat %s Prozent an den Gesamtdelegationen" % (row[1], percentage))


def payout():
    """prepare and execute the payout for all delegators
    payout will use all SBD that are currently on the chain and distribute
    them.
    Payout will only start if there is at least 1 SBD available.
    Arguments:
        none
    Returns:
        0 in case of everything ok
        -1 in any other case
    """
    acc = Account(NAME_ACCOUNT)
    to_distribute = acc.get_balance("available", "SBD")
    if to_distribute < 1:
        print("Nur %s SBD auf dem Account, Auszahlung beginnt erst ab 1 SBD" % to_distribute)
        return -1
    print("Gesamtsumme zum Verteilen %s" % to_distribute)
    CURSOR.execute("SELECT delegator, prozent from delegations WHERE prozent > 0")
    result = CURSOR.fetchall()
    message = "Thanks alot for delegating to STEEMPUNKNET, this is your daily payout!"
    safety = to_distribute * 0.2
    print("Transfer an Steempunksnet %s" % safety)
    safety = str(safety)
    safety = safety.replace(" SBD", "")
    acc.transfer("steempunksnet", safety, "SBD", memo="safety transfer", account=NAME_ACCOUNT)
    time.sleep(3)
    to_distribute = to_distribute - safety - 0.1
    print("Gesamtsumme zum Verteilen an Delegierer %s" % to_distribute)
    for row in result:
        sbd = to_distribute * float(row[1]) /100
        sbd = str(sbd)
        sbd = sbd.replace(" SBD", "")
        delegator = row[0]
        acc.transfer(delegator, sbd, "SBD", memo=message, account=NAME_ACCOUNT)
        print("Delegator %s mit %s Prozent wurden %s SBD transferiert" % (delegator, row[1], sbd))
        time.sleep(3)
    return 0

if __name__ == "__main__":
    SWITCH = get_max_ops()
    if SWITCH > 0:
        X = get_delegations()
        calculate_percentage()
    if SWITCH < 0:
        print("Keine neuen Transaktionen, Berechnung der neuen"
              " Verteilung daher nicht notwendig .. Skipping")
    RESULT = payout()
    if RESULT == 0:
        print("Payout erfolgreich ausgeführt")
    elif RESULT == -1:
        print("Payout nicht erfolgreich, check die Messages")
