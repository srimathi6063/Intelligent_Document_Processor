import React, { useState, useRef, useEffect } from 'react';
import { sendChatMessage } from '../utils/chatApi';

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    zIndex: 999,
    display: 'flex',
    alignItems: 'flex-end',
    justifyContent: 'flex-end',
    padding: '20px',
  },
  chatWindow: {
    background: '#ffffff',
    borderRadius: '20px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
    display: 'flex',
    flexDirection: 'column',
    transition: 'all 0.3s ease-in-out',
    overflow: 'hidden',
  },
  chatWindowMinimized: {
    width: '400px',
    height: '500px',
  },
  chatWindowMaximized: {
    width: '90vw',
    height: '90vh',
  },
  header: {
    background: 'linear-gradient(135deg, #006d77, #005c41)',
    color: 'white',
    padding: '20px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopLeftRadius: '20px',
    borderTopRightRadius: '20px',
  },
  headerTitle: {
    fontSize: '18px',
    fontWeight: '600',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
  },
  headerButtons: {
    display: 'flex',
    gap: '10px',
  },
  headerButton: {
    background: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    color: 'white',
    borderRadius: '8px',
    padding: '8px 12px',
    cursor: 'pointer',
    fontSize: '14px',
    transition: 'all 0.2s ease',
  },
  headerButtonHover: {
    background: 'rgba(255, 255, 255, 0.3)',
  },
  closeButton: {
    background: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    color: 'white',
    borderRadius: '50%',
    width: '32px',
    height: '32px',
    cursor: 'pointer',
    fontSize: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.2s ease',
  },
  closeButtonHover: {
    background: 'rgba(255, 255, 255, 0.3)',
  },
  messagesContainer: {
    flex: 1,
    padding: '20px',
    overflowY: 'auto',
    backgroundColor: '#f8f9fa',
  },
  message: {
    marginBottom: '15px',
    display: 'flex',
    flexDirection: 'column',
  },
  userMessage: {
    alignItems: 'flex-end',
  },
  botMessage: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '70%',
    padding: '12px 16px',
    borderRadius: '18px',
    fontSize: '14px',
    lineHeight: '1.4',
    wordWrap: 'break-word',
  },
  userBubble: {
    background: '#006d77',
    color: 'white',
    borderBottomRightRadius: '6px',
  },
  botBubble: {
    background: 'white',
    color: '#333',
    border: '1px solid #e0e0e0',
    borderBottomLeftRadius: '6px',
  },
  messageTime: {
    fontSize: '11px',
    color: '#999',
    marginTop: '4px',
  },
  userTime: {
    textAlign: 'right',
  },
  botTime: {
    textAlign: 'left',
  },
  welcomeMessage: {
    textAlign: 'center',
    padding: '20px',
    color: '#666',
  },
  databaseButtons: {
    display: 'flex',
    gap: '10px',
    marginTop: '15px',
    justifyContent: 'center',
  },
  dbButton: {
    padding: '10px 20px',
    borderRadius: '12px',
    border: '2px solid #006d77',
    background: 'white',
    color: '#006d77',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.2s ease',
  },
  dbButtonHover: {
    background: '#006d77',
    color: 'white',
    transform: 'translateY(-2px)',
    boxShadow: '0 4px 12px rgba(0, 109, 119, 0.3)',
  },
  inputContainer: {
    padding: '20px',
    borderTop: '1px solid #e0e0e0',
    backgroundColor: 'white',
  },
  inputForm: {
    display: 'flex',
    gap: '10px',
  },
  input: {
    flex: 1,
    padding: '12px 16px',
    borderRadius: '12px',
    border: '2px solid #e0e0e0',
    fontSize: '14px',
    outline: 'none',
    transition: 'border-color 0.2s ease',
  },
  inputFocus: {
    borderColor: '#006d77',
  },
  sendButton: {
    padding: '12px 20px',
    borderRadius: '12px',
    border: 'none',
    background: '#006d77',
    color: 'white',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '600',
    transition: 'all 0.2s ease',
  },
  sendButtonHover: {
    background: '#005c41',
    transform: 'translateY(-2px)',
  },
  sendButtonDisabled: {
    background: '#ccc',
    cursor: 'not-allowed',
  },
  loadingSpinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid #ffffff',
    borderRadius: '50%',
    borderTopColor: 'transparent',
    animation: 'spin 1s ease-in-out infinite',
  },
  typingIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '5px',
    padding: '12px 16px',
    background: 'white',
    border: '1px solid #e0e0e0',
    borderRadius: '18px',
    borderBottomLeftRadius: '6px',
    maxWidth: '70%',
  },
  typingDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    background: '#999',
    animation: 'typing 1.4s infinite ease-in-out',
  },
  typingDot1: { animationDelay: '-0.32s' },
  typingDot2: { animationDelay: '-0.16s' },
};

const ChatInterface = ({ isOpen, onClose, onMaximize, isMaximized }) => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      // Add welcome message when chat opens
      const welcomeMessage = {
        id: Date.now(),
        type: 'bot',
        content: 'What information would you like to ask?',
        timestamp: new Date(),
        showButtons: true,
      };
      setMessages([welcomeMessage]);
    }
  }, [isOpen]);

  const handleDatabaseSelect = (database) => {
    setSelectedDatabase(database);
    const botMessage = {
      id: Date.now(),
      type: 'bot',
      content: `Connected to ${database} database. You can now ask questions about your documents.`,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, botMessage]);
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const data = await sendChatMessage(userMessage.content, selectedDatabase);
      
      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: data.response || 'Sorry, I couldn\'t process your request.',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <>
      {isOpen && (
        <div style={styles.overlay} onClick={onClose}>
          <div 
            style={{
              ...styles.chatWindow,
              ...(isMaximized ? styles.chatWindowMaximized : styles.chatWindowMinimized),
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={styles.header}>
              <div style={styles.headerTitle}>
                🤖 AI Assistant
                {selectedDatabase && (
                  <span style={{ fontSize: '12px', opacity: 0.8 }}>
                    ({selectedDatabase})
                  </span>
                )}
              </div>
              <div style={styles.headerButtons}>
                <button
                  style={styles.headerButton}
                  onClick={onMaximize}
                  title={isMaximized ? 'Minimize' : 'Maximize'}
                >
                  {isMaximized ? '🗗' : '⛶'}
                </button>
                <button
                  style={styles.closeButton}
                  onClick={onClose}
                  title="Close"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Messages */}
            <div style={styles.messagesContainer}>
              {messages.map((message) => (
                <div
                  key={message.id}
                  style={{
                    ...styles.message,
                    ...(message.type === 'user' ? styles.userMessage : styles.botMessage),
                  }}
                >
                  <div
                    style={{
                      ...styles.messageBubble,
                      ...(message.type === 'user' ? styles.userBubble : styles.botBubble),
                    }}
                  >
                    {message.content}
                    {message.showButtons && (
                      <div style={styles.databaseButtons}>
                        <button
                          style={styles.dbButton}
                          onClick={() => handleDatabaseSelect('Invoice')}
                        >
                          📄 Invoice
                        </button>
                        <button
                          style={styles.dbButton}
                          onClick={() => handleDatabaseSelect('Summarization')}
                        >
                          📝 Summarization
                        </button>
                      </div>
                    )}
                  </div>
                  <div
                    style={{
                      ...styles.messageTime,
                      ...(message.type === 'user' ? styles.userTime : styles.botTime),
                    }}
                  >
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div style={styles.message}>
                  <div style={styles.typingIndicator}>
                    <div style={{ ...styles.typingDot, ...styles.typingDot1 }}></div>
                    <div style={{ ...styles.typingDot, ...styles.typingDot2 }}></div>
                    <div style={styles.typingDot}></div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={styles.inputContainer}>
              <form style={styles.inputForm} onSubmit={(e) => e.preventDefault()}>
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={selectedDatabase ? `Ask about ${selectedDatabase}...` : "Type your message..."}
                  disabled={isLoading || !selectedDatabase}
                  style={{
                    ...styles.input,
                    ...(inputRef.current === document.activeElement ? styles.inputFocus : {}),
                  }}
                />
                <button
                  type="submit"
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputValue.trim() || !selectedDatabase}
                  style={{
                    ...styles.sendButton,
                    ...(isLoading || !inputValue.trim() || !selectedDatabase ? styles.sendButtonDisabled : {}),
                  }}
                >
                  {isLoading ? (
                    <div style={styles.loadingSpinner}></div>
                  ) : (
                    'Send'
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      )}


    </>
  );
};

export default ChatInterface;
