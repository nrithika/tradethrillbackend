from fastapi import FastAPI
from stuff import model
from stuff import handle
# from fastapi import FastAPI, Depends, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
# from tasks import tasks, models

app = FastAPI()

origins = ["http://localhost:3000", "http://localhost:3000/"]       #write the server of frontend in your laptop

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

@app.post("/login")
async def login(data:model.User):
    a = await handle.login(data)
    return a

# @app.get("/get_user_info")
# async def get_user_info(user_id: int):
#     a = await handle.get_user_info(user_id)
#     return a

@app.post("/notify_request")
async def notify_request(data:model.Notifications):
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

@app.post("/notify_message")
async def notify_message(data:model.Notifications):
    a = await handle.notify_message(data)
    return a

@app.get("/get_notifications")
async def get_notifications(user_id: int):
    a = await handle.get_notifications(user_id)
    return a

@app.post("/products")
async def products(data:model.Product):
    a = await handle.products(data)
    return a

@app.post("/upload_product_images")
async def upload_file(file: model.ProductImage):
    await handle.upload(file)
    return {"message": "File uploaded successfully and processed."}

@app.post("/wishlist")
async def wishlist(data:model.Wishlist):
    a = await handle.wishlist(data)
    return a

@app.get("/get_wishlist")
async def get_wishlist(user_id: int):
    a = await handle.get_wishlist(user_id)
    return a

@app.post("/transactions")
async def transactions(data:model.Transactions):
    a = await handle.transactions(data)
    return a

@app.get("/get_transactions")
async def get_transactions(user_id: int):
    a = await handle.get_transactions(user_id)
    return a

@app.post("/search")
async def search(data:model.Search):
    a = await handle.search(data)
    return a

@app.post("/edit_profile")
async def edit_profile(file: model.EditProfile):
    await handle.edit_profile(file)
    return {"message": "File uploaded successfully and processed."}

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

@app.get("/get_specific_product")
async def get_specific_product(product_id: int):
    a = await handle.get_specific_product(product_id)
    return a
# view profile 
# view all products
# view specific product









# just checking


@app.post("/fun")
async def fun(data:model.Fun):
    a = await handle.fun(data)
    return a

# @app.get("/searching")
# async def searching(query: str):
#     a = await handle.searching(query)
#     return a