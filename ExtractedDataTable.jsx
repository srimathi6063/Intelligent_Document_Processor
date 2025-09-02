import React, { useState, useEffect } from 'react';

function ExtractedDataTable({ data, onChange }) {
  const [localData, setLocalData] = useState(data);
  const [editField, setEditField] = useState(null);
  const [editLineItem, setEditLineItem] = useState({ idx: null, col: null });

  useEffect(() => {
    setLocalData(data);
    setEditField(null);
    setEditLineItem({ idx: null, col: null });
  }, [data]);

  if (!data) return null;

  // Extract line_items and the other fields separately
  const { line_items = [], ...fields } = localData;

  // Internal CSS styles
  const styles = {
    container: {
      width: '100%',
      overflowX: 'auto'
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      marginBottom: '20px'
    },
    th: {
      borderBottom: '2px solid #ddd',
      textAlign: 'left',
      padding: '8px',
      backgroundColor: '#f3f3f3',
      fontWeight: 'bold'
    },
    td: {
      borderBottom: '1px solid #ddd',
      padding: '8px'
    },
    lineItemsHeader: {
      marginTop: '20px',
      fontWeight: 'bold',
      fontSize: '18px'
    }
  };

  // Helper to format keys for display
  const formatKey = (key) =>
    key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());

  const handleFieldClick = (key) => setEditField(key);
  
  const handleFieldBlur = (key, value) => {
    setEditField(null);
    const updated = { ...localData, [key]: value };
    setLocalData(updated);
    if (onChange) onChange(updated);
  };

  const handleLineCellClick = (idx, col) => setEditLineItem({ idx, col });
  
  const handleLineBlur = (idx, col, value) => {
    setEditLineItem({ idx: null, col: null });
    const updatedItems = line_items.map((item, i) =>
      i === idx ? { ...item, [col]: value } : item
    );
    const updated = { ...localData, line_items: updatedItems };
    setLocalData(updated);
    if (onChange) onChange(updated);
  };

  return (
    <div style={styles.container}>
      {/* General Fields Table */}
      <table style={styles.table}>
        <tbody>
          {Object.entries(fields).map(([key, value]) => {
            if (key === 'line_items') return null; // skip line_items here
            return (
              <tr key={key}>
                <th style={styles.th}>{formatKey(key)}</th>
                <td 
                  style={{
                    ...styles.td,
                    ...(editField === key ? { background: '#e6ffe6' } : {})
                  }}
                  onClick={() => handleFieldClick(key)}
                >
                  {editField === key ? (
                    <input
                      autoFocus
                      type="text"
                      value={value || ""}
                      style={{
                        width: "100%",
                        border: "1.5px solid #28a745",
                        padding: "4px 6px",
                        borderRadius: "4px",
                        background: "#f6fff6",
                      }}
                      onChange={(e) => {
                        const updated = { ...localData, [key]: e.target.value };
                        setLocalData(updated);
                      }}
                      onBlur={(e) => handleFieldBlur(key, e.target.value)}
                      onKeyDown={(e) =>
                        (e.key === "Enter" || e.key === "Tab") &&
                        handleFieldBlur(key, e.target.value)
                      }
                    />
                  ) : (
                    String(value || "N/A")
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Line Items Table */}
      {Array.isArray(line_items) && line_items.length > 0 && (
        <>
          <div style={styles.lineItemsHeader}>Line Items</div>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>S.NO</th>
                <th style={styles.th}>Description</th>
                <th style={styles.th}>Quantity</th>
                <th style={styles.th}>Unit Price</th>
                <th style={styles.th}>Total per Product</th>
              </tr>
            </thead>
            <tbody>
              {line_items.map((item, index) => (
                <tr key={index}>
                  {["S.NO", "description", "quantity", "unit_price", "total_per_product"].map((col) => (
                    <td
                      key={col}
                      style={{
                        ...styles.td,
                        ...(editLineItem.idx === index && editLineItem.col === col
                          ? { background: '#e6ffe6' }
                          : {})
                      }}
                      onClick={() => handleLineCellClick(index, col)}
                    >
                      {editLineItem.idx === index && editLineItem.col === col ? (
                        <input
                          autoFocus
                          type="text"
                          value={item[col] || ""}
                          style={{
                            width: "100%",
                            border: "1.5px solid #28a745",
                            padding: "4px 6px",
                            borderRadius: "4px",
                            background: "#f6fff6",
                          }}
                          onChange={(e) => {
                            const updatedItems = line_items.map((itm, i) =>
                              i === index ? { ...itm, [col]: e.target.value } : itm
                            );
                            const updated = { ...localData, line_items: updatedItems };
                            setLocalData(updated);
                          }}
                          onBlur={(e) => handleLineBlur(index, col, e.target.value)}
                          onKeyDown={(e) =>
                            (e.key === "Enter" || e.key === "Tab") &&
                            handleLineBlur(index, col, e.target.value)
                          }
                        />
                      ) : (
                        item[col] || "N/A"
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}

export default ExtractedDataTable;
