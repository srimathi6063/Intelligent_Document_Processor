import React from 'react';

function FileUploader({ onFileSelect }) {
  const styles = {
    container: {
      width: '100vw',
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      border: '4px dashed #007bff',
      borderRadius: '12px',
      cursor: 'pointer',
      boxSizing: 'border-box',
      color: '#007bff',
      fontSize: '24px',
      fontWeight: '600',
      fontFamily: 'Arial, sans-serif',
      userSelect: 'none',
      padding: '20px',
      textAlign: 'center'
    },
    input: {
      display: 'none'
    }
  };

  // Handle drop event
  const onDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileSelect(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  };

  // Handle drag over event (to allow drop)
  const onDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div
      style={styles.container}
      onDrop={onDrop}
      onDragOver={onDragOver}
      onClick={() => document.getElementById('file-input').click()}
    >
      Click or drag file here to upload
      <input
        id="file-input"
        type="file"
        accept=".pdf,.docx,.txt,.md"
        style={styles.input}
        onChange={(e) => {
          if (e.target.files.length > 0) {
            onFileSelect(e.target.files[0]);
          }
        }}
      />
    </div>
  );
}

export default FileUploader;
