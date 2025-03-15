from app import app

# This file is needed for Vercel to identify the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000) 