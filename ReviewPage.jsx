import React, { useState } from "react";
import ExtractedDataTable from "../components/ExtractedDataTable.jsx";
import VerificationStatus from "../components/VerificationStatus.jsx";
import ProgressBar from "../components/ProgressBar.jsx";
import SubmitButton from "../components/SubmitButton.jsx";
import DocumentPreview from "../components/DocumentPreview.jsx";

const styles = {
  container: {
    width: "100vw",
    minHeight: "100vh",
    background: "linear-gradient(135deg, #d9fdd3, #e0f7f9)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
    padding: "2rem",
    boxSizing: "border-box",
  },
  card: {
    background: "#ffffff",
    boxShadow: "0 10px 25px rgba(0,0,0,0.08)",
    borderRadius: "20px",
    padding: "2rem",
    maxWidth: "1400px",
    width: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    transition: "0.3s ease",
  },
  header: {
    fontSize: "2.5rem",
    fontWeight: 800,
    color: "#004d40",
    marginBottom: "0.7rem",
    textAlign: "center",
  },
  subheader: {
    fontSize: "1.2rem",
    color: "#00796b",
    fontWeight: 500,
    marginBottom: "2rem",
    textAlign: "center",
  },
  fileInfo: {
    background: "#f0fdfa",
    padding: "1rem",
    borderRadius: "12px",
    marginBottom: "2rem",
    width: "100%",
    textAlign: "center",
    border: "1px solid #e0f7f9",
  },
  tabContainer: {
    width: "100%",
    marginBottom: "2rem",
  },
  tabList: {
    display: "flex",
    borderBottom: "2px solid #e0f7f9",
    marginBottom: "2rem",
    overflowX: "auto",
    gap: "0.5rem",
  },
  tab: {
    padding: "1rem 1.5rem",
    fontSize: "1rem",
    fontWeight: "600",
    border: "none",
    background: "transparent",
    cursor: "pointer",
    borderBottom: "3px solid transparent",
    transition: "all 0.2s ease",
    whiteSpace: "nowrap",
    minWidth: "120px",
  },
  activeTab: {
    color: "#00796b",
    borderBottomColor: "#00796b",
    background: "#f0fdfa",
  },
  inactiveTab: {
    color: "#666",
  },
  tabContent: {
    width: "100%",
  },
  contentContainer: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "2rem",
    width: "100%",
    marginBottom: "2rem",
  },
  leftPanel: {
    display: "flex",
    flexDirection: "column",
    gap: "1rem",
  },
  rightPanel: {
    display: "flex",
    flexDirection: "column",
    gap: "1rem",
  },
  buttonContainer: {
    display: "flex",
    gap: "1rem",
    flexWrap: "wrap",
    justifyContent: "center",
    marginTop: "2rem",
  },
  button: {
    padding: "1rem 2rem",
    fontSize: "1.1rem",
    fontWeight: "600",
    border: "none",
    borderRadius: "12px",
    cursor: "pointer",
    transition: "all 0.2s ease-in-out",
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
  },
  primaryButton: {
    background: "linear-gradient(90deg, #00796b, #004d40)",
    color: "white",
    boxShadow: "0 4px 15px rgba(0,0,0,0.15)",
  },
  secondaryButton: {
    background: "#f0fdfa",
    color: "#00796b",
    border: "2px solid #00796b",
  },
  backButton: {
    background: "#e0f7f9",
    color: "#004d40",
    border: "2px solid #004d40",
  },
  buttonHover: {
    transform: "translateY(-2px)",
    boxShadow: "0 6px 20px rgba(0,0,0,0.2)",
  },
  loadingSpinner: {
    display: "inline-block",
    width: "20px",
    height: "20px",
    border: "3px solid #ffffff",
    borderRadius: "50%",
    borderTopColor: "transparent",
    animation: "spin 1s ease-in-out infinite",
  },
  checkboxContainer: {
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '16px',
    color: '#333',
    cursor: 'pointer',
    fontFamily: 'Arial, sans-serif',
  },
  checkbox: {
    width: '18px',
    height: '18px',
    cursor: 'pointer',
  },
  errorMessage: {
    background: "#ffebee",
    color: "#c62828",
    padding: "1rem",
    borderRadius: "8px",
    marginBottom: "1rem",
    border: "1px solid #ffcdd2",
  },
};

export default function ReviewPage({
  files,
  extractedDataList,
  setExtractedDataList,
  verificationReports,
  onSubmit,
  submitting,
  loading,
  progress,
  setModalMsg,
}) {
  const [activeTab, setActiveTab] = useState(0);
  const [sendEmail, setSendEmail] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(false);

  const handleSubmitToDatabase = async () => {
    try {
      const result = await onSubmit(false, activeTab);
      setModalMsg(result?.message || "Data submitted successfully!");
    } catch (error) {
      setModalMsg("Submission failed: " + error.message);
    }
  };

  const handleSendEmail = async () => {
    if (!sendEmail) return;
    
    setSendingEmail(true);
    try {
      const result = await onSubmit(true, activeTab);
      setModalMsg(result?.message || "Email sent successfully!");
    } catch (error) {
      setModalMsg("Email sending failed: " + error.message);
    } finally {
      setSendingEmail(false);
    }
  };

  const handleDataChange = (newData) => {
    const updatedList = [...extractedDataList];
    updatedList[activeTab] = newData;
    setExtractedDataList(updatedList);
  };

  if (!extractedDataList || extractedDataList.length === 0) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.header}>📄 Document Review</div>
          <div style={styles.errorMessage}>
            No extracted data available. Please try uploading files again.
          </div>
          <button
            style={{
              ...styles.button,
              ...styles.backButton
            }}
            onClick={() => window.history.back()}
          >
            ← Back to Upload
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>📄 Document Review</div>
        <div style={styles.subheader}>
          Review and edit the extracted data from your documents
        </div>

        <div style={styles.fileInfo}>
          <strong>Files:</strong> {files.length} document(s) processed successfully
        </div>

        <div style={styles.tabContainer}>
          <div style={styles.tabList}>
            {files.map((file, index) => (
              <button
                key={index}
                style={{
                  ...styles.tab,
                  ...(activeTab === index ? styles.activeTab : styles.inactiveTab)
                }}
                onClick={() => setActiveTab(index)}
              >
                {file.name || `Document ${index + 1}`}
              </button>
            ))}
          </div>

          <div style={styles.tabContent}>
            {files.map((file, index) => (
              <div key={index} style={{ display: activeTab === index ? 'block' : 'none' }}>
                {extractedDataList[index] ? (
                  <div style={styles.contentContainer}>
                    <div style={styles.leftPanel}>
                      <ExtractedDataTable
                        data={extractedDataList[index]}
                        onChange={handleDataChange}
                      />
                      <VerificationStatus
                        status={verificationReports[index] || ""}
                      />
                      {/* Debug info */}
                      {console.log(`Verification report for index ${index}:`, verificationReports[index])}
                    </div>
                    <div style={styles.rightPanel}>
                      <DocumentPreview file={file} />
                    </div>
                  </div>
                ) : (
                  <div style={styles.errorMessage}>
                    Failed to extract data from this document. Please try again.
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Email Checkbox */}
        <div style={styles.checkboxContainer}>
          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
              style={styles.checkbox}
            />
            📧 Send results via email (optional)
          </label>
        </div>

        <div style={styles.buttonContainer}>
          <button
            style={{
              ...styles.button,
              ...styles.primaryButton
            }}
            onClick={handleSubmitToDatabase}
            disabled={submitting || loading}
          >
            {submitting ? (
              <>
                <div style={styles.loadingSpinner}></div>
                Submitting...
              </>
            ) : (
              "💾 Submit to Database"
            )}
          </button>
          
          {sendEmail && (
            <button
              style={{
                ...styles.button,
                ...styles.primaryButton
              }}
              onClick={handleSendEmail}
              disabled={submitting || loading || sendingEmail}
            >
              {sendingEmail ? (
                <>
                  <div style={styles.loadingSpinner}></div>
                  Sending Email...
                </>
              ) : (
                "📧 Send Email"
              )}
            </button>
          )}
          
          <button
            style={{
              ...styles.button,
              ...styles.backButton
            }}
            onClick={() => window.history.back()}
            disabled={submitting || loading}
          >
            ← Back to Upload
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
