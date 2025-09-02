import React from 'react';

function VerificationStatus({ status }) {
  const styles = {
    container: {
      padding: '15px',
      borderRadius: '8px',
      marginBottom: '20px',
      fontWeight: 'bold',
      fontFamily: 'Arial, sans-serif'
    },
    verified: {
      backgroundColor: '#d4edda',
      border: '1px solid #c3e6cb',
      color: '#155724'
    },
    partiallyVerified: {
      backgroundColor: '#fff3cd',
      border: '1px solid #ffeeba',
      color: '#856404'
    },
    failed: {
      backgroundColor: '#f8d7da',
      border: '1px solid #f5c6cb',
      color: '#721c24'
    },
    defaultStyle: {
      backgroundColor: '#e2e3e5',
      border: '1px solid #d6d8db',
      color: '#383d41'
    }
  };

  // Determine style based on status string (case-insensitive)
  let style = styles.defaultStyle;
  if (typeof status === 'string') {
    const lower = status.toLowerCase();
    if (lower.includes('verified')) {
      style = lower.includes('partial') ? styles.partiallyVerified : styles.verified;
    } else if (lower.includes('fail')) {
      style = styles.failed;
    }
  }

  return (
    <div style={{ ...styles.container, ...style }}>
      {status || 'Verification status not available.'}
    </div>
  );
}

export default VerificationStatus;
