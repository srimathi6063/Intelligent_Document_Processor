

// import React, { useState } from "react";

// const styles = {
//   container: {
//     width: "100vw",
//     minHeight: "100vh",
//     backgroundColor: "#f0f8f0",
//     display: "flex",
//     flexDirection: "column",
//     alignItems: "center",
//     fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
//     padding: "2rem",
//     boxSizing: "border-box",
//   },
//   branding: {
//     fontSize: "2.3rem",
//     fontWeight: 700,
//     color: "#006d77",
//     marginBottom: "0.5rem",
//   },
//   subhead: {
//     fontSize: "1.35rem",
//     color: "#22664d",
//     fontWeight: 500,
//     marginBottom: "2rem",
//     textAlign: "center",
//     maxWidth: "620px",
//   },
//   uploadZone: {
//     width: "100%",
//     maxWidth: "580px",
//     border: "2.5px dashed #006d77",
//     borderRadius: "16px",
//     background: "#fff",
//     minHeight: "160px",
//     display: "flex",
//     alignItems: "center",
//     justifyContent: "center",
//     fontSize: "1.2rem",
//     color: "#006d77",
//     cursor: "pointer",
//     marginBottom: "2rem",
//     textAlign: "center",
//     fontWeight: 500,
//     userSelect: "none",
//   },
//   fileInput: {
//     display: "none",
//   },
//   select: {
//     width: "320px",
//     padding: "0.8rem",
//     fontSize: "1.05rem",
//     marginBottom: "1.5rem",
//     borderRadius: "8px",
//     border: "1.5px solid #228b71",
//     color: "#005c41",
//     background: "#e9f7ef",
//     fontWeight: 500,
//   },
//   fileInfo: {
//     fontSize: "1rem",
//     color: "#333",
//     marginBottom: "1.5rem",
//     marginTop: "0.5rem",
//     textAlign: "center",
//   },
//   button: {
//     padding: "1rem 2.2rem",
//     fontSize: "1.2rem",
//     backgroundColor: "#006d77",
//     color: "white",
//     fontWeight: "700",
//     border: "none",
//     borderRadius: "12px",
//     cursor: "pointer",
//     marginTop: "1rem",
//     marginBottom: "1.5rem"
//   },
//   buttonDisabled: {
//     backgroundColor: "#b5d5c5",
//     cursor: "not-allowed",
//   },
// };

// export default function UploadPage({ onExtract, loading }) {
//   const [selectedFile, setSelectedFile] = useState(null);
//   const [provider, setProvider] = useState("");

//   const handleFileChange = (e) => {
//     if (e.target.files.length > 0) {
//       setSelectedFile(e.target.files[0]);
//     }
//   };

//   const handleProviderChange = (e) => {
//     setProvider(e.target.value);
//   };

//   const handleExtractClick = () => {
//     if (provider && selectedFile && onExtract && !loading) {
//       onExtract({ provider, file: selectedFile });
//     }
//   };

//   return (
//     <div style={styles.container}>
//       <div style={styles.branding}>Invoice/PO AI Extractor & Review System</div>
//       <div style={styles.subhead}>
//         Upload your documents, extract data with AI, review and edit, then submit to database
//       </div>
//       <select
//         value={provider}
//         onChange={handleProviderChange}
//         style={styles.select}
//       >
//         <option value="">-- Select Document Processor --</option>

//         <option value="aws">AWS IDP</option>
//       </select>
//       <label htmlFor="file-upload" style={styles.uploadZone}>
//         {selectedFile
//           ? selectedFile.name
//           : "Click or drag file here to upload (.pdf, .docx, .txt, .md)"}
//         <input
//           id="file-upload"
//           type="file"
//           accept=".pdf,.docx,.txt,.md"
//           style={styles.fileInput}
//           onChange={handleFileChange}
//         />
//       </label>
//       {selectedFile && (
//         <div style={styles.fileInfo}>
//           File size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
//         </div>
//       )}
//       <button
//         style={{
//           ...styles.button,
//           ...(provider && selectedFile && !loading ? {} : styles.buttonDisabled),
//         }}
//         disabled={!provider || !selectedFile || loading}
//         onClick={handleExtractClick}
//       >
//         {loading ? "Extracting..." : "Extract & Process Data"}
//       </button>
//     </div>
//   );
// }


import React, { useState } from "react";

const styles = {
  container: {
    width: "100vw",
    minHeight: "100vh",
    backgroundColor: "#f0f8f0",
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
    padding: "2.5rem",
    maxWidth: "700px",
    width: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    transition: "0.3s ease",
  },
  branding: {
    fontSize: "2.5rem",
    fontWeight: 800,
    color: "#006d77",
    marginBottom: "0.6rem",
    textAlign: "center",
  },
  subhead: {
    fontSize: "1.2rem",
    color: "#22664d",
    fontWeight: 500,
    marginBottom: "2rem",
    textAlign: "center",
    lineHeight: 1.5,
  },
  select: {
    width: "100%",
    padding: "1rem",
    fontSize: "1.1rem",
    marginBottom: "2rem",
    borderRadius: "12px",
    border: "1.5px solid #228b71",
    color: "#005c41",
    background: "#e9f7ef",
    fontWeight: 500,
    outline: "none",
    transition: "0.2s",
  },
  uploadZone: {
    width: "100%",
    border: "2.5px dashed #006d77",
    borderRadius: "16px",
    background: "#fff",
    minHeight: "180px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "1.2rem",
    color: "#006d77",
    cursor: "pointer",
    marginBottom: "1.5rem",
    textAlign: "center",
    fontWeight: 600,
    userSelect: "none",
    transition: "all 0.2s ease-in-out",
  },
  uploadZoneHover: {
    background: "#f0f8f0",
    borderColor: "#22664d",
    color: "#22664d",
  },
  fileInput: {
    display: "none",
  },
  fileInfo: {
    fontSize: "1rem",
    color: "#333",
    marginBottom: "1.5rem",
    textAlign: "center",
  },
  button: {
    padding: "1rem 2.5rem",
    fontSize: "1.2rem",
    backgroundColor: "#006d77",
    color: "white",
    fontWeight: "700",
    border: "none",
    borderRadius: "14px",
    cursor: "pointer",
    marginTop: "1rem",
    boxShadow: "0 8px 20px rgba(0,0,0,0.15)",
    transition: "all 0.2s ease-in-out",
  },
  buttonHover: {
    transform: "translateY(-2px)",
    boxShadow: "0 12px 25px rgba(0,0,0,0.2)",
    backgroundColor: "#005c41",
  },
  buttonDisabled: {
    backgroundColor: "#b5d5c5",
    cursor: "not-allowed",
    boxShadow: "none",
  },

};

export default function UploadPage({ onExtract, loading }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [classification, setClassification] = useState("");
  const [hoverUpload, setHoverUpload] = useState(false);
  const [hoverButton, setHoverButton] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      setSelectedFiles(Array.from(e.target.files));
    }
  };

  const handleClassificationChange = (e) => {
    setClassification(e.target.value);
  };

  const handleExtractClick = () => {
    if (classification && selectedFiles.length > 0 && onExtract && !loading) {
      onExtract({ classification, files: selectedFiles });
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.branding}>📄 AI Invoice/PO Extractor</div>
        <div style={styles.subhead}>
          Upload your document → Extract with AI → Review → Submit 🚀
        </div>

        <select
          value={classification}
          onChange={handleClassificationChange}
          style={styles.select}
        >
          <option value="">-- Select Classification --</option>
          <option value="invoice_process">Invoice Process</option>
          <option value="document_summarization">Document Summarization</option>
        </select>

        <label
          htmlFor="file-upload"
          style={{
            ...styles.uploadZone,
            ...(hoverUpload ? styles.uploadZoneHover : {}),
          }}
          onMouseEnter={() => setHoverUpload(true)}
          onMouseLeave={() => setHoverUpload(false)}
        >
          {selectedFiles.length > 0
            ? `✅ ${selectedFiles.length} file(s) selected`
            : "📂 Click or drag files here to upload (.pdf, .docx, .txt, .md)"}
          <input
            id="file-upload"
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.md"
            style={styles.fileInput}
            onChange={handleFileChange}
          />
        </label>

        {selectedFiles.length > 0 && (
          <div style={styles.fileInfo}>
            {selectedFiles.length} file(s) selected • Total size: {(selectedFiles.reduce((acc, file) => acc + file.size, 0) / (1024 * 1024)).toFixed(2)} MB
          </div>
        )}

        <button
          style={{
            ...styles.button,
            ...(hoverButton && classification && selectedFiles.length > 0 && !loading
              ? styles.buttonHover
              : {}),
            ...(classification && selectedFiles.length > 0 && !loading
              ? {}
              : styles.buttonDisabled),
          }}
          disabled={!classification || selectedFiles.length === 0 || loading}
          onMouseEnter={() => setHoverButton(true)}
          onMouseLeave={() => setHoverButton(false)}
          onClick={handleExtractClick}
        >
          {loading ? "⏳ Extracting..." : "⚡ Extract & Process"}
        </button>
      </div>
    </div>
  );
}
