from pydantic import BaseModel

class User(BaseModel):
    user_id:int
    hashed_password:str

class User_For_Registration(User):
    name:str
    confirm_password:str

class OTP(BaseModel):
    user_id:int
    otp:int

class ForgotPassword(BaseModel):
    user_id:int
    new_password:str
    confirm_password:str
    # otp:int

class EditProfile(BaseModel):
    user_id:int
    photo:str

class Product(BaseModel):
    seller_id:int
    sell_price:int
    cost_price:int
    title:str
    usage:int
    description:str
    tags:str

class Wishlist(BaseModel):
    product_id:int
    buyer_id:int

class Transactions(BaseModel):
    product_id:int
    seller_id:int
    buyer_id:int
    # cost:int
    # title:str
    # description:str

class Search(BaseModel):
    query: str

# class ProductImage(BaseModel):
#     product_id: int
#     image_url: str