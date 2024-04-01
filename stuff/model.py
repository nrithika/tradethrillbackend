from pydantic import BaseModel
from fastapi import UploadFile
from typing import Optional,Union

# class User(BaseModel):
#     user_id:int
#     hashed_password:str

# class User_For_Registration(User):
#     name:str
#     email:str
    # confirm_password:str

class User_For_Registration(BaseModel):
    user_id:int
    name:str
    email:str
    hashed_password:str

class OTP(BaseModel):
    user_id:int
    otp:int

class ForgotPassword(BaseModel):
    user_id:int
    new_password:str
    # confirm_password:str
    # otp:int

class EditProfile(BaseModel):
    user_id:int
    name: str
    # photo:str

class Product(BaseModel):
    product_id:int
    sell_price:int
    cost_price:int
    title:str
    usage:int
    description:str
    # tags:str

# class ProductImage(BaseModel):
#     pid: int
#     Image: Optional[UploadFile]

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
    
class Report(BaseModel):
    product_id: int
    reporter_id: int
    # reported_id: int

class Notification(BaseModel):
    pid: int
    # seller_id: int
    buyer_id: int

class Notifications(Notification):
    seller_id: int












# just checking
# class Fun(BaseModel):
#     # product_id: int
#     title: str
#     description: str