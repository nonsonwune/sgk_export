# SGK Export System Deployment Guide

## Quick Deployment with Render.com

For a fast and straightforward cloud deployment, Render.com is recommended:

1. **Sign up at [Render.com](https://render.com)** and connect your GitHub repository

2. **Create a new Web Service**
   - Link to your GitHub repository
   - Select the `local-file-storage` branch
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn wsgi:app`

3. **Configure environment variables**
   ```
   FLASK_APP=app.py
   FLASK_ENV=production
   SECRET_KEY=<generate-random-key>
   DATABASE_URL=<your-render-postgres-url>
   USE_NAS_STORAGE=false
   UPLOAD_FOLDER=/var/data/files
   ```

4. **Add PostgreSQL database**
   - Create a PostgreSQL database from Render dashboard
   - The DATABASE_URL will be automatically added to your environment

5. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Your app will be available at `https://your-app-name.onrender.com`

## Basic Troubleshooting

- **Application not starting**: Check build logs in Render dashboard
- **Database connection issues**: Verify environment variables are set correctly
- **File upload problems**: Ensure UPLOAD_FOLDER environment variable points to a writable directory

For more complex deployments and office setups, see the detailed guide in the project repository.

## Documentation References

- [Render Python Deployment Docs](https://render.com/docs/deploy-flask)
- [Flask Deployment Best Practices](https://flask.palletsprojects.com/en/2.0.x/deploying/) 