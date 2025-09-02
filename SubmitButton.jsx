import React, { useState } from 'react';

function SubmitButton({ disabled, onSubmit }) {
  const [popup, setPopup] = useState(null); // { success: boolean, message: string } or null

  // Internal CSS styles
  const styles = {
    button: {
      padding: '12px 25px',
      backgroundColor: disabled ? '#cccccc' : '#007bff',
      color: 'white',
      fontSize: '16px',
      border: 'none',
      borderRadius: '5px',
      cursor: disabled ? 'not-allowed' : 'pointer',
      outline: 'none',
      userSelect: 'none'
    },
    popupOverlay: {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(0,0,0,0.4)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 9999
    },
    popupContent: {
      backgroundColor: 'white',
      padding: '30px',
      borderRadius: '8px',
      textAlign: 'center',
      width: '320px',
      boxShadow: '0 3px 10px rgba(0,0,0,0.3)'
    },
    popupTitle: {
      marginBottom: '15px',
      fontWeight: 'bold',
      fontSize: '18px',
      color: '#333'
    },
    popupMessage: {
      fontSize: '16px',
      color: '#555'
    },
    closeBtn: {
      marginTop: '20px',
      padding: '8px 20px',
      border: 'none',
      backgroundColor: '#007bff',
      color: 'white',
      borderRadius: '5px',
      cursor: 'pointer'
    }
  };

  // Wrapper for submit action
  const handleClick = async () => {
    if (disabled) return;

    try {
      const result = await onSubmit();
      if (result && result.success) {
        showPopup(true, 'Submission successful!');
      } else {
        showPopup(false, result?.message || 'Submission failed');
      }
    } catch (e) {
      showPopup(false, `Submission error: ${e.message}`);
    }
  };

  const showPopup = (success, message) => {
    setPopup({ success, message });
  };

  const closePopup = () => setPopup(null);

  return (
    <>
      <button style={styles.button} disabled={disabled} onClick={handleClick}>
        Submit to Database
      </button>

      {popup && (
        <div style={styles.popupOverlay} onClick={closePopup}>
          <div style={styles.popupContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.popupTitle}>{popup.success ? 'Success' : 'Error'}</div>
            <div style={styles.popupMessage}>{popup.message}</div>
            <button style={styles.closeBtn} onClick={closePopup}>Close</button>
          </div>
        </div>
      )}
    </>
  );
}

export default SubmitButton;
