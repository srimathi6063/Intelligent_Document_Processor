import React, { useState } from "react";

const styles = {
  container: {
    background: "#f8f9fa",
    borderRadius: "12px",
    padding: "1rem",
    border: "1px solid #e0f7f9",
  },
  header: {
    fontSize: "1.2rem",
    fontWeight: "600",
    color: "#004d40",
    marginBottom: "1rem",
    textAlign: "center",
  },
  pdfWrapper: {
    borderRadius: "8px",
    background: "#fff",
    padding: "0.5rem",
    width: "100%",
    minHeight: "400px",
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    border: "1px solid #ddd",
  },
  pdfControls: {
    display: "flex",
    gap: "0.5rem",
    marginBottom: "0.5rem",
    alignItems: "center",
    justifyContent: "center",
  },
  controlButton: {
    background: "#f5f5f5",
    border: "none",
    borderRadius: "6px",
    width: "32px",
    height: "32px",
    fontSize: "1.2rem",
    fontWeight: "700",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  zoomLabel: {
    fontWeight: "600",
    fontSize: "1rem",
    color: "#00796b",
    minWidth: "60px",
    textAlign: "center",
  },
  pdfEmbed: {
    width: "100%",
    height: "auto",
    minHeight: "350px",
    border: "none",
    borderRadius: "6px",
  },
  noPreview: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    height: "350px",
    color: "#666",
    fontSize: "1rem",
    textAlign: "center",
    background: "#f9f9f9",
    borderRadius: "6px",
    border: "1px dashed #ccc",
  },
  fileInfo: {
    background: "#e8f5e8",
    padding: "0.5rem",
    borderRadius: "6px",
    marginBottom: "0.5rem",
    fontSize: "0.9rem",
    color: "#2d5a2d",
    textAlign: "center",
  },
};

export default function DocumentPreview({ file }) {
  const [zoom, setZoom] = useState(1);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.5));

  if (!file) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>📄 Document Preview</div>
        <div style={styles.noPreview}>No document selected</div>
      </div>
    );
  }

  const isPDF = file.type === "application/pdf";
  const fileSize = (file.size / (1024 * 1024)).toFixed(2);

  return (
    <div style={styles.container}>
      <div style={styles.header}>📄 Document Preview</div>
      
      <div style={styles.fileInfo}>
        <strong>{file.name}</strong> • {fileSize} MB • {file.type}
      </div>

      <div style={styles.pdfWrapper}>
        {isPDF ? (
          <>
            <div style={styles.pdfControls}>
              <button
                onClick={handleZoomOut}
                style={styles.controlButton}
                title="Zoom Out"
              >
                −
              </button>
              <span style={styles.zoomLabel}>{Math.round(zoom * 100)}%</span>
              <button
                onClick={handleZoomIn}
                style={styles.controlButton}
                title="Zoom In"
              >
                +
              </button>
            </div>
            <embed
              src={URL.createObjectURL(file)}
              type="application/pdf"
              style={{
                ...styles.pdfEmbed,
                transform: `scale(${zoom})`,
                transformOrigin: "top center",
              }}
              title="Document Preview"
            />
          </>
        ) : (
          <div style={styles.noPreview}>
            <div>
              <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>📄</div>
              <div>Preview not available for file type:</div>
              <div style={{ fontWeight: "600", marginTop: "0.5rem" }}>
                {file.type || "Unknown"}
              </div>
              <div style={{ fontSize: "0.9rem", marginTop: "1rem", color: "#888" }}>
                Supported formats: PDF
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
