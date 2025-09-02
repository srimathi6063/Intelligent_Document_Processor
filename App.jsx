import React, { useState } from "react";
import UploadPage from "./pages/UploadPage";
import ReviewPage from "./pages/ReviewPage";
import SummarizationPage from "./pages/SummarizationPage";
import PopupModal from "./pages/PopupModal";
import { ChatProvider } from "./components/ChatProvider";
import {
  awsUploadFile,
  awsExtractData,
  awsExtractText,
  awsSubmitData,
  summarizeDocument
} from "../src/utils/api";

const BASE_URL = "http://localhost:9000";

export default function App() {
  const [step, setStep] = useState("upload"); // "upload", "review", or "summarization"
  const [classification, setClassification] = useState(null);
  const [files, setFiles] = useState([]); // Store multiple files
  const [extractedDataList, setExtractedDataList] = useState([]); // Store multiple extracted data
  const [verificationReports, setVerificationReports] = useState([]); // Store multiple verification reports
  const [summaries, setSummaries] = useState([]); // Store multiple summaries
  const [summaryFilePaths, setSummaryFilePaths] = useState([]); // Store file paths for summarization emails
  const [sendEmail, setSendEmail] = useState(false);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [modalMsg, setModalMsg] = useState("");

  // --- Extract & Process handler ---
  const handleExtract = async ({ classification, files }) => {
    setClassification(classification);
    setFiles(files);
    setLoading(true);
    setProgress(30);

    try {
      if (classification === "invoice_process") {
        setProgress(40);
        const uploadRes = await awsUploadFile(files);
        setProgress(60);
        
        // Process each uploaded file
        const extractedDataResults = [];
        const verificationReportResults = [];
        
        for (const result of uploadRes.results) {
          if (result.success) {
            const extractRes = await awsExtractData(result.s3_key);
            extractedDataResults.push(extractRes.extracted_data);
            verificationReportResults.push(extractRes.verification_report);
          } else {
            // Handle failed uploads
            extractedDataResults.push(null);
            verificationReportResults.push(`Upload failed: ${result.error}`);
          }
        }
        
        console.log("Verification reports received:", verificationReportResults);
        setExtractedDataList(extractedDataResults);
        setVerificationReports(verificationReportResults);
        setProgress(90);
        setStep("review");
      } else if (classification === "document_summarization") {
        setProgress(40);
        
        // For document summarization, we need to check if files are scanned PDFs
        // If they are, we should use AWS Textract first, then summarize
        const hasScannedPDFs = files.some(file => 
          file.type === 'application/pdf' && file.size > 100000 // PDFs larger than 100KB are likely scanned
        );
        
        if (hasScannedPDFs) {
          console.log("📄 Detected scanned PDFs, using AWS Textract for text extraction...");
          
          // Use AWS Textract for scanned PDFs
          const uploadRes = await awsUploadFile(files);
          setProgress(60);
          
          // Process each uploaded file with AWS Textract
          const summaryResults = [];
          
          for (const result of uploadRes.results) {
            if (result.success) {
              const extractRes = await awsExtractText(result.s3_key);
              const extractedText = extractRes.extracted_text || "";
              
              if (extractedText) {
                // Now call the summarization endpoint with the extracted text
                const summaryFormData = new FormData();
                summaryFormData.append("extracted_text", extractedText);
                summaryFormData.append("filename", result.filename);
                summaryFormData.append("send_email", sendEmail.toString());
                
                const summaryResponse = await fetch(`${BASE_URL}/summarize_text`, {
                  method: "POST",
                  body: summaryFormData,
                });
                
                if (summaryResponse.ok) {
                  const summaryResult = await summaryResponse.json();
                  summaryResults.push({
                    ...summaryResult,
                    file_path: result.s3_key,
                    original_filename: result.filename
                  });
                } else {
                  summaryResults.push({
                    success: false,
                    error: `Summarization failed for ${result.filename}`,
                    file_path: result.s3_key,
                    original_filename: result.filename
                  });
                }
              } else {
                summaryResults.push({
                  success: false,
                  error: `No text extracted from ${result.filename}`,
                  file_path: result.s3_key,
                  original_filename: result.filename
                });
              }
            } else {
              summaryResults.push({
                success: false,
                error: `Upload failed for ${result.filename}`,
                original_filename: result.filename
              });
            }
          }
          
          setSummaries(summaryResults);
          setSummaryFilePaths(summaryResults.map(result => result.file_path).filter(Boolean));
        } else {
          // Use local processing for non-scanned documents
          const summaryRes = await summarizeDocument(files);
          setSummaries(summaryRes.results || []);
          setSummaryFilePaths(summaryRes.results?.map(result => result.file_path) || []);
        }
        
        setProgress(90);
        setStep("summarization");
      }
    } catch (e) {
      setModalMsg("Processing failed: " + e.message);
    } finally {
      setLoading(false);
      setProgress(0);
    }
  };

  // --- Submit handler ---
  // const handleSubmit = async () => {
  //   setSubmitting(true);
  //   let result;
  //   try {

  //     console.log(result,"This is my resulttttttttttttttttttttttttttttttttttttttttttttttttt")
  //     setModalMsg(result?.message || "Submission successful!");
  //   } catch (e) {
  //     setModalMsg("Submission failed: " + result?.message);
  //   }
  //   setSubmitting(false);
  // };

  const handleSubmit = async (sendEmail = false, index = 0) => {
  setSubmitting(true);
  try {
    const extractedData = extractedDataList[index];
    if (!extractedData) {
      throw new Error("No data available for submission");
    }
    const result = await awsSubmitData(extractedData, sendEmail);
    console.log(result, "This is my result");
    return result; // Return the result so the calling component can handle it
  } catch (error) {
    console.error("Submission error:", error);
    
    // Check if error has a response with data (from our custom error)
    let errorMessage = "Submission failed";
    
    if (error.response && error.response.data && error.response.data.message) {
      errorMessage = error.response.data.message;
    } else if (error.message) {
      errorMessage = error.message;
    }
    
    throw new Error(errorMessage); // Throw error so calling component can handle it
  } finally {
    setSubmitting(false);
  }
};

  const handleBackToUpload = () => {
    setStep("upload");
    setClassification(null);
    setFiles([]);
    setExtractedDataList([]);
    setVerificationReports([]);
    setSummaries([]);
    setSummaryFilePaths([]);
    setSendEmail(false);
  };

  // --- Render ---
  const renderContent = () => {
    if (step === "upload") {
      return (
        <>
          <UploadPage onExtract={handleExtract} loading={loading} />
          <PopupModal show={!!modalMsg} onClose={() => setModalMsg("")}>
            {modalMsg}
          </PopupModal>
        </>
      );
    }

    if (step === "review") {
      return (
        <>
          <ReviewPage
            files={files}
            extractedDataList={extractedDataList}
            setExtractedDataList={setExtractedDataList}
            verificationReports={verificationReports}
            onSubmit={handleSubmit}
            submitting={submitting}
            loading={loading}
            progress={progress}
            setModalMsg={setModalMsg}
          />
          <PopupModal show={!!modalMsg} onClose={() => setModalMsg("")}>
            {modalMsg}
          </PopupModal>
        </>
      );
    }

    if (step === "summarization") {
      return (
        <>
          <SummarizationPage
            files={files}
            summaries={summaries}
            setSummaries={setSummaries}
            filePaths={summaryFilePaths}
            onBack={handleBackToUpload}
            onDownload={(editedSummaries) => {
              // Handle download functionality for multiple files
              editedSummaries.forEach((summary, index) => {
                const file = files[index];
                const blob = new Blob([summary], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${file?.name?.replace(/\.[^/.]+$/, '') || 'document'}_summary.txt`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
              });
            }}
            loading={loading}
          />
          <PopupModal show={!!modalMsg} onClose={() => setModalMsg("")}>
            {modalMsg}
          </PopupModal>
        </>
      );
    }

    return null;
  };

  return (
    <ChatProvider>
      {renderContent()}
    </ChatProvider>
  );
}
