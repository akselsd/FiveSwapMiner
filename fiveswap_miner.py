import urllib.request, urllib.error, urllib.parse
import json
import hashlib
import binascii
import time
from struct import pack, unpack
import random
import datetime
import requests
from ctypes import cdll
import ctypes
import gmpy2 as gm

NODE_URL = "http://6857coin.csail.mit.edu"

lib = cdll.LoadLibrary("./libFiveSwapMiner/libfiveswapminer.so")
lib.FiveMiner_new.restype = ctypes.c_void_p

W = 256
HASHES_PER_ATTEMPT = 120000

class FiveMiner(object):

    def __init__(self):
        self.obj = lib.FiveMiner_new()
        self.mine_func = lib.mine_block
        self.mine_func.restype = ctypes.c_int
        self.mine_func.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

    def check_hash(self, hash):

        argument = hash.to_bytes(int(W/8), "little")

        return lib.mine_block(self.obj, argument)

def solve_block(b, miner):
    
    b["nonce"] = rand_nonce()
    nonces_tried = 0
    popcount_record = 0

    while True:
        
        b["nonce"] += 1
        nonces_tried += 1
        h = int(hash_block_to_hex(b), 16)

        nonce_popcount = miner.check_hash(h)

        if nonce_popcount > popcount_record:
            popcount_record = nonce_popcount

        if nonce_popcount > b["difficulty"]:
            print("Found block after", nonces_tried, "tries. Popcount:", popcount_record)
            return True
        
        # Dont spend too much time in case someone else solves it
        if nonces_tried >= HASHES_PER_ATTEMPT:
            print("Record:", popcount_record, "after", nonces_tried, "nonces tried. Current difficulty:", b["difficulty"])
            return False

        

def main():

    miner = FiveMiner()

    start_time = datetime.datetime.now()

    block_contents = "Akselsd"
    current_block_parent = None
    attempts = 0

    while True:
        #   Next block's parent, version, difficulty
        next_header =  get_next()
        #   Construct a block with our name in the contents that appends to the
        #   head of the main chain
        new_block = make_block(next_header, block_contents)

        if new_block["parentid"] != current_block_parent:
            current_block_parent = new_block["parentid"]
            attempts = 0
            print("Solving block", new_block["parentid"], "with root", new_block["root"])
        
        solved = solve_block(new_block, miner)
        #   Send to the server
        if solved:
            print("Solved!")
            print(new_block)
            add_block(new_block, block_contents)
        else:
            attempts += 1
            delta = datetime.datetime.now() - start_time
            print("Total nonces tried: %d (%d / sec))" \
                % (attempts*HASHES_PER_ATTEMPT, attempts*HASHES_PER_ATTEMPT // delta.total_seconds()))




def get_next():
    """
       Parse JSON of the next block info
           difficulty      uint64
           parentid        HexString
           version         single byte
    """
    return json.loads(urllib.request.urlopen(NODE_URL + "/next").read())

def add_block(h, contents):
    """
       Send JSON of solved block to server.
       Note that the header and block contents are separated.
            header:
                difficulty      uint64
                parentid        HexString
                root            HexString
                timestampe      uint64
                version         single byte
            block:          string
    """
    add_block_request = {"header": h, "block": contents}
    print("Sending block to server...")
    print(json.dumps(add_block_request))
    r = requests.post(NODE_URL + "/add", data=json.dumps(add_block_request))
    print(r)
    print(r.text)

def hash_block_to_hex(b):
    """
    Computes the hex-encoded hash of a block header. First builds an array of
    bytes with the correct endianness and length for each arguments. Then hashes
    the concatenation of these bytes and encodes to hexidecimal.
    """
    packed_data = []
    packed_data.extend(b["parentid"])
    packed_data.extend(b["root"])
    packed_data.extend(fixed_length_hex(int(b["difficulty"]), 16))
    packed_data.extend(fixed_length_hex(int(b["timestamp"]), 16))
    packed_data.extend(fixed_length_hex(int(b["nonce"]), 16))
    packed_data.extend(fixed_length_hex(int(b["version"]), 2))
    b["hash"] = hashlib.sha256(bytes.fromhex(''.join(packed_data))).hexdigest()
    return b["hash"]

def fixed_length_hex(content, length):
    return hex(content)[2:].zfill(length)

def make_block(next_info, contents):
    """
    Constructs a block from /next header information `next_info` and sepcified
    contents.
    """
    block = {
        "version": next_info["version"],
        #   for now, root is hash of block contents (team name)
        "root": hashlib.sha256(contents.encode('utf-8')).hexdigest(),
        "parentid": next_info["parentid"],
        #   nanoseconds since unix epoch
        "timestamp": int(time.time()*1000*1000*1000),
        "difficulty": next_info["difficulty"]
    }
    return block

def rand_nonce():
    """
    Returns a random int in [0, 2**64)
    """
    return random.randint(0,2**64-1)

if __name__ == "__main__":
    main()