# Auto-Receipts: Automated Receipt Processing System

## Overview

This project is a web application designed to automate the processing of scanned receipts. It leverages OCR/AI to extract key details from PDF receipts and stores the structured data in a SQLite database. The system provides REST APIs for managing and retrieving receipt information, making it a comprehensive solution for digital receipt management.

## Features

- **Multi-format Receipt Uploads**: Upload scanned receipts in PDF, PNG, JPG, and JPEG formats
- **File Validation**: Ensures that all uploaded files are valid receipts before processing
- **AI-Powered Data Extraction**: Uses **Gemini models through openai library** to extract key information such as:
  - Merchant name
  - Purchase date and time
  - Total amount and currency
  - Payment method
  - Category classification
  - Line items with descriptions, quantities, and prices
- **Structured Database Storage**: Stores extracted data in an organized SQLite database
- **RESTful API**: Complete set of APIs for seamless receipt management and data retrieval
- **Advanced Duplicate Detection**: SHA-256 file hash-based duplicate detection with multiple handling strategies
- **Flexible Duplicate Handling**: Choose how to handle duplicates with different strategies for uploads and processing

## Duplicate Detection & Handling

The system uses SHA-256 file hashing to detect exact duplicate files and provides multiple strategies for handling them:

### Upload Duplicate Strategies

| Strategy | Description | HTTP Status | Use Case |
|----------|-------------|-------------|----------|
| **`reject`** (default) | Reject duplicate uploads with detailed information about the existing file | 409 Conflict | Prevent accidental duplicates |
| **`update`** | Update the existing receipt metadata with new file information | 200 OK | Replace file with updated version |

### Processing Duplicate Strategies

| Strategy | Description | HTTP Status | Use Case |
|----------|-------------|-------------|----------|
| **`return_existing`** (default) | Return existing processed data without reprocessing | 200 OK | Retrieve existing data |
| **`reprocess`** | Delete existing data and reprocess the receipt | 200 OK | Update extracted data |
| **`reject`** | Reject processing with information about existing data | 409 Conflict | Prevent reprocessing |

## Database Schema

The application uses a SQLite database (`receipts.db`) with the following tables:

### `receipt_file` (ReceiptMetaData)

Stores metadata for each uploaded receipt file.

| Column | Description |
|--------|-------------|
| `id` | Unique identifier for the uploaded file |
| `file_name` | Name of the uploaded file |
| `file_path` | Storage path of the uploaded file |
| `file_hash` | SHA-256 hash of file content for duplicate detection |
| `is_valid` | Indicates if the file is a valid receipt |
| `invalid_reason` | Reason for the file being invalid (if applicable) |
| `is_processed` | Indicates if the file has been processed |
| `created_at` | Timestamp of when the receipt was first uploaded |
| `updated_at` | Timestamp of the last modification |

### `receipt`

Stores the extracted information from valid receipt files.

| Column | Description |
|--------|-------------|
| `id` | Unique identifier for the extracted receipt |
| `purchased_at` | Date and time of purchase from the receipt |
| `merchant_name` | Merchant's name as extracted from the receipt |
| `total_amount` | Total amount spent as shown on the receipt |
| `currency` | Currency code (e.g., USD, EUR) |
| `payment_method` | Payment method used (e.g., Credit Card, Cash) |
| `category` | Receipt category (e.g., Food, Transportation) |
| `receipt_file` | Foreign key to the associated receipt file |

### `line_item`

Stores individual line items from receipts.

| Column | Description |
|--------|-------------|
| `id` | Unique identifier for the line item |
| `description` | Description of the item |
| `quantity` | Quantity purchased |
| `unit_price` | Price per unit |
| `total` | Total price for this line item |
| `receipt` | Foreign key to the parent receipt |

## API Endpoints

### 1. Upload Receipt
**POST** `/upload`

Uploads a new receipt file and stores its metadata. Supports duplicate detection.

**Query Parameters:**
- `duplicate_strategy` (optional): `reject`, `update` (default: `reject`)

**Request:**
```bash
# Normal upload
curl -X POST -F "file=@/path/to/your/receipt.pdf" http://127.0.0.1:8000/upload

# Upload with duplicate update strategy
curl -X POST -F "file=@/path/to/your/receipt.pdf" "http://127.0.0.1:8000/upload?duplicate_strategy=update"
```

**Success Response (201 Created):**
```json
{
    "id": 1,
    "file_name": "receipt.pdf",
    "file_path": "uploads/file-1_receipt.pdf",
    "file_hash": "a1b2c3d4e5f6...",
    "is_valid": false,
    "invalid_reason": null,
    "is_processed": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Duplicate Detection Response (409 Conflict):**
```json
{
    "error": "Duplicate file detected",
    "duplicate_info": {
        "existing_id": 1,
        "existing_file_name": "receipt.pdf",
        "uploaded_at": "2024-01-15T10:30:00Z",
        "is_processed": true,
        "is_valid": true
    },
    "message": "Use duplicate_strategy=update to update existing receipt to create new entry"
}
```

### 2. Validate Receipt
**GET** `/validate/{receipt_id}`

Validates an uploaded file to confirm it is a valid receipt.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/validate/1
```

**Response (200 OK):**
```json
{
    "id": 1,
    "file_name": "receipt.pdf",
    "file_path": "uploads/file-1_receipt.pdf",
    "file_hash": "a1b2c3d4e5f6...",
    "is_valid": true,
    "invalid_reason": "",
    "is_processed": false,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

### 3. Process Receipt
**GET** `/process/{receipt_id}`

Extracts receipt details using AI and saves the data. Handles duplicate processing scenarios.

**Query Parameters:**
- `duplicate_strategy` (optional): `return_existing`, `reprocess`, or `reject` (default: `return_existing`)

**Request:**
```bash
# Normal processing
curl -X GET http://127.0.0.1:8000/process/1

# Reprocess existing receipt
curl -X GET "http://127.0.0.1:8000/process/1?duplicate_strategy=reprocess"
```

**Success Response (200 OK):**
```json
{
    "id": 1,
    "purchased_at": "2024-01-15T10:30:00Z",
    "merchant_name": "Walmart",
    "total_amount": "156.78",
    "currency": "USD",
    "payment_method": "Credit Card",
    "category": "Shopping",
    "receipt_file": 1,
    "created_at": "2024-01-15T10:35:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "line_items": [
        {
            "id": 1,
            "description": "Milk",
            "quantity": "2.00",
            "unit_price": "3.99",
            "total": "7.98"
        },
        {
            "id": 2,
            "description": "Bread",
            "quantity": "1.00",
            "unit_price": "2.49",
            "total": "2.49"
        }
    ]
}
```

**Already Processed Response (409 Conflict):**
```json
{
    "error": "Receipt already processed",
    "existing_data": [...],
    "message": "Use duplicate_strategy=reprocess to reprocess or duplicate_strategy=return_existing to return existing data"
}
```

### 4. List All Receipts
**GET** `/receipts`

Retrieves a list of all receipts stored in the database.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/receipts
```

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "purchased_at": "2024-01-15T10:30:00Z",
        "merchant_name": "Walmart",
        "total_amount": "156.78",
        "currency": "USD",
        "payment_method": "Credit Card",
        "category": "Shopping",
        "receipt_file": 1,
        "created_at": "2024-01-15T10:35:00Z",
        "updated_at": "2024-01-15T10:35:00Z",
        "line_items": [...]
    }
]
```

### 5. Get Receipt Details
**GET** `/receipts/{id}`

Fetches the details of a specific receipt by its ID.

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/receipts/1
```

**Response (200 OK):**
```json
{
    "id": 1,
    "purchased_at": "2024-01-15T10:30:00Z",
    "merchant_name": "Walmart",
    "total_amount": "156.78",
    "currency": "USD",
    "payment_method": "Credit Card",
    "category": "Shopping",
    "receipt_file": 1,
    "created_at": "2024-01-15T10:35:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "line_items": [...]
}
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for AI-powered extraction) - I used Gemini Key here as it is free.
- Postman (for API testing)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/auto-receipts.git
   cd auto-receipts
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_BASE_URL=your_service_provider
   LLM_MODEL=model_you_want_use
   DJANGO_SECURITY_KEY=your_django_secret_key_here
   ```
   * I used Gemini Key here as it is free. You can get one at - - > https://aistudio.google.com/
   * OPENAI_API_KEY - you can put in gemini api-key here
   * OPENAI_BASE_URL - just put in https://generativelanguage.googleapis.com/v1beta/ to use gemini with openai library
   * LLM_MODEL - I used gemini-2.5-flash

5. **Run database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://127.0.0.1:8000/`

## Using the Postman Collection

### Importing the Collection

1. **Download the collection**: The collection file is available as `Auto-Receipts API.postman_collection.json` in the project root.

2. **Import into Postman**:
   - Open Postman
   - Click "Import" button
   - Select the `Auto-Receipts API.postman_collection.json` file
   - The collection will be imported with all test scenarios

3. **Set up environment variables**:
   - The collection uses a `base_url` variable set to `http://127.0.0.1:8000` by default
   - You can modify this in the collection variables if your server runs on a different URL

### Collection Structure

The collection is organized into 4 main sections for logical testing flow:

#### **1. Upload & Duplicate Detection**
Test file upload scenarios and duplicate handling:

- **Upload Receipt - First Time**: Test successful file upload
- **Upload Receipt - Duplicate Detection (Reject)**: Test default duplicate rejection (409 Conflict)
- **Upload Receipt - Duplicate Update**: Test updating existing receipt (200 OK)
- **Upload Receipt - Invalid File Type**: Test error handling for unsupported formats (400 Bad Request)
- **Upload Receipt - No File**: Test missing file validation

#### **2. Validation**
Test receipt validation functionality:

- **Validate Receipt - Success**: Test successful validation (200 OK)
- **Validate Receipt - Not Found**: Test validation of non-existent receipts (404 Not Found)

#### **3. Processing & Duplicate Handling**
Test data extraction and duplicate processing:

- **Process Receipt - First Time**: Test initial data extraction (200 OK)
- **Process Receipt - Already Processed (Return Existing)**: Test default duplicate strategy (200 OK)
- **Process Receipt - Reprocess**: Test reprocessing existing receipts (200 OK)
- **Process Receipt - Already Processed (Reject)**: Test rejection strategy (409 Conflict)
- **Process Receipt - Not Validated**: Test processing unvalidated receipts (400 Bad Request)
- **Process Receipt - Not Found**: Test processing non-existent receipts (404 Not Found)

#### **4. Data Retrieval**
Test data retrieval functionality:

- **List All Receipts**: Test bulk data retrieval (200 OK)
- **Get Receipt Details - Success**: Test individual receipt retrieval (200 OK)
- **Get Receipt Details - Not Found**: Test retrieval of non-existent receipts (404 Not Found)

### Testing Workflow

#### **Complete End-to-End Testing**

1. **Start with Upload**:
   - Use "Upload Receipt - First Time" to upload a receipt file
   - Note the receipt ID from the response

2. **Validate the Receipt**:
   - Use "Validate Receipt - Success" with the receipt ID
   - Verify the receipt is marked as valid

3. **Process the Receipt**:
   - Use "Process Receipt - First Time" with the receipt ID
   - Verify data extraction works correctly

4. **Test Duplicate Scenarios**:
   - Upload the same file again to test duplicate detection
   - Try different duplicate strategies (update)
   - Test reprocessing with different strategies

5. **Retrieve Data**:
   - Use "List All Receipts" to see all processed receipts
   - Use "Get Receipt Details - Success" to view specific receipt

#### **Duplicate Testing Scenarios**

1. **Upload Duplicates**:
   ```bash
   # First upload (should succeed)
   POST /upload with file
   
   # Second upload with same file (should return 409 Conflict)
   POST /upload with same file
   
   # Third upload with update strategy (should return 200 OK)
   POST /upload?duplicate_strategy=update with same file
   ```

2. **Processing Duplicates**:
   ```bash
   # First processing (should succeed)
   GET /process/1
   
   # Second processing with return_existing (should return 200 OK with existing data)
   GET /process/1?duplicate_strategy=return_existing
   
   # Third processing with reprocess (should return 200 OK with new data)
   GET /process/1?duplicate_strategy=reprocess
   
   # Fourth processing with reject (should return 409 Conflict)
   GET /process/1?duplicate_strategy=reject
   ```

### Expected HTTP Status Codes

| Scenario | Expected Status | Description |
|----------|----------------|-------------|
| Successful upload | 201 Created | New receipt created |
| Duplicate upload (reject) | 409 Conflict | Duplicate detected and rejected |
| Duplicate upload (update) | 200 OK | Existing receipt updated |
| Invalid file type | 400 Bad Request | Unsupported format |
| Missing file | 400 Bad Request | No file provided |
| Successful validation | 200 OK | Receipt validated |
| Receipt not found | 404 Not Found | Receipt doesn't exist |
| Successful processing | 200 OK | Data extracted successfully |
| Already processed (return existing) | 200 OK | Existing data returned |
| Already processed (reprocess) | 200 OK | Data reprocessed |
| Already processed (reject) | 409 Conflict | Processing rejected |
| Not validated | 400 Bad Request | Receipt not validated |
| Successful retrieval | 200 OK | Data retrieved successfully |

## Dependencies

- **Django**: Web framework
- **Django REST Framework**: API framework
- **OpenAI**: AI-powered text extraction
- **PyPDFium2**: PDF processing
- **Pillow**: Image processing
- **python-dotenv**: Environment variable management

## Project Structure

```
auto-receipts/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── receipts.db              # SQLite database
├── uploads/                 # Directory for uploaded files
├── auto-receipts.postman_collection.json  # Postman collection
├── receipt_project/         # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── receipts/               # Main application
    ├── models.py           # Database models
    ├── views.py            # API views
    ├── serializers.py      # Data serializers
    ├── utils.py            # Utility functions
    ├── urls.py             # URL routing
    └── migrations/         # Database migrations
```

## Usage Examples

### Using curl

1. **Upload a receipt:**
   ```bash
   curl -X POST -F "file=@receipt.pdf" http://127.0.0.1:8000/upload
   ```

2. **Upload with duplicate handling:**
   ```bash
   # Update existing duplicate
   curl -X POST -F "file=@receipt.pdf" "http://127.0.0.1:8000/upload?duplicate_strategy=update"
   ```

3. **Validate the uploaded receipt:**
   ```bash
   curl -X GET http://127.0.0.1:8000/validate/1
   ```

4. **Process the receipt to extract data:**
   ```bash
   curl -X GET http://127.0.0.1:8000/process/1
   ```

5. **Reprocess an existing receipt:**
   ```bash
   curl -X GET "http://127.0.0.1:8000/process/1?duplicate_strategy=reprocess"
   ```

6. **List all receipts:**
   ```bash
   curl -X GET http://127.0.0.1:8000/receipts
   ```

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request**: Invalid file format, missing file, or processing errors
- **404 Not Found**: Receipt or file not found
- **409 Conflict**: Duplicate detection scenarios
- **500 Internal Server Error**: Server-side processing errors

Error responses include descriptive messages:
```json
{
    "error": "Not a Valid format - Supported Formats: ['.png', '.pdf', '.jpg', '.jpeg']"
}
```

## Duplicate Detection Features

### File Hash Generation
- Uses SHA-256 hashing for exact file content matching
- Automatically generated when files are uploaded
- Stored in database for fast duplicate detection
- Handles file content changes, not just filename changes

### Duplicate Strategies in Detail

#### **Upload Strategies**

**`reject` (Default)**
- **Purpose**: Prevent accidental duplicate uploads
- **Behavior**: Returns 409 Conflict with detailed duplicate information
- **Use Case**: Production environments where duplicates should be prevented
- **Response**: Includes existing file details and strategy options

**`update`**
- **Purpose**: Replace existing file with updated version
- **Behavior**: Updates metadata and file on disk, returns 200 OK
- **Use Case**: When you want to replace an existing receipt with a better quality version
- **Response**: Updated receipt metadata

#### **Processing Strategies**

**`return_existing` (Default)**
- **Purpose**: Retrieve existing processed data without reprocessing
- **Behavior**: Returns existing extracted data, returns 200 OK
- **Use Case**: When you want to retrieve data without re-running AI extraction
- **Response**: Existing receipt data with line items

**`reprocess`**
- **Purpose**: Delete existing data and extract fresh data
- **Behavior**: Deletes existing data, runs AI extraction again, returns 200 OK
- **Use Case**: When you want to update extracted data or fix extraction errors
- **Response**: Freshly extracted receipt data

**`reject`**
- **Purpose**: Prevent reprocessing of already processed receipts
- **Behavior**: Returns 409 Conflict with existing data information
- **Use Case**: When you want to prevent accidental reprocessing
- **Response**: Error message with existing data and strategy options

### Benefits of Duplicate Detection
- **Prevents accidental duplicate uploads**: Saves storage space and processing time
- **Provides flexible handling options**: Choose the right strategy for your use case
- **Maintains data integrity**: Ensures consistent data handling
- **Improves user experience**: Clear feedback on duplicate scenarios
- **Supports different workflows**: From strict duplicate prevention to flexible handling
