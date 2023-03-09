import asyncio
import websockets
import os
import json
import stripe
from cartitem import CartItem
from uuid import uuid4

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

CLIENTS = set()
NUM_CLIENTS = 0
# MESSAGE_LIST = dict()
CLIENT_TABLES = dict() # {table_id: [websocket1, websocket2 ...]}
CLIENT_TABLE_LOOKUP = dict()# {websocket: table_id}
CART_DICT = dict() # {table_id: {id: cartItem, id: cartItem, ...}}

SERVER_TABLES = dict() # {table_id: [websocket1, websocket2]}
SERVER_TABLE_LOOKUP = dict() # {websocket: [table_id, ...]}

PAYMENT_INTENTS = dict() # {table_id1: {user_id: [payment_intent1, payment_intent2, ...]}, 
USERS_AT_TABLES = dict() # {tabled_id: [user_id]}

async def handler(websocket):
    global NUM_CLIENTS

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
                    CLIENT_TABLE_LOOKUP[websocket] = table_id

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
                        cartItem = CartItem(message['id'], message['item'], message['user'], table_id)
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

                        user_id = json.loads(message['user'])['id']
                        print(json.loads(message['user']))

                        if table_id not in USERS_AT_TABLES:
                            USERS_AT_TABLES[table_id] = []
                        if user_id not in USERS_AT_TABLES[table_id]:
                            USERS_AT_TABLES[table_id].append(user_id)

                        if table_id not in PAYMENT_INTENTS:
                            PAYMENT_INTENTS[table_id] = dict()

                        if user_id not in PAYMENT_INTENTS[table_id]:
                            PAYMENT_INTENTS[table_id][user_id] = []

                        PAYMENT_INTENTS[table_id][user_id].append(message['payment_intent'])

                        for cartItem in CART_DICT[table_id].values():
                            if cartItem.get_orderedBy() == message['user'] and cartItem.get_status() == "pending":
                                cartItem.set_status("ordered")
                                cartItem.set_order_id(uuid4())
                        

                        json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                        print("broadcasting this message to servers:")
                        print(json_message)
                        await broadcast_to_servers(json_message, table_id)

                    json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                    print("broadcasting this message to customers:")
                    print(json_message)
                    await broadcast_to_customers(json_message, table_id)

            # Message from a Server
            if 'restaurant' in message:

                if message['restaurant']: # Joining websocket
                    # Send data to server

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

                    # print(SERVER_TABLE_LOOKUP)
                    json_message = []
                    for table_id in SERVER_TABLE_LOOKUP[websocket]:
                        if table_id in CART_DICT:
                            json_message.append(json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4))
                    message = {
                        "json_message": json.dumps(json_message),
                        "refresh": True
                    }
                    await websocket.send(json.dumps(message))
                else: # Modify status of order
                    if message['action'] == "send":
                        table_id = message['table_id']
                        item_id = message['item_id']
                        CART_DICT[table_id][item_id].set_status("received")
                        
                        json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                        await broadcast_to_servers(json_message, table_id)
                        await broadcast_to_customers(json_message, table_id)

                    elif message['action'] == "delete":
                        table_id = message['table_id']
                        item_id = message['item_id']
                        del CART_DICT[table_id][item_id]
                        
                        json_message = json.dumps(list(CART_DICT[table_id].values()), default=lambda o: o.__dict__, indent=4)
                        await broadcast_to_servers(json_message, table_id)
                        await broadcast_to_customers(json_message, table_id)

                    elif message['action'] == "clear":
                        table_id = message['table_id']

                        for user in USERS_AT_TABLES[table_id]:
                            for p_id in PAYMENT_INTENTS[table_id][user]:
                                payment_intent = stripe.PaymentIntent.retrieve(p_id)
                                payment_intent.cancel()
                            del PAYMENT_INTENTS[table_id][user]
                        
                        del PAYMENT_INTENTS[table_id]
                        del USERS_AT_TABLES[table_id]

                        del CART_DICT[table_id]
                        print("CLEAR")
                        print(CART_DICT)

                        # Clear customers from table
                        for client in CLIENT_TABLES[table_id].copy():
                            message = {
                                "clear": True
                            }
                            await client.send(json.dumps(message))

                        # Update servers with new set of tables (after deleting)
                        print(SERVER_TABLES)
                        for server in SERVER_TABLES[table_id].copy():
                            print("clearing server")
                            print(server)
                            json_message = []
                            for id in SERVER_TABLE_LOOKUP[server]:
                                if id in CART_DICT:
                                    print("nothing hopefully")
                                    print(CART_DICT[id])
                                    json_message.append(json.dumps(list(CART_DICT[id].values()), default=lambda o: o.__dict__, indent=4))
                            message = {
                                "json_message": json.dumps(json_message),
                                "table_id": table_id,
                                "refresh": True
                            }
                            print(json_message)
                            print(message)
                            # print("sending message: " + str(json_message))
                            # await broadcast_to_servers(json_message, table_id)
                            await server.send(json.dumps(message))
                            print("done")

            # if 'payment_intent' in message:
            #     table_id = message['table_id']
            #     user_id = message['user_id']

            #     if table_id not in USERS_AT_TABLES:
            #         USERS_AT_TABLES[table_id] = []
            #     if user_id not in USERS_AT_TABLES[table_id]:
            #         USERS_AT_TABLES[table_id].append(user_id)

            #     if table_id not in PAYMENT_INTENTS:
            #         PAYMENT_INTENTS[table_id] = dict()

            #     if user_id not in PAYMENT_INTENTS[table_id]:
            #         PAYMENT_INTENTS[table_id][user_id] = []

            #     PAYMENT_INTENTS[table_id][user_id].append(message['payment'])

                
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
        print("cleaning up")
        if websocket in CLIENT_TABLE_LOOKUP:
            table_id = CLIENT_TABLE_LOOKUP[websocket]
            CLIENT_TABLES[table_id].remove(websocket)
            del CLIENT_TABLE_LOOKUP[websocket]
            print("after cleanup client")
            print(CLIENT_TABLE_LOOKUP)
            print(CLIENT_TABLES)

        if websocket in SERVER_TABLE_LOOKUP:
            for table_id in SERVER_TABLE_LOOKUP[websocket]:
                SERVER_TABLES[table_id].remove(websocket)
                if(len(SERVER_TABLES[table_id]) == 0):
                    del SERVER_TABLES[table_id]
            del SERVER_TABLE_LOOKUP[websocket]

            print("after cleanup server")
            print(SERVER_TABLE_LOOKUP)
            print(SERVER_TABLES)

        


async def broadcast_to_customers(message, table_id):
    print('broadcasting to customers of ' + str(table_id))

    for websocket in CLIENT_TABLES[table_id].copy():
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass
        
async def broadcast_to_servers(json_message, table_id):
    print('broadcasting to servers of ' + str(table_id))

    if table_id in SERVER_TABLES:
        for websocket in SERVER_TABLES[table_id].copy():
            try:
                message = {
                    "json_message": json_message,
                    "table_id": table_id,
                    "refresh": False
                }
                await websocket.send(json.dumps(message))
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