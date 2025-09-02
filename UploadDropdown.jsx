import React from 'react';

function UploadDropdown({ selectedClassification, onSelect }) {
  const styles = {
    container: {
      marginBottom: '30px',
      width: '300px',
      fontFamily: 'Arial, sans-serif'
    },
    select: {
      width: '100%',
      padding: '12px',
      fontSize: '18px',
      borderRadius: '6px',
      border: '1px solid #ccc',
      cursor: 'pointer',
      outline: 'none'
    }
  };

  return (
    <div style={styles.container}>
      <select
        value={selectedClassification}
        onChange={(e) => onSelect(e.target.value)}
        style={styles.select}
      >
        <option value="">-- Select Classification --</option>
        <option value="invoice_process">Invoice Process</option>
        <option value="document_summarization">Document Summarization</option>
      </select>
    </div>
  );
}

export default UploadDropdown;
