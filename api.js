// api.js

const BASE_URL = "http://localhost:9000";






// AWS
export async function awsUploadFile(files) {
  const formData = new FormData();
  
  // Handle both single file and multiple files
  if (Array.isArray(files)) {
    files.forEach(file => {
      formData.append("files", file);
    });
  } else {
    formData.append("files", files);
  }

  const response = await fetch(`${BASE_URL}/aws/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(`AWS upload failed: ${response.statusText}`);
  return response.json();
}

export async function awsExtractData(s3Key) {
  const response = await fetch(`${BASE_URL}/aws/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ s3_key: s3Key }),
  });

  if (!response.ok) throw new Error(`AWS extract failed: ${response.statusText}`);
  return response.json();
}

export async function awsExtractText(s3Key) {
  const response = await fetch(`${BASE_URL}/aws/extract_text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ s3_key: s3Key }),
  });

  if (!response.ok) throw new Error(`AWS extract text failed: ${response.statusText}`);
  return response.json();
}

export async function awsSubmitData(extractedData, sendEmail = false) {
  console.log("Submitting data with sendEmail:", sendEmail);
  const requestBody = { extractedData, sendEmail };
  console.log("Request body:", requestBody);
  
  const response = await fetch(`${BASE_URL}/aws/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(requestBody),
  });

  // Parse the response JSON regardless of status
  const result = await response.json();
  
  if (!response.ok) {
    // Create an error with the server's message
    const error = new Error(result.message || `HTTP ${response.status}: ${response.statusText}`);
    error.response = {
      status: response.status,
      data: result
    };
    throw error;
  }
  
  return result;
}

// Document Summarization
export async function summarizeDocument(files, sendEmail = false) {
  const formData = new FormData();
  
  // Handle both single file and multiple files
  if (Array.isArray(files)) {
    files.forEach(file => {
      formData.append("files", file);
    });
  } else {
    formData.append("files", files);
  }
  
  formData.append("send_email", sendEmail.toString());

  const response = await fetch(`${BASE_URL}/summarize`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(`Summarization failed: ${response.statusText}`);
  return response.json();
}

// Send edited summary via email
export async function sendEditedSummaryEmail(filename, editedSummary, sendEmail = false) {
  const formData = new FormData();
  formData.append("file", filename);
  formData.append("edited_summary", editedSummary);
  formData.append("send_email", sendEmail.toString());

  const response = await fetch(`${BASE_URL}/send-summary-email`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(`Email sending failed: ${response.statusText}`);
  return response.json();
}

// Send invoice email only
export async function sendInvoiceEmail(extractedData) {
  console.log("Sending invoice email with data:", extractedData);
  
  const response = await fetch(`${BASE_URL}/aws/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      extractedData, 
      sendEmail: true,
      emailOnly: true // Flag to indicate this is email-only request
    }),
  });

  // Parse the response JSON regardless of status
  const result = await response.json();
  
  if (!response.ok) {
    // Create an error with the server's message
    const error = new Error(result.message || `HTTP ${response.status}: ${response.statusText}`);
    error.response = {
      status: response.status,
      data: result
    };
    throw error;
  }
  
  return result;
}


