from fastapi import FastAPI
from stuff import model
from stuff import handle
from fastapi import FastAPI, UploadFile, File

app = FastAPI()


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

@app.get("/login")
async def login(data:model.User):
    a = await handle.login(data)
    return a

@app.post("/products")
async def products(data:model.Product):
    a = await handle.products(data)
    return a

# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     await handle.save_uploaded_file(file)
    
#     return {"message": "File uploaded successfully and processed."}

@app.post("/wishlist")
async def wishlist(data:model.Wishlist):
    a = await handle.wishlist(data)
    return a

@app.post("/transactions")
async def transactions(data:model.Transactions):
    a = await handle.transactions(data)
    return a

@app.get("/search")
async def search(data:model.Search):
    a = await handle.search(data)
    return a

