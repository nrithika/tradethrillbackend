from stuff import model
from stuff import database
from fastapi import HTTPException
from fastapi import UploadFile, File
from typing import List

import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os 
from dotenv import load_dotenv

load_dotenv()

def send_otp_email(receiver_email, otp):
    sender_email =  os.getenv("OTP_SENDER_EMAIL") # Enter your email address
    sender_password = os.getenv("OTP_SENDER_PASSWORD") # Enter your email password
    # print(sender_email + " " + sender_password)

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Your One Time Password (OTP)"
    body = f"Welcome to TradeThrill. Your OTP to start your experience with us is: {otp}"
    message.attach(MIMEText(body, 'plain'))
    # print("Reached")

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

async def handle_register(data:model.User_For_Registration):
    # print(data)
    if data.hashed_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    email = f"{data.user_id}@iitk.ac.in"
    otp = random.randrange(100000, 999999, 1)
    send_otp_email(email, otp)
    conn,cursor=database.make_db()
    check_query = f"SELECT * FROM users WHERE user_id = '{data.user_id}'"
    cursor.execute(check_query)
    result = cursor.fetchall()
    if result == []:
        query = f"""insert into users values('{data.user_id}', '{email}', '{data.hashed_password}', '{data.name}', NULL, '{otp}', FALSE)"""
        cursor.execute(query)
        conn.commit()
        return data
    
    return False

async def verify_otp(data:model.OTP):
    conn, cursor = database.make_db()
    query = f"SELECT otp FROM users WHERE user_id = '{data.user_id}'"
    cursor.execute(query)
    result = cursor.fetchone()

    if result and result[0] == data.otp:
        update_query = f"UPDATE users SET verified = TRUE WHERE user_id = '{data.user_id}'"
        cursor.execute(update_query)
        conn.commit()  
        conn.close()
        return True
    
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    # conn.close()

    # return False

def otp_email_forgotpass(receiver_email, otp):
    sender_email =  os.getenv("OTP_SENDER_EMAIL") # Enter your email address
    sender_password = os.getenv("OTP_SENDER_PASSWORD") # Enter your email password
    # print(sender_email + " " + sender_password)

    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = "Your One Time Password (OTP)"
    body = f"Your OTP to change your password is: {otp}"
    message.attach(MIMEText(body, 'plain'))
    # print("Reached")

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

async def forgot_password(data:model.ForgotPassword):
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    conn, cursor = database.make_db()
    verify_user_query = f"SELECT verified FROM users WHERE user_id = '{data.user_id}'"
    cursor.execute(verify_user_query)
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    elif not user[0]:
        raise HTTPException(status_code=400, detail="User is not verified")
    
    email = f"{data.user_id}@iitk.ac.in"
    otp = random.randrange(100000, 999999, 1)
    otp_email_forgotpass(email, otp)
    
    query = f"""insert into change_password values('{data.user_id}', '{data.new_password}', '{otp}')"""
    cursor.execute(query)
    conn.commit()
    return data

async def new_otp(data:model.OTP):
    verify_query = f"SELECT otp FROM change_password WHERE user_id = '{data.user_id}'"

    conn, cursor = database.make_db()
    cursor.execute(verify_query)
    result = cursor.fetchone()
    if result and result[0] == data.otp:
        query = f"SELECT new_password FROM change_password WHERE user_id = '{data.user_id}'"
        cursor.execute(query)
        new_password = cursor.fetchone()
        update_query = f"UPDATE users SET hashed_password = '{new_password[0]}' WHERE user_id = '{data.user_id}'"
        cursor.execute(update_query)
        # conn.commit()
        # conn.close()

        delete_query = f"DELETE FROM change_password WHERE user_id = '{data.user_id}'"
        cursor.execute(delete_query)
        # conn.commit()
        # conn.close()

        conn.commit()
        conn.close()
        return True
    
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # check_query = f"SELECT * FROM users WHERE user_id = '{data.user_id}'"
    # cursor.execute(check_query)
    # result = cursor.fetchall()
    
async def login(data:model.User):
    conn, cursor = database.make_db()
    query = f"SELECT hashed_password, verified FROM users WHERE user_id='{data.user_id}'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        hashed_password, verified = result
        if verified and hashed_password == data.hashed_password:
            conn.close()
            return("Login successful!")
        else:
            conn.close()
            raise HTTPException(status_code=401, detail="Incorrect password or unverified account")
        
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # return False

# IMAGES_DIR = "images/products"
# os.makedirs(IMAGES_DIR, exist_ok=True)

# async def save_uploaded_file(file: UploadFile) -> str:
#     file_path = os.path.join(IMAGES_DIR, file.filename)
#     with open(file_path, "wb") as buffer:
#         buffer.write(await file.read())
#     return file_path

# async def insert_product_images(product_id: int, image_urls: List[str]):
#     conn, cursor = database.make_db()

#     try:
#         for image_url in image_urls:
#             await cursor.execute("INSERT INTO product_images (product_id, image_url) VALUES ($1, $2)", product_id, image_url)
#             conn.commit()
#     finally:
#         await conn.close()


async def products(data:model.Product, files: List[UploadFile] = File(...)):
    conn, cursor = database.make_db()
    cursor.execute("SELECT MAX(product_id) FROM products")
    result = cursor.fetchone()
    if result and result[0]:
        product_id = int(result[0]) + 1
    else:
        product_id = 100000
    
    query = f"""insert into products values ('{product_id}', '{data.seller_id}', '{data.sell_price}', '{data.cost_price}', '{data.title}', NULL, '{data.usage}', '{data.description}', '{data.tags}')"""
    cursor.execute(query)

    # image_urls = []
    # for file in files:
    #     file_path = await save_uploaded_file(file)
    #     image_urls.append(file_path)
        
    # await insert_product_images(product_id, image_urls)
    conn.commit()
    conn.close()
    return data

async def update_interests(product_id):
    conn, cursor = database.make_db()
    query = f"""UPDATE products SET nf_interests = (SELECT COUNT(*) FROM wishlist WHERE wishlist.product_id = '{product_id}') WHERE product_id = '{product_id}'"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def wishlist(data:model.Wishlist):
    conn, cursor = database.make_db()
    query = f"SELECT seller_id FROM products WHERE product_id = '{data.product_id}'"
    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        seller_id = result[0]
        insert_query = f"insert into wishlist values('{data.product_id}', '{seller_id}', '{data.buyer_id}')"
        cursor.execute(insert_query)
        conn.commit()

        await update_interests(data.product_id)

        return data
    
    return False

async def transactions(data:model.Transactions):
    conn, cursor = database.make_db()
    query = f"SELECT sell_price, title, description FROM products WHERE product_id = '{data.product_id}'"
    cursor.execute(query)
    product_data = cursor.fetchone()

    if product_data:
        sell_price, title, description = product_data
        insert_query = f"INSERT INTO transactions (product_id, seller_id, buyer_id, cost, title, description) VALUES (%s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (data.product_id, data.seller_id, data.buyer_id, sell_price, title, description))
        conn.commit()
        conn.close()
        return data
    


# async def edit_profile(data:model.EditProfile):
#     conn, cursor = database.make_db()
    
async def search(data: model.Search):           #do the code where spaces arent included
                                                #one idea is when you take the input and in the initial phase itself
                                                #convert title and description into a str with no spaces
                                                #but then the issue would be where the checking number of words exists 
                                                #may be then check number of words that are together                            

    conn, cursor = database.make_db()

    words = data.query.split()

    title_conditions = " + ".join([f"CASE WHEN title ILIKE '%%{word}%%' THEN 1 ELSE 0 END" for word in words])
    description_conditions = " + ".join([f"CASE WHEN description ILIKE '%%{word}%%' THEN 1 ELSE 0 END" for word in words])

    search_query = f"""
        SELECT 
            p.*,
            u.name AS seller_username,
            u.email AS seller_email
        FROM 
            (SELECT 
                p.*,
                ({title_conditions}) AS title_score,
                ({description_conditions}) AS description_score
            FROM 
                products p
            WHERE 
                ({title_conditions}) > 0 OR ({description_conditions}) > 0) AS p
        JOIN
            users u ON p.seller_id = u.user_id
        ORDER BY 
            (p.title_score + p.description_score) DESC
    """
    cursor.execute(search_query)
    search_results = cursor.fetchall()

    conn.close()
    return search_results

