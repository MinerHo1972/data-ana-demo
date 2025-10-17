# Data Model: 商品破损照片智能比对系统

**Date**: 2025-10-14
**Database**: PostgreSQL RDS
**ORM**: SQLAlchemy (Python)

## Entity Relationship Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Users       │    │   Complaints    │    │     Photos      │
│                 │    │                 │    │                 │
│ id (PK)         │◄──►│ id (PK)         │◄──►│ id (PK)         │
│ email           │    │ user_id (FK)     │    │ complaint_id(FK)│
│ name            │    │ customer_info   │    │ s3_key          │
│ role            │    │ product_info    │    │ metadata        │
│ created_at      │    │ status          │    │ created_at      │
│ updated_at      │    │ created_at      │    │ updated_at      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐    ┌────────▼────────┐
         │              │ PhotoComparisons│    │ PhotoVectors    │
         │              │                 │    │                 │
         │              │ id (PK)         │    │ id (PK)         │
         │              │ uploaded_photo │    │ photo_id (FK)   │
         │              │ historical_photo│    │ vector_data     │
         │              │ similarity_score│    │ algorithm       │
         │              │ comparison_time │    │ created_at      │
         │              │ status          │    └─────────────────┘
         │              └─────────────────┘
         │                       │
         │              ┌────────▼────────┐
         │              │SuspiciousClaims │
         │              │                 │
         │              │ id (PK)         │
         │              │ complaint_id(FK)│
         │              │ evidence        │
         │              │ risk_score      │
         │              │ status          │
         │              │ created_at      │
         │              └─────────────────┘
```

## Table Definitions

### 1. Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('customer_service_agent', 'admin', 'system')),
    phone VARCHAR(20),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Fields Description**:
- `id`: Unique user identifier
- `email`: User email address (unique)
- `name`: Full name
- `role`: User role (customer_service_agent, admin, system)
- `phone`: Contact phone number
- `department`: Department for organizational tracking
- `is_active`: Account status
- `last_login`: Last successful login timestamp

### 2. Complaints Table

```sql
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    complaint_number VARCHAR(50) UNIQUE NOT NULL,
    customer_info JSONB NOT NULL,
    product_info JSONB NOT NULL,
    damage_description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'resolved', 'rejected', 'suspicious')),
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'urgent')),
    assigned_agent_id UUID REFERENCES users(id),
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_complaints_user_id ON complaints(user_id);
CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
CREATE INDEX idx_complaints_number ON complaints(complaint_number);
```

**Fields Description**:
- `id`: Unique complaint identifier
- `user_id`: User who created the complaint
- `complaint_number`: Business identifier (e.g., "COMP-2025-001234")
- `customer_info`: JSON with customer details (name, contact, order info)
- `product_info`: JSON with product details (SKU, name, purchase date)
- `damage_description`: Text description of damage
- `status`: Current complaint status
- `priority`: Priority level for processing
- `assigned_agent_id`: Customer service agent assigned
- `resolution_notes`: Notes about resolution

**customer_info JSON Schema**:
```json
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "order_id": "string",
  "order_date": "YYYY-MM-DD",
  "shipping_address": {
    "street": "string",
    "city": "string",
    "state": "string",
    "zip": "string",
    "country": "string"
  }
}
```

**product_info JSON Schema**:
```json
{
  "sku": "string",
  "name": "string",
  "category": "string",
  "price": "number",
  "purchase_date": "YYYY-MM-DD",
  "serial_number": "string"
}
```

### 3. Photos Table

```sql
CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    s3_key VARCHAR(500) NOT NULL UNIQUE,
    s3_bucket VARCHAR(100) NOT NULL DEFAULT 'damage-photos',
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    width INTEGER,
    height INTEGER,
    metadata JSONB,
    processing_status VARCHAR(50) DEFAULT 'uploaded' CHECK (processing_status IN ('uploaded', 'processing', 'processed', 'failed')),
    upload_source VARCHAR(50) DEFAULT 'manual' CHECK (upload_source IN ('manual', 'api', 'webhook')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_photos_complaint_id ON photos(complaint_id);
CREATE INDEX idx_photos_s3_key ON photos(s3_key);
CREATE INDEX idx_photos_processing_status ON photos(processing_status);
CREATE INDEX idx_photos_created_at ON photos(created_at);
```

**Fields Description**:
- `id`: Unique photo identifier
- `complaint_id`: Associated complaint
- `s3_key`: S3 object key
- `s3_bucket`: S3 bucket name
- `original_filename`: Original filename from upload
- `file_size`: File size in bytes
- `mime_type`: MIME type (image/jpeg, image/png, etc.)
- `width`, `height`: Image dimensions
- `metadata`: Additional metadata (EXIF data, upload info)
- `processing_status`: Current processing status
- `upload_source`: How photo was uploaded

**metadata JSON Schema**:
```json
{
  "upload_source": "string",
  "user_agent": "string",
  "ip_address": "string",
  "exif_data": {
    "camera_make": "string",
    "camera_model": "string",
    "taken_at": "YYYY-MM-DDTHH:MM:SSZ",
    "gps_coordinates": {
      "latitude": "number",
      "longitude": "number"
    }
  },
  "processing_info": {
    "format": "string",
    "quality_score": "number",
    "blur_detected": "boolean",
    "brightness": "number"
  }
}
```

### 4. PhotoVectors Table

```sql
CREATE TABLE photo_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    photo_id UUID NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    vector_data VECTOR(1536) NOT NULL, -- Assuming OpenAI CLIP-like embedding size
    algorithm VARCHAR(100) NOT NULL DEFAULT 'aws-rekognition',
    model_version VARCHAR(50) NOT NULL,
    embedding_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(photo_id, algorithm, model_version)
);

CREATE INDEX idx_photo_vectors_photo_id ON photo_vectors(photo_id);
CREATE INDEX idx_photo_vectors_algorithm ON photo_vectors(algorithm);
```

**Fields Description**:
- `id`: Unique vector identifier
- `photo_id`: Associated photo
- `vector_data`: Vector embedding data (1536 dimensions)
- `algorithm`: Algorithm used to generate vector
- `model_version`: Version of the model used
- `embedding_created_at`: When the vector was generated

### 5. PhotoComparisons Table

```sql
CREATE TABLE photo_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_photo_id UUID NOT NULL REFERENCES photos(id),
    historical_photo_id UUID NOT NULL REFERENCES photos(id),
    similarity_score DECIMAL(5,2) NOT NULL CHECK (similarity_score >= 0 AND similarity_score <= 100),
    comparison_threshold DECIMAL(5,2) NOT NULL DEFAULT 90.00,
    algorithm VARCHAR(100) NOT NULL DEFAULT 'aws-rekognition',
    comparison_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processing_duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'completed' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uc_photo_comparison UNIQUE (uploaded_photo_id, historical_photo_id, algorithm)
);

CREATE INDEX idx_photo_comparisons_uploaded ON photo_comparisons(uploaded_photo_id);
CREATE INDEX idx_photo_comparisons_historical ON photo_comparisons(historical_photo_id);
CREATE INDEX idx_photo_comparisons_score ON photo_comparisons(similarity_score DESC);
CREATE INDEX idx_photo_comparisons_status ON photo_comparisons(status);
CREATE INDEX idx_photo_comparisons_time ON photo_comparisons(comparison_time DESC);
```

**Fields Description**:
- `id`: Unique comparison identifier
- `uploaded_photo_id`: The newly uploaded photo
- `historical_photo_id`: The historical photo being compared
- `similarity_score`: Similarity percentage (0-100)
- `comparison_threshold`: Threshold used for this comparison
- `algorithm`: Algorithm used for comparison
- `comparison_time`: When comparison was performed
- `processing_duration_ms`: Time taken in milliseconds
- `status`: Current comparison status
- `error_message`: Error details if failed
- `metadata`: Additional comparison details

**metadata JSON Schema**:
```json
{
  "comparison_method": "string",
  "feature_matches": [
    {
      "feature_type": "string",
      "confidence": "number",
      "location": {"x": "number", "y": "number"}
    }
  ],
  "visual_differences": [
    {
      "type": "string",
      "severity": "number",
      "description": "string"
    }
  ],
  "performance_metrics": {
    "preprocessing_time_ms": "number",
    "feature_extraction_time_ms": "number",
    "comparison_time_ms": "number"
  }
}
```

### 6. SuspiciousClaims Table

```sql
CREATE TABLE suspicious_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    risk_score DECIMAL(5,2) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    evidence JSONB NOT NULL,
    pattern_analysis JSONB,
    status VARCHAR(50) DEFAULT 'under_review' CHECK (status IN ('under_review', 'confirmed_suspicious', 'cleared', 'escalated')),
    reviewed_by UUID REFERENCES users(id),
    review_notes TEXT,
    auto_flagged BOOLEAN DEFAULT true,
    manual_review_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_suspicious_complaints_complaint_id ON suspicious_claims(complaint_id);
CREATE INDEX idx_suspicious_complaints_risk_score ON suspicious_claims(risk_score DESC);
CREATE INDEX idx_suspicious_complaints_status ON suspicious_claims(status);
CREATE INDEX idx_suspicious_complaints_created_at ON suspicious_claims(created_at DESC);
```

**Fields Description**:
- `id`: Unique suspicious claim identifier
- `complaint_id`: Associated complaint
- `risk_score`: Calculated risk score (0-100)
- `risk_level`: Categorized risk level
- `evidence`: Evidence supporting suspicion
- `pattern_analysis`: Analysis of suspicious patterns
- `status`: Current review status
- `reviewed_by`: User who reviewed the claim
- `review_notes`: Notes from manual review
- `auto_flagged`: Whether automatically flagged by system
- `manual_review_required`: Whether manual review is needed

**evidence JSON Schema**:
```json
{
  "similar_photos": [
    {
      "photo_id": "string",
      "similarity_score": "number",
      "historical_complaint_id": "string",
      "historical_date": "YYYY-MM-DD"
    }
  ],
  "repetition_patterns": {
    "same_photo_count": "number",
    "similar_photo_count": "number",
    "timeframe_days": "number"
  },
  "behavioral_indicators": [
    {
      "type": "string",
      "description": "string",
      "confidence": "number"
    }
  ]
}
```

**pattern_analysis JSON Schema**:
```json
{
  "customer_history": {
    "previous_claims": "number",
    "suspicious_claims": "number",
    "claim_frequency": "number"
  },
  "photo_patterns": {
    "repeated_photos": "number",
    "similar_damage_types": "string[]",
    "consistency_score": "number"
  },
  "temporal_patterns": {
    "claim_frequency_trend": "string",
    "seasonal_patterns": "string[]",
    "time_of_day_patterns": "string[]"
  }
}
```

### 7. Configuration Table

```sql
CREATE TABLE configuration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_configuration_key ON configuration(key);
CREATE INDEX idx_configuration_category ON configuration(category);
```

**Configuration Examples**:
```json
{
  "key": "similarity_threshold_default",
  "value": 90.0,
  "description": "Default similarity threshold for photo comparisons",
  "category": "comparison"
}

{
  "key": "risk_score_weights",
  "value": {
    "photo_similarity": 0.4,
    "repetition_pattern": 0.3,
    "customer_history": 0.2,
    "temporal_pattern": 0.1
  },
  "description": "Weights for calculating suspicious claim risk scores",
  "category": "risk_assessment"
}
```

### 8. AuditLog Table

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
```

## Data Validation Rules

### Photo Validation
- File size: Maximum 50MB per photo
- Supported formats: JPEG, PNG, WebP
- Minimum resolution: 200x200 pixels
- Maximum resolution: 10000x10000 pixels

### Similarity Score Validation
- Range: 0-100%
- Precision: 2 decimal places
- Default threshold: 90%

### Risk Score Validation
- Range: 0-100%
- Risk levels: Low (0-30), Medium (31-60), High (61-80), Critical (81-100)

## Data Retention Policies

### Photos
- Active complaints: Keep indefinitely
- Resolved complaints: Keep for 7 years
- Failed uploads: Delete after 30 days

### Comparison Results
- Keep for 3 years for analysis and training

### Audit Logs
- Keep for 5 years for compliance

## Performance Considerations

### Indexing Strategy
- Primary indexes on all foreign keys
- Composite indexes on frequently queried combinations
- Time-based indexes for reporting queries

### Partitioning
- Consider partitioning large tables by date (audit_log, photo_comparisons)
- Partition by status for complaint management

### Caching
- Cache frequently accessed configuration
- Cache user session data
- Cache recent comparison results

## Security Considerations

### Data Encryption
- Encrypt sensitive data at rest
- Use TLS for all data in transit
- Encrypt PII in database columns

### Access Control
- Row-level security for user data
- Column-level security for sensitive fields
- Audit all data access

### Data Privacy
- Anonymize customer data for analysis
- Implement data retention policies
- Provide data deletion capabilities