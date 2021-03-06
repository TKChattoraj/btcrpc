# a controller file will house the functions called by the application view frames


# retrieves the utxo from the database wallet given the utxo database id
# # transaction
from wallet_database import MyDatabase
from thread import UpDateThread

import threading


import tkinter as tk
from tkinter import ttk

import time
import globals
#import application_view
import sys
sys.path.append('./programming_bitcoin_song/')
from programming_bitcoin_song.tx import Tx, TxIn, TxOut, Connection, TxFetcher
from programming_bitcoin_song.ecc import PrivateKey


from f4_model import TxFactory, Utxo, grab_address, push_raw_tx
from f4_model import update_utxo_for_spent, sort_pushed_tx_for_utxo_update
from f4_model import update_db_for_utxo, update_db_keys_utxos
from f4_model import inputs_for_new_utxos, inputs_for_utxo_spents, calculate_wallet_amount

import f4_view




def get_payees(frame_object):
    #
    #  To get the payees addresses, you would need to recieve the addresses from
    #  the payees' application, somehow--text, email, QR code etc maybe
    #  For now, the following gets those addresses from internal database table keys.
    #  This internal table would be used to get the address to send to someone for them to
    #  pay this wallet owner.
    #
    # key_array is array of tuples (db_id, private_key, public_key)
    key_array = frame_object.master.wallet.retrieve_keys_for_payee()

    # make list of possible payee adresses:
    #
    possible_payee_addresses = []
    for key in key_array:
        private_key = int.from_bytes(key[1], byteorder='big', signed=False)
        #
        # generate the public key from the private key retrieved in the database
        #

        key_object = PrivateKey(private_key)

        # produce the public key address

        ###
        # Update Note:  The public key address will depend on what type of ScriptPubkey
        # will be used.  Assume for now p2pkh--which would require the Base58 of the
        # hash160 of the public key.  p2sh would require the Base58 of the hash160
        # of the Redeem script.
        ###

        public_key_address = key_object.point.address(testnet=True)

        ##
        # Update Note:  Maybe a verification that the public_key_address just created from the
        # private key is the same address that results from the database public_key.
        # Would need to take that public_key--take it from bytes to dar [?] to base58 [?]
        ##

        # create array of tuples (db_id associated with private_key that make the public_key_address, public_key-address)
        possible_payee_addresses.append((key[0], public_key_address))

    f4_view.show_possible_payees(frame_object, possible_payee_addresses)

def get_n_public_addresses(frame_object, n):
    key_array = frame_object.master.wallet.retrieve_n_keys(n)
    n_addresses = []
    for key in key_array:
        private_key = int.from_bytes(key[1], byteorder='big', signed=False)
        #
        # generate the public key from the private key retrieved in the database
        #

        key_object = PrivateKey(private_key)

        # produce the public key address

        ###
        # Update Note:  The public key address will depend on what type of ScriptPubkey
        # will be used.  Assume for now p2pkh--which would require the Base58 of the
        # hash160 of the public key.  p2sh would require the Base58 of the hash160
        # of the Redeem script.
        ###
        # get the compressed sec public key
        compressed = True
        compressed_public_key_address = key_object.point.sec(compressed)

        ##
        # Update Note:  Maybe a verification that the public_key_address just created from the
        # private key is the same address that results from the database public_key.
        # Would need to take that public_key--take it from bytes to dar [?] to base58 [?]
        ##

        # create array of tuples (db_id associated with private_key that make the public_key_address, public_key-address)
        n_addresses.append((key[0], compressed_public_key_address))
    # Return info to the view
    # uncomment when used in the app--comment for temp__run1
    #f4_view.show_possible_payees(frame_object, possible_payee_addresses)
    return n_addresses





class CreateTxThread (threading.Thread):
    def __init__(self, name, array):
        threading.Thread.__init__(self)
        print("initializing create tx thread")
        self.name = name
        self.array = array
        self.lock = threading.Lock()
        self.running = True

    def run(self):

        tx=_create_tx(self.array)

    def terminate_run(self):
        self.running = False



def create_tx(frame_object, array):

    create_tx_thread = CreateTxThread(name="Create-Tx", array=array)
    create_tx_thread.start()
    update_view_thread = f4_view.UpdateViewThread("update", frame_object)
    update_view_thread.start()
    print("before the join")
    create_tx_thread.join()
    print("after the join")
    update_view_thread.terminate()

    #update_view.terminate()
    print("here is where we need access to the tx created in the create_tx_thread")



    #f4_view.show_tx(frame_object=frame_object, tx=tx)


def _create_tx(array):
    """
    Arguments:
        master: is the master for the tkinker unit--the frame for the f4
        ## Here array needs to change to be [(type=p2pkh, p2sh; [addresses], amount)]
        array:  array of tuples (keys_db_id, address, amount)

    Returns
        tx_serialized.hex():  serialized tx as hex string to be displayed in the f4_view

    """
    # create the "material" for a transaction--the "material will be a TxFactory object"


    print("Creating the tx...from create_tx")


#################################################
    # # use list comprehension to remove potential tuples representing utxos (keys_db_id, address, amount)
    # # that are not to be use, i.e. to which we are not sending Bitcoin.
    #
    #
    #
    #
    # addresses_to_use = [item for item in array if item[2].get() > 0] # each item will be a tuple (key_db_id, address, amount)
    #
    # change_address_to_use = [item for item in array if item[2].get()==0][0] # take the first element that has 0 BTC for change_key
    # # Note:  the making of change_address_to_use as above assumes array has at
    # # least one entry with 0 BTC.
    # ##
    # # If no such entry then, we'll need code to generate a private/public key pair, put it into the db, and then create a public address
    # ##
    #
    # # create a TxFactory object--from which the tx will be made
    #
    # tx_material = TxFactory()
    # tx_material.calc_paid_amount(addresses_to_use)
    #
    # # append the change_address_to_use
    # addresses_to_use.append(change_address_to_use)
    #
    #
    #
    # # create the TxFactory attribute that holds the utxo factory objects for
    # # the utxos that will be spent, i.e. the inputs
    # tx_material.create_factory_input_array()
    # # Create the tx_ins objects
    # tx_ins = tx_material.create_tx_ins_array()
    #
    # tx_material.create_factory_output_array(addresses_to_use)
    #####
    ##### addresses_to_useneeds to be changed to be an array of tuples
    ##### of how the outputs will be: [(type=p2pkh, p2sh; [addresses], amount)]
    #####  if p2pkh then the [addresses] array will be lenght of 1
    #####  if p2sh then the [addresses] array will be a list of all the possible
    #####  sec public keys that could be signed  -- the n of the m of n
    #
    # # Create the tx_outs object
    # tx_outs = tx_material.create_tx_outs_array()
    # print(tx_outs)
    #
    #
    # # Create the tx object
    # tx = Tx(version=1,tx_ins=tx_ins, tx_outs=tx_outs, locktime=0, testnet=True, segwit=False)
    # tx.sign_all_inputs(tx_material.utxo_array)
    # print("Tx_ins[0]: {}".format(tx.tx_ins[0]))
    # print()
    # tx_serialized = tx.serialize()
    # tx_serialized_hex = tx_serialized.hex()
    # print("Tx Serialized: {}".format(tx_serialized_hex))
    # print(tx)
###########################################################################
    #  Show the created tx in f4
    #f4_view.show_serialized_tx(master, tx_serialized_hex)

    time.sleep(15)
    print("ending in 5")
    time.sleep(5)
    # threadLock.release()
    print("ending the cr_tx")

    #f4_view.show_tx(frame_object=frame_object, tx=tx)

    #######################  Turned off the push_raw_tx for now
    #
    #  Here the created transaction is pushed to the network.
    #  In this case, the testnet is used.
    #  Furhter revisions needed for real life.  In real life the mainnet
    #  would be used via the local node.

    # pushed_tx = push_raw_tx(tx_serialized_hex)

    #######################


    """
    Pushed Tx: {'tx': {'block_height': -1, 'block_index': -1, 'hash': '0aa127db5e775571f1919bccddc9ef4e52aa3785585a5a26d42fb7282e6ac992', 'addresses': ['mwV7paRv7VdcecM1UPc2jLEWYJb9Uk8pzB', 'muArwFiHwKb682YwStc9VdevUeosghzxTq', 'n1fpHjQXCEumdBVKhhJA77aEmsdjNLErNr', 'mkKJzpQbCQacNtKn6n8MR43nF3CX2v8ttP'], 'total': 950000, 'fees': 50000, 'size': 260, 'preference': 'high', 'relayed_by': '216.18.205.180', 'received': '2020-08-22T17:58:52.741500514Z', 'ver': 1, 'double_spend': False, 'vin_sz': 1, 'vout_sz': 3, 'confirmations': 0, 'inputs': [{'prev_hash': '1379573a272bc1d5b2c6ddf82f0a653d1acb3539f6ee231e2f1c2ed1243812b3', 'output_index': 0, 'script': '483045022100fd66ba3d86cd5283479946b47267c47fb1bf47a2eda6de4fd55e1ee4c00b6b46022017492d5215026337d484d2fa8e9c92112394a48fbef1274da76eb32869fe729c0121035f43cc7aef82e9b603cafdc35b3e0b274138c23323eb05f3b7f7c818534120c4', 'output_value': 1000000, 'sequence': 4294967295, 'addresses': ['mwV7paRv7VdcecM1UPc2jLEWYJb9Uk8pzB'], 'script_type': 'pay-to-pubkey-hash', 'age': 1773191}], 'outputs': [{'value': 100000, 'script': '76a91495c4f7f5aa0390f476865a2a416ac0be1125c8ba88ac', 'addresses': ['muArwFiHwKb682YwStc9VdevUeosghzxTq'], 'script_type': 'pay-to-pubkey-hash'}, {'value': 200001, 'script': '76a914dd0f939e30b2ba468d8ce8fac07c512d3dffe3d788ac', 'addresses': ['n1fpHjQXCEumdBVKhhJA77aEmsdjNLErNr'], 'script_type': 'pay-to-pubkey-hash'}, {'value': 649999, 'script': '76a91434a4eb52a487bc2cdc3839355322b3e7d1c028ab88ac', 'addresses': ['mkKJzpQbCQacNtKn6n8MR43nF3CX2v8ttP'], 'script_type': 'pay-to-pubkey-hash'}]}}

    """
#### Turned off for now.
####  This is the portion that updates the database
#### after pushing the tx to the blockchain
####
    # #
    # # Call method to update the wallet based on the new pushed tx
    # # In the utxo table, the tx_ins would need to be status as "spent"
    # # and the tx_outs would need to be added to the utxo table_name
    # # and status as "utxo."
    # # In the keys table, the keys used for the outputs would need to
    # # reference the associated utxo--the keys table utxo_id would need to
    # # point to the appropriate utxo table id.
    # #
    #
    # # update_utxo_for_spent
    # i = inputs_for_utxo_spents(pushed_tx)
    # print(i)
    # MyDatabase.update_utxo_table_spent(i)
    #
    # # update utxo for new utxo_script_pubkey
    # n = inputs_for_new_utxos(pushed_tx)
    # print(n)
    # MyDatabase.insert_new_utxos(n)
    #
    # # retrieve utxo table ids for output addresses_array
    #
    # utxo_ids_addresses = MyDatabase.retrieve_utxo_ids(n)
    # print(utxo_ids_addresses)
    # # utxo_ids_addresses is a list of tuples ([addresses], utxos_id)
    # MyDatabase.update_keys_for_utxos(utxo_ids_addresses)
    #
    # print("Pushed Tx: {}".format(pushed_tx))
#####
#####
#####


def calculate_btc_amount():
    return calculate_wallet_amount()
