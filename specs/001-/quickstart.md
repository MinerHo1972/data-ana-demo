# Quick Start Guide: 商品破损照片智能比对系统

**Date**: 2025-10-14
**Version**: 1.0.0
**Target Audience**: Developers and System Administrators

## Overview

This guide provides step-by-step instructions for setting up and deploying the 商品破损照片智能比对系统 (Product Damage Photo Comparison System).

## Prerequisites

### System Requirements
- **AWS Account**: Active AWS account with appropriate permissions
- **Node.js**: Version 18+
- **Python**: Version 3.9+
- **Docker**: Latest version
- **Git**: Latest version

### AWS Services Required
- AWS S3 (Simple Storage Service)
- AWS RDS PostgreSQL
- AWS Lambda
- AWS API Gateway
- AWS Cognito
- AWS Rekognition
- Pinecone Vector Database
- AWS SQS
- AWS SNS
- AWS SES

### IAM Permissions
Ensure your AWS account has permissions for:
- Creating and managing S3 buckets
- Creating and managing RDS instances
- Creating Lambda functions
- Creating API Gateway resources
- Managing Cognito user pools
- Using AWS Rekognition
- Creating SQS queues
- Publishing to SNS topics
- Sending emails via SES

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   AWS Lambda    │    │   AWS           │
│   Application   │◄──►│   Functions     │◄──►│   Rekognition   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐    ┌────────▼────────┐
         │              │   PostgreSQL    │    │   Pinecone      │
         │              │   RDS           │    │   Vector DB     │
         │              └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐    ┌────────▼────────┐
         │              │   AWS S3        │    │   AWS SNS/SES   │
         │              │   Storage       │    │   Notifications │
         │              └─────────────────┘    └─────────────────┘
```

## Setup Instructions

### 1. Clone Repository

```bash
git clone https://github.com/your-org/product-damage-comparison.git
cd product-damage-comparison
```

### 2. AWS Infrastructure Setup

#### 2.1 Create S3 Bucket

```bash
# Create S3 bucket for photo storage
aws s3 mb s3://your-damage-photos-bucket --region us-east-1

# Configure bucket policies and encryption
aws s3api put-bucket-encryption \
    --bucket your-damage-photos-bucket \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'
```

#### 2.2 Set up PostgreSQL RDS

```bash
# Create RDS subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name damage-comparison-subnet-group \
    --db-subnet-group-description "Subnet group for damage comparison system" \
    --subnet-ids subnet-12345678 subnet-87654321

# Create RDS instance
aws rds create-db-instance \
    --db-instance-identifier damage-comparison-db \
    --db-instance-class db.t3.medium \
    --engine postgres \
    --engine-version 14.9 \
    --master-username admin \
    --master-user-password your-secure-password \
    --allocated-storage 100 \
    --db-name damage_comparison \
    --vpc-security-group-ids sg-12345678 \
    --db-subnet-group-name damage-comparison-subnet-group \
    --backup-retention-period 7 \
    --multi-az \
    --storage-type gp2 \
    --publicly-accessible false
```

#### 2.3 Set up Cognito User Pool

```bash
# Create user pool
aws cognito-idp create-user-pool \
    --pool-name damage-comparison-users \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": true,
            "RequireLowercase": true,
            "RequireNumbers": true,
            "RequireSymbols": false
        }
    }' \
    --auto-verified-attributes email \
    --username-attributes email \
    --schema '[
        {
            "Name": "name",
            "AttributeDataType": "String",
            "Required": true,
            "Mutable": true
        }
    ]'

# Note the User Pool ID from the response
```

#### 2.4 Create Pinecone Index

```python
# Create a Python script to set up Pinecone
import pinecone

pinecone.init(api_key="your-pinecone-api-key", environment="us-west1-gcp")

# Create index for photo vectors
pinecone.create_index(
    name="damage-photos",
    dimension=1536,  # Adjust based on your embedding model
    metric="cosine",
    pod_type="p1.x1"
)
```

### 3. Application Setup

#### 3.1 Environment Configuration

Create `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://admin:your-secure-password@damage-comparison-db.abcdefg123456.us-east-1.rds.amazonaws.com:5432/damage_comparison

# AWS Configuration
AWS_REGION=us-east-1
S3_BUCKET=your-damage-photos-bucket

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_INDEX=damage-photos

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Cognito Configuration
COGNITO_USER_POOL_ID=us-east-1_123456789
COGNITO_CLIENT_ID=your-client-id

# API Configuration
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["https://your-frontend-domain.com"]

# Notification Configuration
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:damage-comparison-notifications
SES_FROM_EMAIL=noreply@yourdomain.com
```

#### 3.2 Database Migration

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create initial user
python scripts/create_admin_user.py
```

#### 3.3 Local Development Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI application locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the processing service
python services/photo_processor.py

# Start the notification service
python services/notification_service.py
```

### 4. Deployment

#### 4.1 Docker Deployment

```bash
# Build Docker image
docker build -t damage-comparison-api .

# Run with Docker Compose
docker-compose up -d
```

#### 4.2 AWS Lambda Deployment

```bash
# Package Lambda functions
cd functions/
./deploy.sh

# Deploy API Gateway
cd ../infrastructure/
terraform apply
```

### 5. Testing

#### 5.1 API Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "your-password"}'

# Test photo upload (with auth token)
curl -X POST http://localhost:8000/api/v1/complaints/{complaint_id}/photos \
  -H "Authorization: Bearer your-jwt-token" \
  -F "photo=@test-photo.jpg" \
  -F "description=Test damage photo"
```

#### 5.2 Integration Testing

```bash
# Run integration tests
pytest tests/integration/

# Load testing
python tests/load_test.py
```

## Configuration

### System Configuration

Key system parameters can be configured via API or environment variables:

```python
# Similarity threshold
SIMILARITY_THRESHOLD_DEFAULT = 90.0

# Risk scoring weights
RISK_SCORE_WEIGHTS = {
    "photo_similarity": 0.4,
    "repetition_pattern": 0.3,
    "customer_history": 0.2,
    "temporal_pattern": 0.1
}

# Processing limits
MAX_PHOTO_SIZE_MB = 50
SUPPORTED_PHOTO_FORMATS = ["JPEG", "PNG", "WebP"]
MAX_CONCURRENT_ANALYSES = 50
```

### Monitoring and Logging

Enable comprehensive monitoring:

```bash
# AWS CloudWatch metrics
aws logs create-log-group --log-group-name /aws/lambda/damage-comparison

# Set up alarms
aws cloudwatch put-metric-alarm \
    --alarm-name "HighErrorRate" \
    --alarm-description "Error rate too high" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check RDS instance status
   aws rds describe-db-instances --db-instance-identifier damage-comparison-db

   # Check security group rules
   aws ec2 describe-security-groups --group-ids sg-12345678
   ```

2. **Photo Upload Failures**
   ```bash
   # Check S3 bucket permissions
   aws s3api get-bucket-policy --bucket your-damage-photos-bucket

   # Check Lambda logs
   aws logs tail /aws/lambda/photo-processor --follow
   ```

3. **Similarity Search Issues**
   ```bash
   # Check Pinecone index status
   python -c "import pinecone; pinecone.init(); print(pinecone.describe_index('damage-photos'))"
   ```

### Performance Tuning

1. **Database Optimization**
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX CONCURRENTLY idx_complaints_status_created ON complaints(status, created_at);
   CREATE INDEX CONCURRENTLY idx_photo_comparisons_score ON photo_comparisons(similarity_score DESC);
   ```

2. **Caching**
   ```python
   # Redis caching for frequently accessed data
   CACHE_CONFIG = {
       'host': 'your-redis-cluster',
       'port': 6379,
       'db': 0,
       'ttl': 3600  # 1 hour
   }
   ```

## Security Considerations

### Data Protection
- All data encrypted at rest and in transit
- PII data masked in logs
- Regular security audits
- Compliance with GDPR/CCPA

### Access Control
- Role-based access control (RBAC)
- API rate limiting
- IP whitelisting for admin access
- Multi-factor authentication for admin accounts

### Network Security
- VPC with private subnets
- Security groups restricting access
- AWS WAF for API protection
- DDoS protection with AWS Shield

## Maintenance

### Regular Tasks

1. **Database Maintenance**
   ```bash
   # Weekly vacuum and analyze
   psql -h your-db-host -U admin -d damage_comparison -c "VACUUM ANALYZE;"
   ```

2. **Log Cleanup**
   ```bash
   # Clean up old logs
   aws logs delete-log-group --log-group-name /aws/lambda/old-function
   ```

3. **Performance Monitoring**
   ```bash
   # Check key metrics
   aws cloudwatch get-metric-statistics \
       --namespace AWS/Lambda \
       --metric-name Duration \
       --dimensions Name=FunctionName,Value=photo-processor \
       --statistics Average \
       --period 3600 \
       --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
       --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ)
   ```

## Support

### Documentation
- [API Documentation](./contracts/api.yaml)
- [Data Model Documentation](./data-model.md)
- [Research Findings](./research.md)

### Getting Help
- Create GitHub issues for bugs
- Contact support team for urgent issues
- Check AWS service health for infrastructure issues

## Next Steps

1. Review the [data model](./data-model.md) to understand the database structure
2. Examine the [API contracts](./contracts/api.yaml) for integration details
3. Review the [research findings](./research.md) for technology decisions
4. Set up monitoring and alerting
5. Plan your scaling strategy based on expected usage patterns