from fastapi import FastAPI
from stuff import model
from stuff import handle
# from fastapi import FastAPI, Depends, UploadFile, Header
from fastapi import UploadFile, File, Form

from fastapi import WebSocket
from typing import List

import json

from fastapi.middleware.cors import CORSMiddleware
# from tasks import tasks, models

app = FastAPI()

# origins = ["http://localhost:3000", "https://tradethrill.netlify.app"]       #write the server of frontend in your laptop
origins = ["*"]       #write the server of frontend in your laptop

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/register")
async def register(data:model.User_For_Registration):
    a = await handle.handle_register(data)
    return a

@app.post("/otp")
async def otp(data:model.OTP):
    a = await handle.verify_otp(data)
    return a

@app.post("/forgotpassword")
async def forgot_password(data:model.ForgotPassword):
    a = await handle.forgot_password(data)
    return a

@app.post("/newotp")
async def new_otp(data:model.OTP):
    a = await handle.new_otp(data)
    return a

@app.get("/login/{user_id}")
async def login(user_id: int):
    # print("hello")
    print(user_id)
    a = await handle.login(user_id)
    return a

# @app.get("/get_user_info")
# async def get_user_info(user_id: int):
#     a = await handle.get_user_info(user_id)
#     return a

@app.post("/notify_request")
async def notify_request(data:model.Notification):
    a = await handle.notify_request(data)
    return a

@app.post("/notify_accept")
async def notify_accept(data:model.Notifications):
    a = await handle.notify_accept(data)
    return a

@app.post("/notify_reject")
async def notify_reject(data:model.Notifications):
    a = await handle.notify_reject(data)
    return a

# @app.post("/notify_message")
# async def notify_message(data:model.Notifications):
#     a = await handle.notify_message(data)
#     return a

@app.get("/get_notifications/{user_id}")
async def get_notifications(user_id: int):
    a = await handle.get_notifications(user_id)
    return a

@app.post("/sellproduct")
async def products(file: UploadFile = File(...), data: str = Form(...)):
    # print("Hello")
    # print(data)
    a = await handle.products(file, data) 
    return None

# @app.post("/upload_product_images")
# async def upload_file(file: model.ProductImage):
#     print(file.pid)
#     await handle.upload(file)
#     return {"message": "File uploaded successfully and processed."}

@app.post("/wishlist")
async def add_wishlist(data:model.Wishlist):
    a = await handle.add_wishlist(data)
    return a

@app.post("/remove_wishlist")
async def remove_wishlist(data:model.Wishlist):
    a = await handle.remove_wishlist(data)
    return a

@app.get("/get_wishlist/{user_id}")
async def get_wishlist(user_id: int):
    a = await handle.get_wishlist(user_id)
    return a

@app.post("/transactions")
async def transactions(data:model.Transactions):
    a = await handle.transactions(data)
    return a

@app.get("/get_transactions/{user_id}")
async def get_transactions(user_id: int):
    a = await handle.get_transactions(user_id)
    return a

@app.post("/search")
async def search(data:model.Search):
    print(data)
    a = await handle.search(data)
    return a

@app.post("/edit_profile")
async def edit_profile(file: UploadFile = File(...), data: str = Form(...)):
    await handle.edit_profile(file, data)
    return {"message": "File uploaded successfully and processed."}

@app.post("/edit_name")
async def edit_name(data: model.EditProfile):
    await handle.edit_name(data)
    return True

@app.post("/edit_products")
async def edit_products(file: UploadFile = File(...), data: str = Form(...)):
    await handle.edit_products(file, data)
    return {"message": "File uploaded successsfully and processed."}

@app.post("/edit_product_details")
async def edit_product_details(data: model.Product):
    await handle.edit_product_details(data)
    return True

@app.post("/report")
async def report(data:model.Report):
    a = await handle.report_user(data)
    return a

@app.get("/view_profile")
async def view_profile(user_id: int):
    a = await handle.view_profile(user_id)
    return a


@app.get("/get_products")
async def get_products():
    a = await handle.get_products()
    return a

@app.get("/get_specific_product/{product_id}")
async def get_specific_product(product_id: int):
    a = await handle.get_specific_product(product_id)
    return a
# view profile 
# view all products
# view specific product



@app.get("/on_sale/{user_id}")
async def products_on_sale(user_id: int):
    a = await handle.products_on_sale(user_id)
    return a

@app.delete("/remove_product/{product_id}")
async def remove_product(product_id: int):
    a = await handle.remove_product(product_id)
    return a

@app.get("/request_count/{product_id}/{buyer_id}")
async def get_request_count(product_id: int, buyer_id: int):
    a = await handle.get_request_count(product_id, buyer_id)
    return a
# just checking


# @app.post("/fun")
# async def fun(data:model.Fun):
#     a = await handle.fun(data)
#     return a

# @app.get("/searching")
# async def searching(query: str):
#     a = await handle.searching(query)
#     return a





# backend/main.py


# # Store all active websocket connections
# active_connections = []
# # Store conversation history
# conversation_history = {}

# # WebSocket endpoint
# @app.websocket("/chat/{user_id}")
# async def chat(websocket: WebSocket, user_id: str):
#     await websocket.accept()
#     active_connections.append((user_id, websocket))

#     try:
#         while True:
#             message = await websocket.receive_text()
#             await handle_message(message, user_id)
#     except Exception:
#         active_connections.remove((user_id, websocket))

# async def handle_message(message: str, sender_id: str):
#     # Parse message data
#     data = json.loads(message)
#     if data['type'] == 'message':
#         receiver = data['receiver']
#         # Store message in conversation history
#         if receiver in conversation_history:
#             conversation_history[receiver].append({
#                 'sender': sender_id,
#                 'content': data['content']
#             })
#         else:
#             conversation_history[receiver] = [{
#                 'sender': sender_id,
#                 'content': data['content']
#             }]
#         # Send message to the receiver if online
#         for user_id, connection in active_connections:
#             if user_id == receiver:
#                 await connection.send_text(data['content'])
#     elif data['type'] == 'history':
#         receiver = data['user']
#         # Send conversation history to the sender
#         if receiver in conversation_history:
#             history = conversation_history[receiver]
#             for message in history:
#                 await sender_websocket.send_text(message['content'])

# # @app.get("/users", response_model=List[str])
# # async def get_users():
# #     return list(conversation_history.keys())


# @app.get("/users/{user_id}", response_model=List[str])
# async def get_user_interactions(user_id: str):
#     interacting_users = set()
#     for receiver, messages in conversation_history.items():
#         for message in messages:
#             if message['sender'] == user_id:
#                 interacting_users.add(receiver)
#             elif receiver == user_id:
#                 interacting_users.add(message['sender'])
#     return list(interacting_users)


# active_connections = []
# conversation_history = {}

# @app.websocket("/chat/{user_id}")
# async def chat(websocket: WebSocket, user_id: str):
#     await websocket.accept()
#     active_connections.append((user_id, websocket))

#     try:
#         while True:
#             message = await websocket.receive_text()
#             await handle_message(message, user_id, websocket)
#     except Exception:
#         active_connections.remove((user_id, websocket))

# async def handle_message(message: str, sender_id: str, websocket: WebSocket):
#     data = json.loads(message)
#     if data['type'] == 'message':
#         receiver = data['receiver']
#         if receiver in conversation_history:
#             conversation_history[receiver].append({
#                 'sender': sender_id,
#                 'content': data['content']
#             })
#         else:
#             conversation_history[receiver] = [{
#                 'sender': sender_id,
#                 'content': data['content']
#             }]
#         for user_id, connection in active_connections:
#             if user_id == receiver:
#                 await connection[1].send_text(data['content'])
#     elif data['type'] == 'history':
#         receiver = data['user']
#         if receiver in conversation_history:
#             history = conversation_history[receiver]
#             for message in history:
#                 await websocket.send_text(message['content'])

# @app.get("/users/{user_id}", response_model=List[str])
# async def get_user_interactions(user_id: str):
#     interacting_users = set()
#     for receiver, messages in conversation_history.items():
#         for message in messages:
#             if message['sender'] == user_id:
#                 interacting_users.add(receiver)
#             elif receiver == user_id:
#                 interacting_users.add(message['sender'])
#     return list(interacting_users)


# main.py

# Store user connections
connections: List[WebSocket] = []

# WebSocket endpoint for chat
@app.websocket("/chat/{seller_id}/{buyer_id}")
async def chat_endpoint(websocket: WebSocket, seller_id: int, buyer_id: int):
    await websocket.accept()
    connections.append(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            # Broadcast message to all connected clients
            for connection in connections:
                await connection.send_text(data)
    except Exception as e:
        print(e)
        connections.remove(websocket)
