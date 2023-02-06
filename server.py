import asyncio
import websockets
import os
import json
import CartItem

CLIENTS = set()
NUM_CLIENTS = 0
# MESSAGE_LIST = dict()
CLIENT_TABLES = dict() # {table_id: {websocket1, websocket2 ...}}
CLIENT_TABLEID_LOOKUP = dict()# {websocket: table_id}
CART_DICT = dict() # {table_id: [cartItem, cartItem, ...]}

async def handler(websocket):
    global NUM_CLIENTS
    # global MESSAGE_LIST

    print('handler')
    try: 
        async for websocket_message in websocket:
            message = json.loads(websocket_message)
            print(message)

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
            if 'flag' in message:
                if table_id in CART_DICT:
                    await websocket.send(json.dumps(CART_DICT[table_id]))
                    
            # All other messages should be treated as edits to the cart
            else:
                if not table_id in CART_DICT:
                    CART_DICT[table_id] = []
                if message['action'] == 'add':
                    print("ADDING HERE")
                    print(message['user'])
                    cartItem = CartItem(message['item'], message['user'])
                    print(cartItem)
                    CART_DICT[table_id][message['id']] = cartItem
                elif message['action'] == 'delete':
                    CART_DICT.pop(message['id'], None)
                elif message['action'] == 'share':
                    if message['id'] in CART_DICT[table_id]:
                        CART_DICT[table_id][message['id']].addUserToItem(message['user'])
                elif message['action'] == 'unshare':
                    if message['id'] in CART_DICT[table_id]:
                        CART_DICT[table_id][message['id']].removeUserToItem(message['user'])
                elif message['action'] == 'order':
                    for cartItem in CART_DICT[table_id].values():
                        if cartItem.get_orderedBy() == message['user']:
                            cartItem.set_isOrdered_true()

                await broadcast(json.dumps(CART_DICT[table_id].values()), table_id)
                
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

async def broadcast(message, table_id):

    for websocket in CLIENT_TABLES[table_id].copy():
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