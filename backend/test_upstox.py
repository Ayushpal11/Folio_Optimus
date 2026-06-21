from dotenv import load_dotenv
import os
from app.upstox import client

# Load environment variables
load_dotenv("backend/.env")

def test_upstox_connection():
    token = os.getenv("UPSTOX_ACCESS_TOKEN")
    if not token:
        print("❌ Error: UPSTOX_ACCESS_TOKEN not found in environment.")
        return

    print(f"Testing connection with token: {token[:10]}...{token[-10:]}")
    
    try:
        upstox = client.UpstoxClient(token)
        # Try to get LTP for RELIANCE (NSE_EQ|INE002A01018)
        instrument_key = "NSE_EQ|INE002A01018"
        print(f"Fetching LTP for {instrument_key}...")
        
        ltp_data = upstox.get_ltp(instrument_key)
        print("✅ Successfully connected to Upstox API!")
        print(f"LTP Data: {ltp_data}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    test_upstox_connection()
