# Flask Backend Deployment to Render

## 📋 Prerequisites

- GitHub account
- Render account (free tier available at [render.com](https://render.com))
- Your GMC Merchant ID

---

## 🚀 Step-by-Step Deployment

### Step 1: Initialize Git Repository

```bash
cd gmc-automation
git init
git add .
git commit -m "Initial commit - GMC Backend"
```

### Step 2: Create GitHub Repository

1. Go to [github.com](https://github.com) and create a new repository
2. Name it: `gmc-backend` (or any name you prefer)
3. **Important**: Do NOT initialize with README (we already have code)
4. Copy the repository URL

### Step 3: Push to GitHub

```bash
git remote add origin YOUR_GITHUB_REPO_URL
git branch -M main
git push -u origin main
```

**Example**:
```bash
git remote add origin https://github.com/yourusername/gmc-backend.git
git branch -M main
git push -u origin main
```

---

### Step 4: Deploy on Render

1. **Go to Render Dashboard**: [dashboard.render.com](https://dashboard.render.com)

2. **Create New Web Service**:
   - Click **"New +"** → **"Web Service"**
   - Click **"Connect GitHub"** and authorize Render
   - Select your `gmc-backend` repository

3. **Configure Service**:
   - **Name**: `gmc-backend` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave blank
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`

4. **Set Environment Variables**:
   Click **"Advanced"** → **"Add Environment Variable"**
   
   Add these variables:
   ```
   GMC_MERCHANT_ID = your_merchant_id_here
   PORT = 10000
   ```

5. **Select Plan**:
   - Choose **"Free"** plan (750 hours/month)

6. **Click "Create Web Service"**

---

### Step 5: Wait for Deployment

Render will:
1. Clone your repository
2. Install dependencies from `requirements.txt`
3. Start your Flask server
4. Give you a public URL like: `https://gmc-backend-xxxx.onrender.com`

**Deployment takes 2-5 minutes**. Watch the logs in real-time.

---

### Step 6: Verify Backend is Running

Once deployed, test these endpoints:

1. **Health Check**:
   ```
   https://your-app.onrender.com/health
   ```
   Should return: `{"status": "ok", "gmc_ready": true}`

2. **Products API**:
   ```
   https://your-app.onrender.com/api/products
   ```
   Should return your products JSON

---

### Step 7: Update Vercel Frontend

Now update your Next.js dashboard to use the Render backend:

1. **Go to Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)

2. **Select your project** → **Settings** → **Environment Variables**

3. **Update** `NEXT_PUBLIC_API_URL`:
   ```
   NEXT_PUBLIC_API_URL = https://your-app.onrender.com
   ```

4. **Redeploy**:
   ```bash
   cd gmc-dashboard
   vercel --prod
   ```

---

## 🔒 Important Files for Deployment

### ✅ Already Created

- **`render.yaml`** - Render configuration
- **`requirements.txt`** - Python dependencies
- **`server.py`** - Updated with PORT environment variable
- **`.env`** - Local environment variables (NOT deployed)

### 🚫 Files to Ignore

Create a `.gitignore` file if you haven't:

```gitignore
__pycache__/
*.pyc
.env
service_account.json
gmc_state.db
*.log
.venv/
```

**IMPORTANT**: Never commit `service_account.json` or `.env` to GitHub!

---

## 📁 Upload Service Account to Render

Since `service_account.json` is not in Git (for security), you need to add it manually:

### Option 1: Environment Variable (Recommended)

1. Copy the contents of `service_account.json`
2. In Render Dashboard → Environment Variables
3. Add:
   ```
   GOOGLE_CREDENTIALS = {"type": "service_account", "project_id": "..."}
   ```
4. Update `server.py` to read from environment variable

### Option 2: Render Disk (Simpler)

1. After deployment, go to **Shell** tab in Render
2. Upload `service_account.json` manually
3. Place it in the project root

**For now, use Option 2 for quick testing.**

---

## 🧪 Testing the Full Stack

### Local Testing
```bash
# Terminal 1 - Backend (local)
cd gmc-automation
python server.py

# Terminal 2 - Frontend (local)
cd gmc-dashboard
npm run dev
```

### Production Testing
1. **Backend**: `https://your-backend.onrender.com/health`
2. **Frontend**: `https://your-dashboard.vercel.app`
3. **Test Upload**: Go to `/upload` and upload a CSV

---

## ⚠️ Common Issues

### Issue 1: "Application failed to respond"
**Solution**: Check Render logs. Usually means:
- Missing environment variable
- `service_account.json` not found
- Port not set correctly

### Issue 2: CORS errors in browser
**Solution**: Update `server.py` CORS settings:
```python
CORS(app, origins=["https://your-dashboard.vercel.app"])
```

### Issue 3: Free tier sleeps after inactivity
**Solution**: 
- Free Render apps sleep after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- Upgrade to paid plan ($7/month) for always-on

---

## 📊 Monitor Your Deployment

### Render Dashboard
- **Logs**: Real-time server logs
- **Metrics**: CPU, Memory usage
- **Events**: Deployment history

### Health Endpoint
Set up monitoring with:
- [UptimeRobot](https://uptimerobot.com) (free)
- Ping `/health` every 5 minutes

---

## 🎉 You're Done!

Your full stack is now deployed:
- ✅ **Frontend**: Vercel (Next.js)
- ✅ **Backend**: Render (Flask)
- ✅ **Database**: SQLite on Render disk
- ✅ **GMC Integration**: Service account configured

Share the Vercel URL with your tech team for testing! 🚀
