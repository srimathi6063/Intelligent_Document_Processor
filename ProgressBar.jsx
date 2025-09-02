import React from 'react';

function ProgressBar({ progress }) {
  const styles = {
    container: {
      width: '100%',
      height: '20px',
      backgroundColor: '#e0e0e0',
      borderRadius: '10px',
      overflow: 'hidden',
      boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.2)'
    },
    filler: {
      height: '100%',
      width: `${progress}%`,
      backgroundColor: '#007bff',
      transition: 'width 0.3s ease-in-out'
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.filler}></div>
    </div>
  );
}

export default ProgressBar;
