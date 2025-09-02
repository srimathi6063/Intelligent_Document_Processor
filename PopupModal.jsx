import React from "react";

const overlayStyle = {
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundColor: "rgba(0,0,0,0.5)",
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  zIndex: 9999,
};

const modalStyle = {
  background: "white",
  padding: "2rem",
  borderRadius: "12px",
  boxShadow: "0 0 20px rgba(0,0,0,0.3)",
  maxWidth: "400px",
  textAlign: "center",
};

const buttonStyle = {
  marginTop: "1rem",
  padding: "0.6rem 1.2rem",
  backgroundColor: "#28a745",
  color: "white",
  border: "none",
  borderRadius: "8px",
  cursor: "pointer",
  fontWeight: "600",
};

export default function PopupModal({ show, onClose, children }) {
  if (!show) return null;

  return (
    <div style={overlayStyle}>
      <div style={modalStyle}>
        <div>{children}</div>
        <button style={buttonStyle} onClick={onClose}>
          OK
        </button>
      </div>
    </div>
  );
}
