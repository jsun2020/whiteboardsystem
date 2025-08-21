# Deployment Guide

This guide covers deploying the Meeting Whiteboard Scribe application to Cloudflare Pages/Workers and Vercel.

## Prerequisites

1. **API Keys**: Obtain your Doubao API key from ByteDance
2. **Database**: Set up a PostgreSQL database (recommended) or use SQLite for testing
3. **Domain**: Have a domain name ready (optional but recommended)

## Environment Variables

Set the following environment variables in your deployment platform:

```env
# Required
DOUBAO_API_KEY=your_doubao_api_key_here
SECRET_KEY=your_secret_key_here

# Optional - API Configuration
DOUBAO_ENDPOINT=https://ark.cn-beijing.volces.com/api/v3
DOUBAO_MODEL_ID=doubao-seed-1-6-flash-250715

# Database
DATABASE_URL=postgresql://user:password@host:port/database
# or for SQLite (not recommended for production)
DATABASE_URL=sqlite:///whiteboard_scribe.db

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT=100 per hour

# Storage (optional)
STORAGE_TYPE=local
# For AWS S3:
# STORAGE_TYPE=s3
# S3_BUCKET=your-bucket-name
# S3_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Vercel Deployment

### 1. Prepare for Deployment

1. Install Vercel CLI:
   ```bash
   npm install -g vercel
   ```

2. Login to Vercel:
   ```bash
   vercel login
   ```

### 2. Configure Environment Variables

Create environment variables in Vercel dashboard or use CLI:

```bash
vercel env add DOUBAO_API_KEY
vercel env add SECRET_KEY
vercel env add DATABASE_URL
# ... add other environment variables
```

### 3. Deploy

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### 4. Database Setup

After deployment, initialize the database:

```bash
# If using PostgreSQL, run migrations
python -c "from app import create_app, db; app = create_app('production'); app.app_context().push(); db.create_all()"
```

### 5. Create Admin User

Create your first admin user:

```python
from app import create_app, db
from models.user import User

app = create_app('production')
with app.app_context():
    admin = User()
    admin.email = 'your-admin-email@example.com'
    admin.username = 'admin'
    admin.display_name = 'Administrator'
    admin.set_password('your-secure-password')
    admin.is_admin = True
    admin.is_active = True
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {admin.email}")
```

## Cloudflare Deployment

### 1. Setup Cloudflare Account

1. Create a Cloudflare account
2. Install Wrangler CLI:
   ```bash
   npm install -g wrangler
   ```

3. Login to Cloudflare:
   ```bash
   wrangler login
   ```

### 2. Configure Resources

1. **Create D1 Database**:
   ```bash
   wrangler d1 create whiteboard-db
   ```
   Update the `database_id` in `wrangler.toml` with the returned ID.

2. **Create R2 Bucket** (for file uploads):
   ```bash
   wrangler r2 bucket create whiteboard-uploads
   ```

3. **Create KV Namespaces**:
   ```bash
   wrangler kv:namespace create "SESSIONS"
   wrangler kv:namespace create "CACHE"
   ```
   Update the namespace IDs in `wrangler.toml`.

### 3. Set Environment Variables

```bash
wrangler secret put DOUBAO_API_KEY
wrangler secret put SECRET_KEY
wrangler secret put DATABASE_URL
```

### 4. Deploy

```bash
# Deploy to development
wrangler publish

# Deploy to production
wrangler publish --env production
```

### 5. Database Migration

```bash
# Run database migrations
wrangler d1 execute whiteboard-db --file=./migrations/init.sql
```

## Post-Deployment Steps

### 1. Test the Application

1. Visit your deployed URL
2. Test user registration
3. Test image upload and processing
4. Verify payment system
5. Test admin panel access

### 2. Configure Payment QR Code

1. Replace `/static/assets/images/payment-qr.png` with your actual payment QR code
2. Update contact information in the payment modal

### 3. Custom Domain (Optional)

For Vercel:
```bash
vercel domains add yourdomain.com
```

For Cloudflare:
Add custom routes in `wrangler.toml` and configure DNS.

### 4. Monitoring and Logging

- Set up error tracking (Sentry, etc.)
- Monitor performance metrics
- Set up health checks

## Usage Limits and Scaling

### Free Tier Limits

**Vercel:**
- 100GB bandwidth/month
- 100 serverless function invocations/day on hobby plan
- 10-second execution time limit

**Cloudflare:**
- 100,000 requests/day on free tier
- 128MB memory limit
- 30-second execution time

### Scaling Considerations

1. **Database**: Use connection pooling for high traffic
2. **File Storage**: Consider CDN for static assets
3. **Caching**: Implement Redis for session and data caching
4. **Rate Limiting**: Implement proper rate limiting to prevent abuse

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **Database Connection**: Verify `DATABASE_URL` is correct
3. **File Uploads**: Check file size limits and storage configuration
4. **API Limits**: Monitor Doubao API usage and quotas

### Debug Mode

For development deployments, you can enable debug mode:

```env
FLASK_ENV=development
FLASK_DEBUG=true
```

**Note**: Never enable debug mode in production!

## Security Checklist

- [ ] Use HTTPS only
- [ ] Set strong `SECRET_KEY`
- [ ] Configure proper CORS origins
- [ ] Implement rate limiting
- [ ] Regularly update dependencies
- [ ] Monitor for security vulnerabilities
- [ ] Use environment variables for sensitive data
- [ ] Enable database connection SSL
- [ ] Implement proper error handling (don't expose stack traces)

## Maintenance

### Regular Tasks

1. **Database Backups**: Set up regular database backups
2. **Dependency Updates**: Keep dependencies up to date
3. **Security Patches**: Apply security updates promptly
4. **Performance Monitoring**: Monitor response times and error rates
5. **User Management**: Regular cleanup of inactive users

### Monitoring Endpoints

- Health check: `GET /health`
- API status: `GET /api/auth/profile` (with valid token)

## Cost Estimation

### Vercel Pro Plan (~$20/month)
- Unlimited bandwidth
- Advanced analytics
- Custom domains

### Cloudflare Workers Paid (~$5/month)
- 10M requests/month
- Additional features

### Database Hosting
- PostgreSQL on platforms like Railway, Supabase, or AWS RDS
- Estimated $5-15/month depending on usage

### Total Estimated Cost: $30-40/month for production use

---

For additional help, please check the GitHub repository or contact support.