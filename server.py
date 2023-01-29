import asyncio
import websockets
import os
import json

CLIENTS = set()
NUM_CLIENTS = 0
MESSAGE_LIST = []
CLIENT_TABLES = dict() # {table_id: {websocekt1, websocekt2 ...}}
CLIENT_TABLEID_LOOKUP = dict()# {websocket: table_id}

async def handler(websocket):
    global NUM_CLIENTS
    global MESSAGE_LIST

    
    if websocket not in CLIENTS:
        NUM_CLIENTS += 1
        CLIENTS.add(websocket)
    
        if(len(MESSAGE_LIST) != 0):
            await websocket.send(MESSAGE_LIST[-1])

    # PROCESS MESSAGE
    async for message in websocket:
        print(json.loads(message))
        table_id = json.loads(message)['table_id']

        
        if not table_id in CLIENT_TABLES:
            CLIENT_TABLES[table_id] = []

        # Add user to CLIENT_TABLES if first time
        if not websocket in CLIENT_TABLES[table_id]:
            CLIENT_TABLES[table_id].append(websocket)
            CLIENT_TABLEID_LOOKUP[websocket] = table_id

            # Send cart data if it exists, the first time a user goes on
            if(len(MESSAGE_LIST) != 0):
                await websocket.send(MESSAGE_LIST[-1])

        # If user already exists, treat message as an edit to cart
        else:
            MESSAGE_LIST.append(message)
            await broadcast(message)

    # USER PRESSES ORDER
    try:
        await websocket.wait_closed()
    finally:
        # Remove user from table and CLIENTS 
        print("cleaning up")
        table_id = CLIENT_TABLEID_LOOKUP[websocket]
        CLIENT_TABLES[table_id].remove(websocket)
        del CLIENT_TABLEID_LOOKUP[websocket]
        CLIENTS.remove(websocket)

        # If no users at table, remove table
        if not CLIENT_TABLES[table_id]:
            print("clearing table")
            MESSAGE_LIST.clear()
            del CLIENT_TABLES[table_id]
            print(CLIENT_TABLES)

async def broadcast(message):
    for websocket in CLIENTS.copy():
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

async def main():
    async with websockets.serve(handler, host="", port=os.environ.get('PORT', 8000)):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())