# test_auth.py
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_signIn():
    base_url = os.getenv("EXPRESS_API_BASE_URL", "https://dowhistle-dev.herokuapp.com/v3")
    url = f"{base_url}/twilio/sign-in"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MCP-Server/1.0"
    }
    
    if os.getenv("API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('API_KEY')}"
    
    payload = {
        "phone": "9994076214",
        "country_code": "+91",
        "name": "Test User",
        "location": [10.997, 76.961]
    }
    
    print(f"Testing: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Error Response: {e.response.text}")
        except Exception as e:
            print(f"Other Error: {str(e)}")

async def test_verifyOtp():
    base_url = os.getenv("EXPRESS_API_BASE_URL", "https://dowhistle-dev.herokuapp.com/v3")
    url = f"{base_url}/twilio/verify-otp"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MCP-Server/1.0"
    }
    
    if os.getenv("API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('API_KEY')}"
    
    payload = {"id": "687e16902de5f0ffb1884609", "otp": 671536}

    
    print(f"Testing: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Error Response: {e.response.text}")
        except Exception as e:
            print(f"Other Error: {str(e)}")

async def test_resentOtp():
    base_url = os.getenv("EXPRESS_API_BASE_URL", "https://dowhistle-dev.herokuapp.com/v3")
    url = f"{base_url}/twilio/resend-otp"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "MCP-Server/1.0"
    }
    
    if os.getenv("API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('API_KEY')}"
    
    payload = {"userid": "687e16902de5f0ffb1884609"}

    
    print(f"Testing: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code}")
            print(f"Error Response: {e.response.text}")
        except Exception as e:
            print(f"Other Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_resentOtp())

    