// ################################################
// # Programmeerimine I
// # 2024/2025 sügissemester
// #
// # Projekt
// # Teema: Vestlusrakendus
// #
// # Autorid: 
// # Oskar Pukk
// # Richard Mihhels
// #
// # Lisakommentaar: Frontendi seadistamine
// ################################################

import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './Chat.css';

// Add encryption helper functions
const encryptionHelper = {
    chars: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?",
    
    decrypt: function(message, privateKey) {
        const shift = privateKey % this.chars.length;
        let result = "";
        for (let char of message) {
            if (this.chars.includes(char)) {
                const currentPos = this.chars.indexOf(char);
                const newPos = (currentPos - shift + this.chars.length) % this.chars.length;
                result += this.chars[newPos];
            } else {
                result += char;
            }
        }
        return result;
    }
};

const Chat = () => {
    const [socket, setSocket] = useState(null);
    const [username, setUsername] = useState('');
    const [privateKey, setPrivateKey] = useState('');
    const [message, setMessage] = useState('');
    const [chatLogs, setChatLogs] = useState({
        'Global Chat': []
    });
    const [users, setUsers] = useState([]);
    const [currentRecipient, setCurrentRecipient] = useState('Global Chat');
    const [encryptionKeys, setEncryptionKeys] = useState({});

    useEffect(() => {
        const newSocket = io('http://172.25.249.164:3002');
        setSocket(newSocket);

        return () => newSocket.close();
    }, []);

    useEffect(() => {
        if (!socket || username) return;

        const promptForCredentials = () => {
            let newUsername;
            do {
                newUsername = window.prompt("Choose your username:") || '';
                newUsername = newUsername.trim();
            } while (!newUsername);

            const key = Math.floor(Math.random() * 22) + 1;
            return { username: newUsername, privateKey: key };
        };

        const credentials = promptForCredentials();
        setUsername(credentials.username);
        setPrivateKey(credentials.privateKey);

        socket.emit('register', {
            username: credentials.username,
            private_key: credentials.privateKey
        }, (response) => {
            if (response.error) {
                alert(response.error);
                setUsername('');
                return;
            }
            console.log('Registration successful', response);
        });

        socket.on('chat_message', (data) => {
            console.log('Received message:', data);
            
            let messageContent = data.message;
            if (!data.self) {
                try {
                    messageContent = encryptionHelper.decrypt(data.message, privateKey);
                    console.log('Decrypted message:', messageContent);
                } catch (error) {
                    console.error('Decryption error:', error);
                }
            }

            setChatLogs(prev => {
                const chatKey = data.recipient === 'Global Chat' ? 'Global Chat' : 
                               (data.self ? data.recipient : data.sender);
                
                console.log('Updating chat logs:', {
                    chatKey,
                    messageContent,
                    sender: data.sender,
                    self: data.self
                });

                return {
                    ...prev,
                    [chatKey]: [
                        ...(prev[chatKey] || []),
                        {
                            sender: data.sender,
                            message: messageContent,
                            self: data.self
                        }
                    ]
                };
            });
        });

        socket.on('user_list', (data) => {
            console.log('Received user list:', data);
            setUsers(data.users.filter(user => user !== credentials.username));
        });

        socket.on('user_joined', (data) => {
            console.log('User joined:', data);
            setUsers(prev => {
                if (!prev.includes(data.username) && data.username !== credentials.username) {
                    return [...prev, data.username];
                }
                return prev;
            });
        });

        socket.on('user_left', (data) => {
            console.log('User left:', data);
            setUsers(prev => prev.filter(user => user !== data.username));
        });

        return () => {
            socket.off('user_list');
            socket.off('user_joined');
            socket.off('user_left');
            socket.off('chat_message');
        };
    }, [socket, username]);

    const handleRecipientChange = (newRecipient) => {
        setCurrentRecipient(newRecipient);
        setChatLogs(prev => ({
            ...prev,
            [newRecipient]: prev[newRecipient] || []
        }));
    };

    const sendMessage = () => {
        if (!message.trim()) return;
        
        console.log("Sending message:", {
            recipient: currentRecipient,
            message: message
        });

        socket.emit('chat_message', { 
            recipient: currentRecipient, 
            message: message 
        });

        setMessage('');
    };

    if (!socket || !username) {
        return <div className="loading">Connecting to chat...</div>;
    }

    return (
        <div className="chat-app">
            <div className="user-header">
                <span>Logged in as: <strong>{username}</strong></span>
            </div>
            
            <div className="chat-main">
                <div className="sidebar">
                    <div className="sidebar-header">Chats</div>
                    <div className="user-list">
                        <div 
                            className={`user-item ${currentRecipient === "Global Chat" ? "active" : ""}`}
                            onClick={() => handleRecipientChange("Global Chat")}
                        >
                            Global Chat
                        </div>
                        {users
                            .filter(user => user !== username)
                            .map(user => (
                                <div
                                    key={user}
                                    className={`user-item ${currentRecipient === user ? "active" : ""}`}
                                    onClick={() => handleRecipientChange(user)}
                                >
                                    {user}
                                </div>
                            ))}
                    </div>
                </div>

                <div className="chat-container">
                    <div className="chat-header">
                        {currentRecipient}
                    </div>
                    <div className="messages">
                        {(chatLogs[currentRecipient] || []).map((msg, index) => (
                            <div
                                key={index}
                                className={`message ${msg.self ? "self" : "other"}`}
                            >
                                <div className="username">{msg.sender}</div>
                                <div className="message-content">{msg.message}</div>
                            </div>
                        ))}
                    </div>
                    <div className="chat-input">
                        <input
                            type="text"
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyPress={(e) => e.key === "Enter" && sendMessage()}
                            placeholder="Type a message... (Press Enter)"
                        />
                        <button onClick={sendMessage}>Send</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Chat;