# [WFGY] Zone: SAFE | λ: 0.1 | Action: Test client with custom user intent
import asyncio
import json
import websockets

async def test_client():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected. Sending intent...")
            await websocket.send(json.dumps({
                "type": "SUBMIT_INTENT",
                "intent": "copie D:\\textual_inversion\\textual_inversion.py vers c:\\test\\"
            }))
            
            async for message in websocket:
                data = json.loads(message)
                print(f"Received event: {data}")
                if data.get("type") == "PLAN_FINISHED":
                    print("Plan finished event received.")
                    break
    except Exception as e:
        print(f"Connection/Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_client())
