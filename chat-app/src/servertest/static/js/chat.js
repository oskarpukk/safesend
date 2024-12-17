// SafeSend vestlusrakenduse peamine komponent
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './Chat.css';

const Chat = () => {
    // Oleku muutujad
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState('');
    const [socket, setSocket] = useState(null);
    
    useEffect(() => {
        // Ühenduse loomine serveriga
        const newSocket = io('http://localhost:5000');
        setSocket(newSocket);
        
        // Puhastamine komponendi eemaldamisel
        return () => newSocket.close();
    }, []);

    // Sõnumi saatmise funktsioon
    const sendMessage = (e) => {
        e.preventDefault();
        if (inputMessage.trim() && socket) {
            socket.emit('message', inputMessage);
            setInputMessage('');
        }
    };

    return (
        <div className="chat-container">
            {/* Vestluse vaade */}
            <div className="messages">
                {messages.map((msg, i) => (
                    <div key={i} className="message">
                        {msg}
                    </div>
                ))}
            </div>
            
            {/* Sõnumi sisestamise vorm */}
            <form onSubmit={sendMessage}>
                <input 
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Kirjuta sõnum..."
                />
                <button type="submit">Saada</button>
            </form>
        </div>
    );
};

export default Chat;