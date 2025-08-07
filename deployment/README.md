# 🚀 Convergio Azure Deployment Guide

**This guide details how to deploy the Convergio platform (FastAPI backend, SvelteKit frontend, PostgreSQL, Redis) to Azure, with Docker completely removed.**

---

## 1. Prerequisites
- Azure account with active subscription
- Python 3.11+ (for backend)
- Node.js 18+ (for frontend)
- GitHub account (for CI/CD)
- Local PostgreSQL/Redis for development (optional)

---

## 2. Azure Resource Planning
- **Subscription**: Choose in Azure Portal/CLI when creating resources
- **Resource Group**: Create a new or use existing (e.g. `convergio-rg`)
- **Region**: Select closest to your users (e.g. `westeurope`)
- **SKU/Pricing**: Start with Basic/Free for dev, scale up for prod

---

## 3. Backend (FastAPI) - Azure App Service
1. **Create App Service**
   - Runtime: Python 3.11+
   - Region, SKU, Resource Group as above
2. **Configure Startup Command**
   - In App Service > Configuration > General settings:
     ```
     gunicorn --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 src.main:app
     ```
3. **Set Environment Variables**
   - In App Service > Configuration > Application settings
   - Add all keys from `backend/.env.example`
4. **Connect to PostgreSQL/Redis**
   - Use Azure connection strings (see below)
5. **Deploy Code**
   - Use GitHub Actions (Deployment Center) or manual zip deploy

---

## 4. Frontend (SvelteKit) - Azure Static Web Apps
1. **Install Azure Adapter**
   - `npm install -D svelte-adapter-azure-swa`
   - In `svelte.config.js`:
     ```js
     import azure from 'svelte-adapter-azure-swa';
     export default { kit: { adapter: azure() } };
     ```
2. **Create Static Web App**
   - Link to your GitHub repo
   - Select SvelteKit preset
   - Set build output as per adapter docs
3. **Set Environment Variables**
   - In Static Web App > Configuration > Environment variables
   - Add all keys from `frontend/.env.example`
4. **Deploy**
   - Azure will auto-create a GitHub Actions workflow

---

## 5. Database & Cache
- **Azure Database for PostgreSQL**
  - Create Flexible Server, enable `pgvector` extension
  - Copy connection string, update in App Service settings
- **Azure Cache for Redis**
  - Create instance, copy connection string, update in App Service settings

---

## 6. CI/CD (GitHub Actions)
- Use Azure Deployment Center to auto-generate workflows
- For custom: use `azure/webapps-deploy@v2` for backend, `Azure/static-web-apps-deploy@v1` for frontend
- Store secrets in GitHub repo settings

---

## 7. Local Development (Bare Metal)
- Backend:
  ```bash
  cd backend
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env  # configure
  uvicorn src.main:app --reload --port 9000
  ```
- Frontend:
  ```bash
  cd frontend
  npm install
  cp .env.example .env  # configure
  npm run dev
  ```
- Use local Postgres/Redis or point to Azure services

---

## 8. Testing & Troubleshooting
- Check App Service/Static Web App logs in Azure Portal
- Use SSH/Console for debugging
- Ensure all env vars are set
- Test endpoints: `/health`, `/docs`, frontend root
- Use Azure Monitor for metrics

---

## 9. Production Checklist
- [ ] All Docker files/references removed
- [ ] All env vars set in Azure
- [ ] Database/Redis connection tested
- [ ] CI/CD pipeline green
- [ ] HTTPS enabled
- [ ] Scaling/SKU reviewed
- [ ] Monitoring/alerts configured

---

## 10. Notes
- **Docker is NOT required or supported.**
- All deployment is via native Python/Node.js or Azure services.
- For resource selection (subscription, region, SKU), use Azure Portal or CLI at resource creation.
- For advanced: see Azure CLI docs for scripting resource creation.

---

**For questions or issues, see the main README or open an issue on GitHub.**
