import asyncio
import websockets
import os
import json
from cartitem import CartItem

CLIENTS = set()
NUM_CLIENTS = 0
# MESSAGE_LIST = dict()
CLIENT_TABLES = dict() # {table_id: {websocket1, websocket2 ...}}
CLIENT_TABLEID_LOOKUP = dict()# {websocket: table_id}
CART_DICT = dict() # {table_id: [cartItem, cartItem, ...]}

SERVER_TABLES = dict() # {table_id: [websocket1, websocket2]}
SERVER_TABLE_LOOKUP = dict() # {websocket: [table_id, ...]}

async def handler(websocket):
    global NUM_CLIENTS
    # global MESSAGE_LIST

    print('handler')
    try: 
        async for websocket_message in websocket:
            message = json.loads(websocket_message)
            print(message)

            # Message from a customer
            if 'flag' in message:
                table_id = message['table_id']


                # Add user to CLIENT_TABLES if nonexistent
                if not table_id in CLIENT_TABLES:
                    CLIENT_TABLES[table_id] = []
                if not websocket in CLIENT_TABLES[table_id]:
                    print("adding websocket to client tables")
                    
                    CLIENT_TABLES[table_id].append(websocket)
                    CLIENT_TABLEID_LOOKUP[websocket] = table_id

                    print(CLIENT_TABLES)
                    
                # Send latest cart data if user goes to Menu screen from camera screen
                if message['flag']:
                    if table_id in CART_DICT:
                        json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                        await websocket.send(json_message)
                # All other messages should be treated as edits to the cart
                else:
                    if not table_id in CART_DICT:
                        CART_DICT[table_id] = dict()
                    if message['action'] == 'add':
                        cartItem = CartItem(message['id'], message['item'], message['user'])
                        CART_DICT[table_id][message['id']] = cartItem
                    elif message['action'] == 'delete':
                        CART_DICT[table_id].pop(message['id'], None)
                    elif message['action'] == 'share':
                        if message['id'] in CART_DICT[table_id]:
                            CART_DICT[table_id][message['id']].addUserToItem(message['user'])
                    elif message['action'] == 'unshare':
                        if message['id'] in CART_DICT[table_id]:
                            CART_DICT[table_id][message['id']].removeUserFromItem(message['user'])
                    elif message['action'] == 'order':
                        for cartItem in CART_DICT[table_id].values():
                            if cartItem.get_orderedBy() == message['user']:
                                cartItem.set_isOrdered_true()

                        json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                        print(json_message)
                        await broadcast_to_servers(json_message, table_id)

                    json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                    print(json_message)
                    await broadcast_to_customers(json_message, table_id)

            # Message from a Server
            if 'restaurant' in message:
                # Add user to SERVER_TABLES if nonexistent
                for table_id in message['table_id_list']:
                    if not table_id in SERVER_TABLES:
                        SERVER_TABLES[table_id] = []
                    if not websocket in SERVER_TABLES[table_id]:
                        print("adding websocket to SERVER tables")
                        SERVER_TABLES[table_id].append(websocket)

                    # Add table to SERVER_TABLE_LOOKUP if nonexistent
                    if not websocket in SERVER_TABLE_LOOKUP:
                        SERVER_TABLE_LOOKUP[websocket] = []
                    if not table_id in SERVER_TABLE_LOOKUP[websocket]:
                        SERVER_TABLE_LOOKUP[websocket].append(table_id)

                if message['restaurant']: # Joining websocket
                    # Send data to server
                    print(SERVER_TABLE_LOOKUP)
                    json_message = []
                    for table_id in SERVER_TABLE_LOOKUP[websocket]:
                        if table_id in CART_DICT:
                            json_message.append(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                    await websocket.send(json.dumps(json_message))
                else: # Modify status of order
                    print("hello!")
                    
                
    except Exception as e:
        print("an error occurred")
        print(e)

    # WEBSOCKET CLOSES
    try:
        await websocket.wait_closed()
    except Exception as e:
        print("error")
        print(e)
    finally:
        # Remove user from table and CLIENTS 
        print("cleaning up")
        print(CLIENT_TABLES)
        table_id = CLIENT_TABLEID_LOOKUP[websocket]
        CLIENT_TABLES[table_id].remove(websocket)
        del CLIENT_TABLEID_LOOKUP[websocket]
        # CLIENTS.remove(websocket)
        print("after cleanup")
        print(CLIENT_TABLES)

        # RESTAURANT SHOULD DO THIS

        # # If no users at table, remove table
        # if not CLIENT_TABLES[table_id]:
        #     print("clearing table")
        #     print(MESSAGE_LIST)
        #     MESSAGE_LIST[table_id].clear()
        #     del CLIENT_TABLES[table_id]
        #     print(CLIENT_TABLES)

async def broadcast_to_customers(message, table_id):
    print('broadcasting to customers of ' + str(table_id))

    for websocket in CLIENT_TABLES[table_id].copy():
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass
        
async def broadcast_to_servers(message, table_id):
    print('broadcasting to servers of ' + str(table_id))

    for websocket in SERVER_TABLES[table_id].copy():
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

async def main():
    try: 
        async with websockets.serve(handler, host="", port=os.environ.get('PORT', 8000)):
            await asyncio.Future()  # run forever
    except:
        print("closed out")


if __name__ == "__main__":
    asyncio.run(main())










# import asyncio
# import websockets
# import os
# import json

# CLIENTS = set()
# NUM_CLIENTS = 0
# MESSAGE_LIST = dict()
# CLIENT_TABLES = dict() # {table_id: {websocket1, websocket2 ...}}
# CLIENT_TABLEID_LOOKUP = dict()# {websocket: table_id}
# CART_DICT = dict() # {table_id: [cartItem, cartItem, ...]}

# async def handler(websocket):
#     global NUM_CLIENTS
#     global MESSAGE_LIST

#     print('handler')
#     # if websocket not in CLIENTS:
#     #     NUM_CLIENTS += 1
#     #     CLIENTS.add(websocket)
    
#     #     if(len(MESSAGE_LIST) != 0):
#     #         await websocket.send(MESSAGE_LIST[-1])

#     # PROCESS MESSAGE
#     try: 
#         async for message in websocket:
#             print('message')
#             print(json.loads(message))

#             table_id = json.loads(message)['table_id']

#             # Add user to CLIENT_TABLES if nonexistent
#             if not table_id in CLIENT_TABLES:
#                 CLIENT_TABLES[table_id] = []
#             if not websocket in CLIENT_TABLES[table_id]:
#                 print("adding websocket to client tables")
                
#                 CLIENT_TABLES[table_id].append(websocket)
#                 CLIENT_TABLEID_LOOKUP[websocket] = table_id

#                 print(CLIENT_TABLES)

#             # Send latest cart data if user goes to Menu screen from camera screen
#             if 'flag' in json.loads(message):
#                 if table_id in MESSAGE_LIST and len(MESSAGE_LIST[table_id]) != 0:
#                     print("sending message")
#                     print(MESSAGE_LIST)
#                     await websocket.send(MESSAGE_LIST[table_id][-1])
#             # All other messages should be treated as edits to the cart
#             else:
#                 if not table_id in MESSAGE_LIST:
#                     MESSAGE_LIST[table_id] = []
#                 MESSAGE_LIST[table_id].append(message)
#                 print(MESSAGE_LIST)
#                 await broadcast(message, table_id)
#     except Exception as e:
#         print("an error occurred")
#         print(e)

#     # WEBSOCKET CLOSES
#     try:
#         await websocket.wait_closed()
#     except Exception as e:
#         print("error")
#         print(e)
#     finally:
#         # Remove user from table and CLIENTS 
#         print("cleaning up")
#         print(CLIENT_TABLES)
#         table_id = CLIENT_TABLEID_LOOKUP[websocket]
#         CLIENT_TABLES[table_id].remove(websocket)
#         del CLIENT_TABLEID_LOOKUP[websocket]
#         # CLIENTS.remove(websocket)
#         print("after cleanup")
#         print(CLIENT_TABLES)

#         # RESTAURANT SHOULD DO THIS

#         # # If no users at table, remove table
#         # if not CLIENT_TABLES[table_id]:
#         #     print("clearing table")
#         #     print(MESSAGE_LIST)
#         #     MESSAGE_LIST[table_id].clear()
#         #     del CLIENT_TABLES[table_id]
#         #     print(CLIENT_TABLES)

# async def broadcast(message, table_id):

#     for websocket in CLIENT_TABLES[table_id].copy():
#         try:
#             await websocket.send(message)
#         except websockets.ConnectionClosed:
#             pass

# async def main():
#     try: 
#         async with websockets.serve(handler, host="", port=os.environ.get('PORT', 8000)):
#             await asyncio.Future()  # run forever
#     except:
#         print("closed out")


# if __name__ == "__main__":
#     asyncio.run(main())