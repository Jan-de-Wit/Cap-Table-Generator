# Vercel Deployment Guide

## Security Configuration

### Internal API Secret

To protect the Python serverless function from unauthorized access, set the `INTERNAL_API_SECRET` environment variable in Vercel:

1. Go to your Vercel project settings
2. Navigate to "Environment Variables"
3. Add a new variable:
   - **Name**: `INTERNAL_API_SECRET`
   - **Value**: A strong random string (e.g., generate with `openssl rand -hex 32`)
   - **Environment**: Production, Preview, and Development (if needed)

This secret ensures that only your Next.js application can call the Python serverless function. Without this secret, the Python function will reject all requests.

### How It Works

- The Next.js API route (`/api/generate-excel`) includes the secret in the `X-Internal-Secret` header when calling the Python function
- The Python serverless function (`/api/generate-excel-python`) validates this secret before processing requests
- If the secret is not set, the Python function will still work (for development), but it's recommended to set it in production

## Deployment Checklist

- [ ] Set `INTERNAL_API_SECRET` environment variable in Vercel
- [ ] Verify `requirements.txt` contains all necessary Python dependencies
- [ ] Ensure `vercel.json` is configured correctly
- [ ] Test the deployment to ensure Python dependencies are installed
- [ ] Verify the `/api/generate-excel` endpoint works correctly

## Troubleshooting

### Python dependencies not installing
- Ensure `requirements.txt` is at the project root
- Check Vercel build logs for Python installation errors

### 403 Forbidden errors
- Verify `INTERNAL_API_SECRET` is set in Vercel environment variables
- Check that the secret matches between Next.js and Python functions

### Import errors in Python function
- Ensure `src/` directory is included in the deployment
- Check that all required Python packages are in `requirements.txt`

