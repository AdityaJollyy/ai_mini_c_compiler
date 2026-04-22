"""
AI Service for Mini-C Compiler
Uses OpenAI SDK configured for Gemini via OpenAI-compatible API
"""

import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# System prompts
GENERATION_SYSTEM_PROMPT = """You are a Mini-C code generator. Generate valid Mini-C code only using these supported constructs:

SUPPORTED:
- int declarations: int x; or int x = 5;
- assignments: x = 5; or x = x + 2;
- arithmetic operators: +, -, *, /
- printf statements: printf("%d", x); or printf("%d %d", x, y);
- if statements: if (x > 5) { printf("%d", x); }
- comparison operators: <, >, <=, >=, ==, !=

PRINTF FORMAT:
- Use printf("%d", variable); for single variable
- Use printf("%d %d", var1, var2); for multiple variables
- Only %d and %i format specifiers are supported

NOT SUPPORTED (DO NOT USE):
- functions (no main(), no function definitions)
- loops (no for, while, do-while)
- arrays
- pointers
- return statements
- else statements
- comments

Output ONLY the code, no explanations. The code should be a sequence of statements without a main function wrapper."""

FIX_SYSTEM_PROMPT = """You are a Mini-C compiler assistant. Fix the given code based on the compiler errors provided.

SUPPORTED CONSTRUCTS:
- int declarations: int x; or int x = 5;
- assignments: x = 5; or x = x + 2;
- arithmetic operators: +, -, *, /
- printf statements: printf("%d", x); or printf("%d %d", x, y);
- if statements: if (x > 5) { printf("%d", x); }
- comparison operators: <, >, <=, >=, ==, !=

PRINTF FORMAT:
- Use printf("%d", variable); for printing integers
- Only %d and %i format specifiers are supported

NOT SUPPORTED (DO NOT USE):
- functions, loops, arrays, pointers, return, else

IMPORTANT: For each fix you make, add a brief inline comment starting with "// FIXED:" explaining what was changed.
Examples:
- int x; // FIXED: added missing declaration
- printf("%d", x); // FIXED: changed %s to %d
- x = 5; // FIXED: added missing semicolon

Return ONLY the corrected code with FIXED comments, no other explanations."""


def clean_code_response(code: str) -> str:
    """Remove markdown code blocks and clean up the response"""
    code = code.strip()
    
    # Remove markdown code blocks if present
    if code.startswith("```"):
        lines = code.split("\n")
        # Remove first line (```c or ```)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    
    # Also handle case where ``` appears at the end without newline
    if code.endswith("```"):
        code = code[:-3].strip()
    
    return code.strip()


class AIService:
    """AI Service for code generation and fixing using Gemini via OpenAI SDK"""
    
    def __init__(self):
        # Configure for Gemini via OpenAI-compatible API
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        self.model = "gemini-3.1-flash-lite-preview"  # Use the appropriate Gemini model name
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except Exception as e:
                raise Exception(f"Failed to initialize OpenAI client: {str(e)}")
        return self._client
    
    def generate_code(self, prompt: str) -> str:
        """
        Generate Mini-C code based on user prompt (synchronous)
        
        Args:
            prompt: User's description of what code to generate
            
        Returns:
            Generated Mini-C code
        """
        if not self.api_key:
            raise Exception("GEMINI_API_KEY environment variable is not set. Please set it in backend/.env file.")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            
            code = response.choices[0].message.content
            if code is None:
                raise Exception("AI returned empty response")
            
            return clean_code_response(code)
            
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid GEMINI_API_KEY. Please check your API key in backend/.env file.")
            elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota exceeded or rate limited. Please try again later.")
            else:
                raise Exception(f"AI generation failed: {error_msg}")
    
    def fix_code(self, code: str, errors: str) -> str:
        """
        Fix Mini-C code based on compiler errors (synchronous)
        
        Args:
            code: The buggy Mini-C code
            errors: Compiler error messages
            
        Returns:
            Fixed Mini-C code
        """
        if not self.api_key:
            raise Exception("GEMINI_API_KEY environment variable is not set. Please set it in backend/.env file.")
        
        try:
            user_message = f"""Please fix this Mini-C code:

```c
{code}
```

Compiler errors:
{errors}

Return only the fixed code."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": FIX_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            
            fixed_code = response.choices[0].message.content
            if fixed_code is None:
                raise Exception("AI returned empty response")
            
            return clean_code_response(fixed_code)
            
        except Exception as e:
            error_msg = str(e)
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid GEMINI_API_KEY. Please check your API key in backend/.env file.")
            elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota exceeded or rate limited. Please try again later.")
            else:
                raise Exception(f"AI fix failed: {error_msg}")


# For testing
if __name__ == "__main__":
    service = AIService()
    
    # Test generation
    print("=== Testing Code Generation ===")
    prompt = "Create a program that declares two variables x and y, assigns them values, adds them together, and prints the result"
    try:
        code = service.generate_code(prompt)
        print(f"Generated code:\n{code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test fixing
    print("\n=== Testing Code Fix ===")
    buggy_code = """
int x = 5;
y = 10;
printf(z);
"""
    errors = """Line 2: Semantic Error - Variable 'y' not declared
Line 3: Semantic Error - Variable 'z' not declared"""
    
    try:
        fixed = service.fix_code(buggy_code, errors)
        print(f"Fixed code:\n{fixed}")
    except Exception as e:
        print(f"Error: {e}")