# Job Candidate API

This API endpoint allows external systems to create Job Candidate entries in ERPNext.

## Endpoint

**POST** `/api/method/corporate_services.api.candidates.v1.create_job_candidate`

## Authentication

Use API Key/Secret authentication:

```
Authorization: token <api_key>:<api_secret>
```

To generate API credentials in ERPNext:
1. Go to User settings
2. Generate API Key and API Secret

## Request Format

Content-Type: `multipart/form-data`

### Required Fields

- `names` (text): Full name of the candidate
- `email_address` (text): Valid email address
- `cv` (file): Resume/CV file

### Optional Fields

- `phone` (text): Contact phone number
- `role` (text): Role/position name the candidate is applying for
- `role_description` (text): Description of the role
- `cover_letter` (file): Cover letter document
- `minimum_requirements` (JSON string): Array of minimum requirements
- `preferred_attributes` (JSON string): Array of preferred attributes

### Child Table Format

**Minimum Requirements:**
```json
[
  {
    "requirement": "Bachelor's degree in Computer Science"
  },
  {
    "requirement": "5+ years of experience in Python"
  }
]
```

**Preferred Attributes:**
```json
[
  {
    "attribute": "Experience with ERPNext"
  },
  {
    "attribute": "Strong communication skills"
  }
]
```

## Example Usage

### Using cURL

```bash
curl -X POST \
  https://your-erpnext-site.com/api/method/corporate_services.api.candidates.v1.create_job_candidate \
  -H "Authorization: token your_api_key:your_api_secret" \
  -F "names=John Doe" \
  -F "email_address=john.doe@example.com" \
  -F "phone=+1234567890" \
  -F "role=Senior Software Engineer" \
  -F "role_description=Full-stack developer position for enterprise applications" \
  -F "cv=@/path/to/resume.pdf" \
  -F "cover_letter=@/path/to/cover_letter.pdf" \
  -F 'minimum_requirements=[{"requirement":"Bachelor degree"},{"requirement":"5 years experience"}]' \
  -F 'preferred_attributes=[{"attribute":"Team player"},{"attribute":"Problem solver"}]'
```

### Using Python

```python
import requests

url = "https://your-erpnext-site.com/api/method/corporate_services.api.candidates.v1.create_job_candidate"
api_key = "your_api_key"
api_secret = "your_api_secret"

headers = {
    "Authorization": f"token {api_key}:{api_secret}"
}

files = {
    "cv": open("resume.pdf", "rb"),
    "cover_letter": open("cover_letter.pdf", "rb")
}

data = {
    "names": "John Doe",
    "email_address": "john.doe@example.com",
    "phone": "+1234567890",
    "role": "Senior Software Engineer",
    "role_description": "Full-stack developer position for enterprise applications",
    "minimum_requirements": '[{"requirement":"Bachelor degree"},{"requirement":"5 years experience"}]',
    "preferred_attributes": '[{"attribute":"Team player"}]'
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())
```

### Using JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('names', 'John Doe');
form.append('email_address', 'john.doe@example.com');
form.append('phone', '+1234567890');
form.append('role', 'Senior Software Engineer');
form.append('role_description', 'Full-stack developer position for enterprise applications');
form.append('cv', fs.createReadStream('resume.pdf'));
form.append('cover_letter', fs.createReadStream('cover_letter.pdf'));
form.append('minimum_requirements', JSON.stringify([
  {"requirement": "Bachelor degree"},
  {"requirement": "5 years experience"}
]));
form.append('preferred_attributes', JSON.stringify([
  {"attribute": "Team player"}
]));

axios.post(
  'https://your-erpnext-site.com/api/method/corporate_services.api.candidates.v1.create_job_candidate',
  form,
  {
    headers: {
      ...form.getHeaders(),
      'Authorization': 'token your_api_key:your_api_secret'
    }
  }
)
.then(response => console.log(response.data))
.catch(error => console.error(error.response.data));
```

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    "name": "JOB-CAND-00001",
    "names": "John Doe",
    "email_address": "john.doe@example.com",
    "phone": "+1234567890",
    "role": "Senior Software Engineer",
    "role_description": "Full-stack developer position for enterprise applications",
    "cv": "/files/resume.pdf",
    "cover_letter": "/files/cover_letter.pdf"
  }
}
```

### Error Response

```json
{
  "success": false,
  "errors": {
    "names": "Candidate name is required",
    "email_address": "Invalid email address format",
    "cv": "Resume/CV file is required"
  }
}
```

## Error Codes

- **Validation Errors**: Missing or invalid field values
- **Duplicate Entry**: Candidate with same email already exists
- **General Errors**: Server errors, permission issues, etc.

