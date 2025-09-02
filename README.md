# AI Invoice/PO Extractor with Chat Functionality

A comprehensive document processing application that extracts data from invoices and purchase orders using AI, with integrated chat functionality for querying both invoice databases and document content.

## Features

- **Document Processing**: Extract structured data from PDF invoices and purchase orders
- **AI-Powered Extraction**: Uses AWS Bedrock with Claude Opus 4.1 for accurate data extraction
- **Chat Interface**: Interactive chat system with two modes:
  - **Invoice Mode**: Query MySQL database for invoice information
  - **Summarization Mode**: Ask questions about uploaded documents
- **Real-time Processing**: Concurrent document processing for chat functionality
- **Modern UI**: React-based frontend with responsive design

## Architecture

### Backend (Flask)
- **Port**: 9000
- **Framework**: Flask with CORS support
- **AI**: AWS Bedrock (Claude Opus 4.1)
- **Database**: MySQL for invoice data
- **Document Storage**: In-memory storage for chat functionality

### Frontend (React)
- **Port**: 3000
- **Framework**: React with Vite
- **Styling**: CSS-in-JS with modern design
- **State Management**: React Context API

## Prerequisites

- Python 3.8+
- Node.js 16+
- AWS Account with Bedrock access
- MySQL Database (optional, for invoice queries)

## Installation

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd BE_IDP_PO
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file with:
   ```env
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_DEFAULT_REGION=us-east-1
   
   # MySQL Configuration (optional)
   MYSQL_HOST=localhost
   MYSQL_USER=your_username
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=your_database
   ```

5. Start the backend server:
   ```bash
   python app.py
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd FE_IDP_PO
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

1. **Upload Documents**: Use the main interface to upload PDF invoices or purchase orders
2. **Extract Data**: The system will automatically extract structured data using AI
3. **Chat Interface**: Click the chat icon in the bottom-right corner
4. **Select Mode**: Choose between "Invoice" or "Summarization" modes
5. **Ask Questions**: Query your data or ask about uploaded documents

## API Endpoints

### Document Processing
- `POST /aws/upload` - Upload documents to S3
- `POST /aws/extract` - Extract data from uploaded documents
- `POST /aws/submit` - Submit extracted data

### Chat Functionality
- `POST /chat/query` - Send chat messages
- `GET /chat/history` - Get chat history
- `POST /chat/clear` - Clear chat history
- `POST /chat/process-document` - Process documents for chat

## Configuration

### AWS Bedrock
The application uses AWS Bedrock with Claude Opus 4.1 for:
- Document data extraction
- Chat responses
- Natural language processing

### MySQL Database
For invoice queries, configure your MySQL database in the `.env` file. The system will automatically connect and handle queries.

## Production Deployment

### Backend
- Use a production WSGI server like Gunicorn
- Set up proper logging and monitoring
- Configure environment variables securely
- Use a production database for document storage

### Frontend
- Build for production: `npm run build`
- Serve static files from a web server
- Configure proper CORS settings
- Set up environment variables for API endpoints

## Security Considerations

- Secure AWS credentials
- Implement proper authentication
- Validate file uploads
- Sanitize user inputs
- Use HTTPS in production
- Implement rate limiting

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure AWS credentials are properly configured
2. **CORS Errors**: Check that the backend is running on the correct port
3. **MySQL Connection**: Verify database credentials and connectivity
4. **File Uploads**: Check file size limits and supported formats

### Logs
- Backend logs are available in the console
- Check browser developer tools for frontend errors
- Monitor AWS CloudWatch for Bedrock usage

## License

This project is proprietary software. All rights reserved.

## Support

For technical support or questions, please contact the development team.
