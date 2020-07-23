# CREATE A CRYPTOCURRENCY

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request, render_template, redirect, url_for
import requests
from uuid import uuid4
from urllib.parse import urlparse
from random import SystemRandom



class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1, miner='0')
        self.nodes = set()

    def create_block(self, proof, miner):
        block = {'index': len(self.chain) + 1,
                 'miner': miner,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'transactions': self.transactions}  # Adding the transctind list to the block
        self.transactions = []  # Setting the transactions list back to empty
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        random_gen = SystemRandom()
        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash_operation = hashlib.sha256(
                str((new_proof* random_gen.randint(0, 20))**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    def add_transaction(self, names, id_number, phone, quantity):
        self.transactions.append({'names': names,
                                  'id_number': id_number,
                                  'phone': phone,
                                  'quantity': quantity})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False


# Mining our Blockchain
# Starting a Web App
app = Flask(__name__)

# Creating an address for the Node on port 5000
node_address = str(uuid4()).replace('-', '')
miner = node_address

# Creating a Blockchain
blockchain = Blockchain()

# Setting the home url
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':

        return redirect(url_for('add_transaction'))

    elif request.method == 'GET':
        return render_template('index.html')

# Adding new transaction to the blockchain
@app.route('/add_transaction', methods=['POST', 'GET'])
def add_transaction():
    json = {
        "names": request.form['names'],
        "id_number": request.form['id_number'],
        "phone": request.form['phone'],
        "quantity": request.form['quantity']
    }
    transaction_keys = ['names', 'id_number', 'phone', 'quantity']
    if not all(key in json for key in transaction_keys):
        # If all the keys in the transaction_keys list are not in the json file...
        return 'Some elements are missing', 400
    index = blockchain.add_transaction(
        json['names'], json['id_number'], json['phone'], json['quantity'])  # This gets the values of the keys and not the keys themselves
    return render_template('confirm.html', names=json['names'], id_number=json['id_number'], phone=json['phone'], quantity=json['quantity'], index=index)


# Mining a new Block
@app.route('/mine_block', methods=['GET'])
def mine_block():
    miner = node_address
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    block = blockchain.create_block(proof, miner)
    response = {
        'index': block['index'],
        'miner': miner,
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'transactions': block['transactions']}
    return render_template('thank_you.html')

# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All Good Champ'}
    else:
        response = {
            'message': 'We seem to have a problem. The blockchain is not valid'}
    return jsonify(response), 200


# Part 3 - Decentralizing the Blockchain

# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The nodes connected are:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201


# Replacing the chain with the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {
            'message': 'The chain was not the longest one. It was replaced',
            'new_chain': blockchain.chain}
    else:
        response = {
            'message': 'The chain is the longest one',
            'actual_chain': blockchain.chain}
    return jsonify(response), 200


# Running the app
app.run(host='0.0.0.0', port=5001)
