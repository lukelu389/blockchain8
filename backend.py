from flask import Flask, render_template
from flask_socketio import SocketIO
import time
from multiprocessing import Manager, Queue, Process
from blockchain import Blockchain
import random

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", ping_interval=5, ping_timeout=10)

# Define computational powers for each miner (lower sleep time means faster mining)
miner_powers = {
    "A": 0.005,  # Faster mining rate for each miner
    "B": 0.003,
    "C": 0.001
}


def mining_simulation(blockchain, miner_username, stop_queue, miner_power):
    """Simulate mining process based on miner's computational power."""
    try:
        while stop_queue.empty():  # Run until stop signal is sent
            # Generate a real transaction between random users
            sender = random.choice(list(blockchain.users.values()))
            receiver = random.choice([user for user in blockchain.users.values() if user != sender])

            if sender.get_balance() > 1:
                amount = random.randint(1, sender.get_balance())
                blockchain.create_transaction(sender.username, receiver.username, amount, miner_username)

                # Always format the transaction as a readable string
                transaction_display = f"From: {sender.username}, To: {receiver.username}, Amount: {amount}"
            else:
                # Fallback transaction in case sender has insufficient balance
                transaction_display = "No valid transaction"

            # Mine the block with the transaction
            new_block = blockchain.add_block(transaction_display, miner_username)

            # Emit the mined block with the properly formatted transaction
            socketio.emit('new_block', {
                'index': new_block.index,
                'transactions': transaction_display,  # Ensure this is always a formatted string
                'hash': new_block.hash,
                'previous_hash': new_block.previous_hash,
                'miner': new_block.miner,
                'timestamp': new_block.timestamp
            })

            print(f"Block mined and added by Miner {miner_username} with hash: {new_block.hash}")

            # Delay based on miner's computational power
            time.sleep(miner_power)
    except KeyboardInterrupt:
        print(f"Miner {miner_username} stopping mining due to KeyboardInterrupt.")


@app.route('/')
def index():
    return render_template('index.html')


@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Emit the entire chain, ensuring each transaction is properly formatted as a string
    for block in blockchain.chain:
        transactions_str = (
            block.transactions if isinstance(block.transactions, str)
            else f"From: {block.transactions['from']}, To: {block.transactions['to']}, Amount: {block.transactions['amount']}"
        )
        socketio.emit('new_block', {
            'index': block.index,
            'transactions': transactions_str,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'miner': block.miner,
            'timestamp': block.timestamp
        })


if __name__ == '__main__':
    manager = Manager()
    blockchain = Blockchain(manager)
    stop_queue = Queue()  # Queue to signal all processes to stop

    # Add users to the blockchain
    blockchain.add_user("A", "1990-01-01", "apassword", 100)
    blockchain.add_user("B", "1992-02-02", "bpassword", 50)
    blockchain.add_user("C", "1985-05-05", "cpassword", 0)  # Miner

    # Start miner processes
    miners = [
        Process(target=mining_simulation, args=(blockchain, "A", stop_queue, miner_powers["A"])),
        Process(target=mining_simulation, args=(blockchain, "B", stop_queue, miner_powers["B"])),
        Process(target=mining_simulation, args=(blockchain, "C", stop_queue, miner_powers["C"]))
    ]

    for miner in miners:
        miner.start()

    try:
        # Run the Flask-SocketIO app with Socket.IO support
        socketio.run(app, host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        print("\nStopping mining simulation...")
        stop_queue.put("STOP")  # Signal all miners to stop
        for miner in miners:
            miner.join(timeout=1)
            if miner.is_alive():
                miner.terminate()
