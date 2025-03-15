# Deployment Guide

This guide will walk you through deploying your Night Sky Planet Viewer to Vercel using GitHub.

## GitHub Setup

1. Create a new GitHub repository
2. Push your code to GitHub:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/your-username/night-sky-planets.git
   git push -u origin main
   ```

## Vercel Deployment

1. Sign up or log in to [Vercel](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository
4. Configure the project:
   - Framework Preset: Other
   - Root Directory: ./
   - Build Command: Leave empty
   - Output Directory: Leave empty
5. Add Environment Variables:
   - ASTRONOMY_API_AUTH_TOKEN: Your API token
   - LATITUDE: Your location latitude
   - LONGITUDE: Your location longitude
6. Click "Deploy"

## After Deployment

After deployment, your app will be available at a Vercel-assigned domain. You can set up a custom domain through the Vercel dashboard.

## Troubleshooting

If your deployment has issues:

1. Check the Vercel logs for any errors
2. Make sure your environment variables are set correctly
3. Ensure your `.env` file is not included in the repository (it should be in `.gitignore`) 