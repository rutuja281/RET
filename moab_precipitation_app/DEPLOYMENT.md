# Deployment Guide - Free Hosting Options

This application can be deployed to several free hosting services. Here are the recommended options:

## Option 1: Render (Recommended - Easiest)

1. **Create a Render account**: Go to https://render.com and sign up (free)

2. **Create a new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository (or use manual deploy)

3. **Configure the service**:
   - **Name**: precipitation-analysis (or your choice)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free

4. **Environment Variables** (optional):
   - `PORT`: Automatically set by Render
   - `SECRET_KEY`: Generate one for production
   - `DATABASE_URL`: Render provides PostgreSQL, or use SQLite for free tier

5. **Deploy**: Click "Create Web Service"

Your app will be available at: `https://your-app-name.onrender.com`

---

## Option 2: Railway

1. **Create Railway account**: Go to https://railway.app and sign up

2. **New Project** → "Deploy from GitHub repo"

3. **Settings**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

4. Railway automatically detects Python and deploys

---

## Option 3: PythonAnywhere

1. **Sign up**: https://www.pythonanywhere.com (free tier available)

2. **Upload files** via Files tab

3. **Create Web App**:
   - Go to Web tab
   - Click "Add a new web app"
   - Choose Flask
   - Select Python 3.10 or 3.11

4. **Configure**:
   - Source code: `/home/yourusername/moab_precipitation_app`
   - WSGI file: Edit to point to `app:app`

5. **Run setup commands** in Bash console:
   ```bash
   cd ~/moab_precipitation_app
   pip3.10 install --user -r requirements.txt
   python3.10 database.py
   ```

---

## Option 4: Fly.io

1. **Install Fly CLI**: https://fly.io/docs/getting-started/installing-flyctl/

2. **Create fly.toml** (included in this repo):
   ```toml
   app = "precipitation-analysis"
   primary_region = "iad"

   [build]

   [http_service]
     internal_port = 5000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]

   [[vm]]
     cpu_kind = "shared"
     cpus = 1
     memory_mb = 256
   ```

3. **Deploy**:
   ```bash
   fly launch
   fly deploy
   ```

---

## Important Notes for Production

### Database
- **SQLite** works for free tiers but has limitations
- **PostgreSQL** is recommended for production (available on Render free tier)
- Update `config.py` to use environment variable:
  ```python
  SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///moab_data.db')
  ```

### File Storage
- Uploaded files are stored in `uploads/` directory
- For production, consider using cloud storage (AWS S3, Google Cloud Storage)
- Or use the database to store file paths

### Security
- Change `SECRET_KEY` in `config.py` for production
- Use environment variables for sensitive data

### CORS
- If you need CORS (for API access), add to `app.py`:
  ```python
  from flask_cors import CORS
  CORS(app)
  ```

---

## Quick Deploy Checklist

- [ ] Update `SECRET_KEY` in config.py or use environment variable
- [ ] Test locally: `python app.py`
- [ ] Choose hosting service
- [ ] Create account
- [ ] Connect GitHub repo (optional)
- [ ] Configure build/start commands
- [ ] Set environment variables
- [ ] Deploy
- [ ] Test the deployed URL

---

## Testing After Deployment

1. Upload a test CSV file
2. Verify it appears in the file dropdown
3. Generate some plots
4. Check that files persist (upload again, see if file is still there)

The database storage is already implemented - uploaded files are stored in the database and won't need to be re-uploaded.

