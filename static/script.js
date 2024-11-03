const socket = io.connect('http://127.0.0.1:5001');
const blockchainContainer = document.getElementById("blockchain-container"); // Make sure this ID matches the HTML

socket.on('new_block', (block) => {
    console.log("Received block:", block);
    addBlock(block);
});

function addBlock(block) {
    // Check if the user is at the bottom of the scrollable area
    const isScrolledToBottom = blockchainContainer.scrollHeight - blockchainContainer.scrollTop === blockchainContainer.clientHeight;

    // Create a new block element with block data
    const blockElement = document.createElement("div");
    blockElement.classList.add("block");
    blockElement.innerHTML = `
        <strong>Block #${block.index}</strong><br>
        Miner: ${block.miner}<br>
        Transactions: ${block.transactions}<br>
        Hash: ${block.hash}<br>
        Previous Hash: ${block.previous_hash}<br>
        Timestamp: ${new Date(block.timestamp * 100).toLocaleString()}
    `;

    // Append the new block to the end of the blockchain container
    blockchainContainer.appendChild(blockElement);

    // Scroll to the bottom only if the user was already there
    if (isScrolledToBottom) {
        blockchainContainer.scrollTop = blockchainContainer.scrollHeight;
    }
}