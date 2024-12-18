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

const Chat = () => {
    const [socket, setSocket] = useState(null);
    const [username, setUsername] = useState('');
    const [privateKey, setPrivateKey] = useState(null);
    const [message, setMessage] = useState('');
    const [chatLogs, setChatLogs] = useState({});
    const [users, setUsers] = useState([]);
    const [currentRecipient, setCurrentRecipient] = useState('Global Chat');

    const generateRandomKey = () => {
        return Math.floor(Math.random() * 22) + 1;
    };

    const promptForCredentials = () => {
        const promptUsername = () => {
            let newUsername;
            do {
                newUsername = window.prompt("Choose your username:") || '';
                newUsername = newUsername.trim();
            } while (!newUsername);
            return newUsername;
        };
        
        const newUsername = promptUsername();
        const useRandomKey = window.confirm("Would you like to use a random private key? (Click OK for yes, Cancel to enter your own)");
        
        let key;
        if (useRandomKey) {
            key = generateRandomKey();
            window.alert(`Your private key is: ${key}\nRemember this number for future logins!`);
        } else {
            do {
                key = window.prompt("Enter your private key (a number between 1-22):") || '';
                key = parseInt(key);
            } while (isNaN(key) || key < 1 || key > 22);
        }
        
        return { username: newUsername, privateKey: key };
    };

    useEffect(() => {
        if (!username || !privateKey) {
            const credentials = promptForCredentials();
            setUsername(credentials.username);
            setPrivateKey(credentials.privateKey);
            
            // Connect to the Python server
            const newSocket = io('http://172.20.10.2:3000');  // Use localhost and port 3000
            setSocket(newSocket);
        }
    }, [username, privateKey]);

    useEffect(() => {
        if (!socket || !username) return;

        socket.emit('register', {
            username: username,
            private_key: privateKey
        }, (response) => {
            if (response.error) {
                alert(response.error);
                setUsername('');
                return;
            }
            console.log('Registration successful', response);
        });

        socket.on('user_list', (data) => {
            console.log('Received user list:', data);
            if (data && data.users) {
                // Filter out the current user from the list
                const filteredUsers = data.users.filter(user => user !== username);
                console.log('Filtered users:', filteredUsers);
                setUsers(filteredUsers);
            } else {
                console.warn('Received invalid user list format:', data);
                setUsers([]);
            }
        });

        socket.on('user_joined', (data) => {
            console.log('User joined:', data);
            setUsers(prev => {
                if (!prev.includes(data.username) && data.username !== username) {
                    return [...prev, data.username];
                }
                return prev;
            });
            setChatLogs(prev => ({
                ...prev,
                [data.username]: []
            }));
        });

        socket.on('user_left', (data) => {
            console.log('User left:', data);
            setUsers(prev => prev.filter(user => user !== data.username));
        });

        socket.on('chat_message', (data) => {
            console.log('Received message:', data);
            if (data.sender === username) return;
            
            const chatKey = data.recipient === 'Global Chat' 
                ? 'Global Chat' 
                : (data.sender === username ? data.recipient : data.sender);
            
            setChatLogs(prev => ({
                ...prev,
                [chatKey]: [
                    ...(prev[chatKey] || []),
                    {
                        sender: data.sender,
                        message: data.message,
                        self: false
                    }
                ]
            }));
        });

        return () => {
            socket.off('user_list');
            socket.off('user_joined');
            socket.off('user_left');
            socket.off('chat_message');
        };
    }, [socket, username, privateKey]);

    const handleRecipientChange = (newRecipient) => {
        setCurrentRecipient(newRecipient);
        setChatLogs(prev => ({
            ...prev,
            [newRecipient]: prev[newRecipient] || []
        }));
    };

    const sendMessage = () => {
        if (!message.trim()) return;
        
        console.log('Sending message:', {
            recipient: currentRecipient,
            message: message
        });

        // Add message to local chat logs immediately
        setChatLogs(prev => ({
            ...prev,
            [currentRecipient]: [
                ...(prev[currentRecipient] || []),
                {
                    sender: username,
                    message: message.trim(),
                    self: true
                }
            ]
        }));

        socket.emit('chat_message', {
            recipient: currentRecipient,
            message: message.trim()
        });

        setMessage('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
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
                            onKeyPress={handleKeyPress}
                            placeholder="Type a message..."
                        />
                        <button onClick={sendMessage}>Send</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Chat;