// Establish WebSocket connection to the server
const socket = new WebSocket('ws://localhost:8080');

// Elements from the DOM
const chatWindow = document.getElementById('chat-window');
const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');

// Handle incoming messages
socket.addEventListener('message', function (event) {
    const messageData = JSON.parse(event.data);
    displayMessage('Partner', messageData.text);
});

// Send message when form is submitted
messageForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const message = messageInput.value;
    if (message.trim() !== '') {
        // Send the message as JSON
        const messageData = { text: message };
        socket.send(JSON.stringify(messageData));

        // Display the message in the chat window
        displayMessage('You', message);
        messageInput.value = '';
    }
});

// Function to display a message in the chat window
function displayMessage(sender, text) {
    const messageElement = document.createElement('div');
    messageElement.classList.add('message');

    const senderElement = document.createElement('div');
    senderElement.classList.add('sender');
    senderElement.textContent = sender;

    const textElement = document.createElement('div');
    textElement.classList.add('text');
    textElement.textContent = text;

    messageElement.appendChild(senderElement);
    messageElement.appendChild(textElement);

    chatWindow.appendChild(messageElement);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}
