from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from agent import run_agent  # Import your agent function

app = FastAPI()

# Enable CORS for frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "TailorTalk Calendar Agent Backend"}

@app.post("/agent")
async def agent_endpoint(request: Request):
    try:
        body = await request.json()
        user_text = body.get("message", "")
        print("📥 Received from frontend:", user_text)

        response = run_agent(user_text)  # Call to LangGraph pipeline
        return {"response": response}

    except Exception as e:
        print("❌ Backend error:", e)
        return JSONResponse(
            status_code=500,
            content={"response": "Server error. Please try again later."}
        )
