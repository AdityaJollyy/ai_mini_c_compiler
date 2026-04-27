"""
main.py:
Mini-C Compiler API
FastAPI backend providing endpoints for compilation, code generation, and code fixing
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import traceback

# Add the current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semantic import Compiler
from ai_service import AIService
from executor import Executor

# Initialize FastAPI app
app = FastAPI(
    title="Mini-C Compiler API",
    description="API for compiling Mini-C code with AI-assisted generation and fixing",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
compiler = Compiler()
executor = Executor()
ai_service = AIService()


# Request/Response Models
class CompileRequest(BaseModel):
    code: str


class CompileError(BaseModel):
    line: int
    type: str  # "Syntax" | "Semantic" | "Lexical"
    message: str


class CompileResponse(BaseModel):
    success: bool
    errors: List[CompileError]
    output: Optional[str] = None  # Program output when execution succeeds


class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    code: str


class FixRequest(BaseModel):
    code: str
    errors: str


class FixResponse(BaseModel):
    fixed_code: str


class ErrorResponse(BaseModel):
    detail: str


# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Mini-C Compiler API is running"}


@app.post("/compile", response_model=CompileResponse)
async def compile_code(request: CompileRequest):
    """
    Compile Mini-C code and return compilation result
    
    - Performs lexical analysis
    - Performs syntax analysis (parsing)
    - Performs semantic analysis
    - If successful, executes the program and returns output
    - Returns structured errors if any
    """
    try:
        result = compiler.compile(request.code)
        
        errors = [
            CompileError(
                line=err.get('line', 0),
                type=err.get('type', 'Unknown'),
                message=err.get('message', 'Unknown error')
            )
            for err in result['errors']
        ]
        
        # If compilation successful, execute the program
        if result['success'] and result['ast'] is not None:
            exec_result = executor.execute(result['ast'])
            
            if exec_result['success']:
                return CompileResponse(
                    success=True,
                    errors=[],
                    output=exec_result['output']
                )
            else:
                # Execution failed - return runtime error
                return CompileResponse(
                    success=False,
                    errors=[CompileError(
                        line=0,
                        type="Runtime",
                        message=exec_result.get('error', 'Unknown runtime error')
                    )],
                    output=exec_result.get('output', '')
                )
        
        # Compilation failed or empty program
        return CompileResponse(
            success=result['success'],
            errors=errors,
            output=None
        )
    except Exception as e:
        print(f"Compilation error: {traceback.format_exc()}")
        return CompileResponse(
            success=False,
            errors=[CompileError(line=0, type="Internal", message=f"Compiler error: {str(e)}")],
            output=None
        )


@app.post("/generate", response_model=GenerateResponse)
async def generate_code(request: GenerateRequest):
    """
    Generate Mini-C code using AI based on user prompt
    
    Uses Gemini via OpenAI-compatible API to generate code
    that follows Mini-C language constraints
    """
    try:
        # Call synchronous method (not async)
        code = ai_service.generate_code(request.prompt)
        return GenerateResponse(code=code)
    except Exception as e:
        error_msg = str(e)
        print(f"Generation error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/fix", response_model=FixResponse)
async def fix_code(request: FixRequest):
    """
    Fix Mini-C code using AI based on compiler errors
    
    Sends both the code and error messages to AI
    to generate corrected code
    """
    try:
        # Call synchronous method (not async)
        fixed_code = ai_service.fix_code(request.code, request.errors)
        return FixResponse(fixed_code=fixed_code)
    except Exception as e:
        error_msg = str(e)
        print(f"Fix error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_msg)


# Sample prompts endpoint for testing
@app.get("/sample-prompts")
async def get_sample_prompts():
    """Return sample prompts for testing the AI generation"""
    return {
        "prompts": [
            "Create a program that declares two integer variables x and y, sets them to 10 and 20, and prints their sum",
            "Write code that declares an integer, assigns it 100, then subtracts 25 and prints the result",
            "Create a program that checks if a number is greater than 50 and prints it if true",
            "Write Mini-C code that multiplies two numbers and prints the product",
            "Create a program with three variables that calculates and prints an average"
        ]
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    api_key_set = bool(os.getenv("GEMINI_API_KEY"))
    return {
        "status": "ok",
        "compiler": "ready",
        "ai_service": "ready" if api_key_set else "no API key",
        "api_key_configured": api_key_set
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting Mini-C Compiler API server...")
    print("Make sure GEMINI_API_KEY is set in .env file for AI features")
    uvicorn.run(app, host="0.0.0.0", port=8000)