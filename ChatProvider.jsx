import React, { createContext, useContext, useState, useEffect } from 'react';
import ChatIcon from './ChatIcon';
import ChatInterface from './ChatInterface';

const ChatContext = createContext();

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

export const ChatProvider = ({ children }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  const [hasUnreadMessages, setHasUnreadMessages] = useState(false);

  const openChat = () => {
    setIsChatOpen(true);
    setHasUnreadMessages(false);
  };

  const closeChat = () => {
    setIsChatOpen(false);
  };

  const toggleMaximize = () => {
    setIsMaximized(!isMaximized);
  };

  const markAsUnread = () => {
    if (!isChatOpen) {
      setHasUnreadMessages(true);
    }
  };

  const value = {
    isChatOpen,
    isMaximized,
    hasUnreadMessages,
    openChat,
    closeChat,
    toggleMaximize,
    markAsUnread,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
      {!isChatOpen && (
        <ChatIcon
          onClick={openChat}
          hasUnreadMessages={hasUnreadMessages}
        />
      )}
      <ChatInterface
        isOpen={isChatOpen}
        onClose={closeChat}
        onMaximize={toggleMaximize}
        isMaximized={isMaximized}
      />
    </ChatContext.Provider>
  );
};
