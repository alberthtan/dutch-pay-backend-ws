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
    print("handler called")
    global NUM_CLIENTS
    global MESSAGE_LIST

    # print(CLIENTS)
    
    if websocket not in CLIENTS:
        # print("adding client " + str(NUM_CLIENTS))
        # print(websocket)
        print("adding websocket")
        NUM_CLIENTS += 1
        CLIENTS.add(websocket)
    
        if(len(MESSAGE_LIST) != 0):
            await websocket.send(MESSAGE_LIST[-1])


        # print(CLIENTS)
    
    # BROADCAST IS CALLED ONCE PER CLICK
    async for message in websocket:
        print("appending new message to message list")
        print(json.loads(message))
        print(CLIENTS)
        table_id = json.loads(message)['table_id']

        
        if not table_id in CLIENT_TABLES:
            CLIENT_TABLES[table_id] = []

        # Add user to CLIENT_TABLES if first time
        if not websocket in CLIENT_TABLES[table_id]:
            CLIENT_TABLES[table_id].append(websocket)
            CLIENT_TABLEID_LOOKUP[websocket] = table_id
            if(len(MESSAGE_LIST) != 0):
                await websocket.send(MESSAGE_LIST[-1])

        # Otherwise treat message as an edit to cart
        else:
            MESSAGE_LIST.append(message)
            await broadcast(message)

    # SHOULD RUN IF USER ORDERS
    try:
        await websocket.wait_closed()
    finally:
        # CLEAN UP
        print("cleaning up")
        table_id = CLIENT_TABLEID_LOOKUP[websocket]
        CLIENT_TABLES[table_id].remove(websocket)
        del CLIENT_TABLEID_LOOKUP[websocket]
        CLIENTS.remove(websocket)
        print(CLIENTS)

        if not CLIENT_TABLES[table_id]:
            print("clearing table")
            MESSAGE_LIST.clear()
            del CLIENT_TABLES[table_id]
            print(CLIENT_TABLES)

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