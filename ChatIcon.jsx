import React from 'react';

const styles = {
  chatIcon: {
    position: 'fixed',
    bottom: '30px',
    right: '30px',
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    backgroundColor: '#006d77',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
    boxShadow: '0 8px 25px rgba(0, 109, 119, 0.3)',
    transition: 'all 0.3s ease-in-out',
    zIndex: 1000,
    animation: 'fadeIn 0.3s ease-in-out',
  },
  chatIconHover: {
    transform: 'scale(1.1)',
    boxShadow: '0 12px 35px rgba(0, 109, 119, 0.4)',
    backgroundColor: '#005c41',
  },
  pulse: {
    animation: 'pulse 2s infinite',
  },
};

const ChatIcon = ({ onClick, hasUnreadMessages }) => {
  return (
    <button
      style={{
        ...styles.chatIcon,
        ...(hasUnreadMessages ? styles.pulse : {}),
      }}
      onClick={onClick}
      title="Chat with AI Assistant"
    >
      💬
    </button>
  );
};

export default ChatIcon;
