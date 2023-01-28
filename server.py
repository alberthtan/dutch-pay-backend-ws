import asyncio
import websockets
import os
import json

CLIENTS = set()
NUM_CLIENTS = 0
MESSAGE_LIST = []
CLIENT_TABLES = dict()

async def handler(websocket):
    global NUM_CLIENTS
    global MESSAGE_LIST

    print(CLIENTS)
    
    if websocket not in CLIENTS:
        # print("adding client " + str(NUM_CLIENTS))
        # print(websocket)
        NUM_CLIENTS += 1
        CLIENTS.add(websocket)
    
        if(len(MESSAGE_LIST) != 0):
            await websocket.send(MESSAGE_LIST[-1])


        # print(CLIENTS)
    
    # BROADCAST IS CALLED ONCE PER CLICK
    async for message in websocket:
        print("appending new message to message list")
        print(json.loads(message))
        table_id = json.loads(message)['table_id']

        
        if not table_id in CLIENT_TABLES:
            CLIENT_TABLES[table_id] = []

        # Add user to CLIENT_TABLES if first time
        if not websocket in CLIENT_TABLES[table_id]:
            CLIENT_TABLES[table_id].append(websocket)
            if(len(MESSAGE_LIST) != 0):
                await websocket.send(MESSAGE_LIST[-1])

        # Otherwise treat message as an edit to cart
        else:
            MESSAGE_LIST.append(message)
            await broadcast(message)

    try:
        await websocket.wait_closed()
    finally:
        CLIENTS.remove(websocket)

async def broadcast(message):
    # i = 0
    for websocket in CLIENTS.copy():
        # print(i)
        # i += 1
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

# async def broadcast_messages():
#     while True:
#         await asyncio.sleep(1)
#         message = 'hello'
#         await broadcast(message)

# async def echo(websocket):
#     async for message in websocket:
#         # print(type(message))
#         print(message)
#         await broadcast()
#         await websocket.send("yoyoyo")
#         await websocket.send(message)

# DO NOT BROADCAST IN MAIN
async def main():
    async with websockets.serve(handler, host="", port=os.environ.get('PORT', 8000)):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())