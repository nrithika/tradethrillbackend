from stuff import model
from stuff import database
from fastapi import HTTPException
from fastapi import UploadFile, File
from typing import List
from datetime import datetime

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

    # server = smtplib.SMTP('smtp.cc.iitk.ac.in', 465)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

# def send_otp_email(receiver_email, otp):
#     try:
#         # Setting up server
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
        
#         sender_email =  os.getenv("OTP_SENDER_EMAIL") # Enter your email address
#         sender_password = os.getenv("OTP_SENDER_PASSWORD") # Enter your email password
#         server.login(sender_email, sender_password)
        
#         # Constructing email message
#         body = f"Your OTP is: {otp}"
#         subject = "OTP"
#         message = f"Subject: {subject}\n\n{body}"
        
#         # Sending email
#         server.sendmail(sender_email, receiver_email, message)
#         print("OTP has been sent to", receiver_email)
        
#         # Quit server
#         server.quit()
#     except Exception as e:
#         print("An error occurred while sending OTP:", str(e))

async def handle_register(data:model.User_For_Registration):
    # print(data)
    conn,cursor=database.make_db()
    cursor.execute("SELECT COUNT(*) FROM reports WHERE reported_id = %s", (data.user_id,))
    num_reports = cursor.fetchone()[0]
    if num_reports >= 7:
        raise HTTPException(status_code=403, detail="User access restricted due to reports")
    
    if data.hashed_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    # email = f"{data.user_id}@iitk.ac.in"
    otp = random.randrange(100000, 999999, 1)
    try:
        send_otp_email(data.email, otp)
    except Exception as e:
        #error in sending otp
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
    
    try:
        check_query = f"SELECT * FROM users WHERE user_id = '{data.user_id}'"
        cursor.execute(check_query)
        result = cursor.fetchall()
        if result == []:
            query = f"""insert into users values('{data.user_id}', '{data.email}', '{data.hashed_password}', '{data.name}', NULL, '{otp}', FALSE)"""
            cursor.execute(query)
            conn.commit()
            return data
    except Exception as e:
        #Error in registering user
        conn.rollback()  # Rollback any pending changes
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
    finally:
        conn.close()
    
    return False

async def verify_otp(data:model.OTP):
    conn, cursor = database.make_db()
    try:
        query = f"SELECT otp FROM users WHERE user_id = '{data.user_id}'"
        cursor.execute(query)
        result = cursor.fetchone()

        if result and result[0] == data.otp:
            update_query = f"UPDATE users SET verified = TRUE WHERE user_id = '{data.user_id}'"
            cursor.execute(update_query)
            conn.commit()  
            conn.close()
            return {
                "message":"success"
            }
        else:
            return{
                "message":"Wrong OTP"
            }
    except Exception as e:
        #error in verifying otp
        conn.rollback()  # Rollback any pending changes
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
    finally:
        conn.close()
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

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        #error in sending otp
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")

async def forgot_password(data:model.ForgotPassword):
    conn, cursor = database.make_db()

    cursor.execute("SELECT COUNT(*) FROM reports WHERE reported_id = %s", (data.user_id,))
    num_reports = cursor.fetchone()[0]
    if num_reports >= 7:
        raise HTTPException(status_code=403, detail="User access restricted due to reports")
    
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    try:
        verify_user_query = f"SELECT verified FROM users WHERE user_id = '{data.user_id}'"
        cursor.execute(verify_user_query)
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        elif not user[0]:
            raise HTTPException(status_code=400, detail="User is not verified")

        get_email = f"SELECT email FROM users WHERE user_id = '{data.user_id}'"
        cursor.execute(get_email)
        email = cursor.fetchone()
        email = email[0]
        otp = random.randrange(100000, 999999, 1)
        otp_email_forgotpass(email, otp)

        query = f"""insert into change_password values('{data.user_id}', '{data.new_password}', '{otp}')"""
        cursor.execute(query)
        conn.commit()
        return data
    except Exception as e:
        #error in reseting password
        conn.rollback()  # Rollback any pending changes
        print(e)
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
    finally:
        conn.close()

async def new_otp(data:model.OTP):
    conn, cursor = database.make_db()
    
    try:
        verify_query = f"SELECT otp FROM change_password WHERE user_id = '{data.user_id}'"
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
    # except Exception as e:
    #     #error in verifying otp
    #     conn.rollback()  # Rollback any pending changes
    #     raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
    finally:
        conn.close()  # Ensure connection is closed

    # check_query = f"SELECT * FROM users WHERE user_id = '{data.user_id}'"
    # cursor.execute(check_query)
    # result = cursor.fetchall()
    
async def get_user_info(user_id: int):
    # function for getting the data of the user and it has been made as a sub function so as to assist the login function
    query = f"""
select user_id, email, name, photo, verified from users where user_id = '{user_id}'
"""
    conn, cursor = database.make_db()
    cursor.execute(query)
    results = cursor.fetchall()
    results = results[0]
    data = {
        "user_id": user_id,
        "email": results[1],
        "name": results[2],
        "photo": results[3],
        "verified": results[4]
    }
    return data

async def notify_request(data:model.Notifications):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    query = f"""INSERT INTO notifications VAlUES ('{data.buyer_id}', '{data.seller_id}', '{time}', 0, {data.pid})"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def notify_accept(data:model.Notifications):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    query = f"""INSERT INTO notifications VAlUES ('{data.seller_id}', '{data.buyer_id}', '{time}', 1, {data.pid})"""
    cursor.execute(query)
    query = f"""
update products set status = TRUE where product_id = {data.pid}
"""
    cursor.execute(query)
    transactions({
        "product_id": data.pid,
        "seller_id":data.seller_id,
        "buyer_id":data.buyer_id
    })
    conn.commit()
    conn.close()

async def notify_reject(data:model.Notifications):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    query = f"""delete from notifications where from from_user={data.seller_id} and to_user = {data.buyer_id} and type = 0"""
    cursor.execute(query)
    query = f"""INSERT INTO notifications VAlUES ('{data.seller_id}', '{data.buyer_id}', '{time}', 2, {data.pid})"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def notify_message(data:model.Notifications):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    query = f"""INSERT INTO notifications VAlUES ('{data.seller_id}', '{data.buyer_id}', '{time}', 3, {data.pid})"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def get_notifications(user_id: int):
    # this function is to get the notifications from the user live and assist the login function
    """
    notifications will have time, from_user, to_user, type
    type = enum{REQUEST TO BUY, ACCEPTED TO SELL, REJECTED TO SELL, SOME MESSAGED YOU}
    It returns an array of objects of tuple of the order (<from_user_name>, <type_of_notification>, <time>)
    0 request to buy
    1 accepted to sell
    2 rejected to sell
    3 someone messaged
    """
    query = f"""
select from_name, from_id, type, time, pid from (select u.name as from_name, n.from_user as from_id, n.time as time, n.pid as pid, n.type as type, 
    n.to_user as to_user  from notifications as n inner join users as u on u.user_id =n.from_user ) where to_user = {user_id}
"""
    conn, cursor = database.make_db()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    fulldata = []
    for result in results:
        data = {
            "from_name":result[0],
            "from_id": result[1],            
            "type":result[2],
            "time":result[3],
            "pid": result[4]
        }
        
        fulldata.append(data)
    # print(fulldata)
    return fulldata

# async def get_notifications(user_id: int):
    """
    notifications will have time, from_user, to_user, type, and product_title
    type = enum{REQUEST TO BUY, ACCEPTED TO SELL, REJECTED TO SELL, SOME MESSAGED YOU}
    It returns an array of objects of tuple of the order (<from_user_name>, <type_of_notification>, <time>, <product_title>)
    0 request to buy
    1 accepted to sell
    2 rejected to sell
    3 someone messaged
    """
    query = f"""
    SELECT u.name AS from_name, n.from_user AS from_id, n.time AS time, n.pid AS pid, n.type AS type,
           n.to_user AS to_user, p.title AS product_title
    FROM notifications AS n
    INNER JOIN users AS u ON u.user_id = n.from_user
    INNER JOIN products AS p ON p.product_id = n.pid
    WHERE to_user = {user_id}
    """
    conn, cursor = database.make_db()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    
    fulldata = []
    for result in results:
        data = {
            "from_name": result[0],
            "from_id": result[1],
            "type": result[2],
            "time": result[3],
            "pid": result[4],
            "product_title": result[5]
        }
        fulldata.append(data)
    
    return fulldata


async def login(data:model.User):
    conn, cursor = database.make_db()
    cursor.execute("SELECT COUNT(*) FROM reports WHERE reported_id = %s", (data.user_id,))
    num_reports = cursor.fetchone()[0]
    if num_reports >= 7:
        raise HTTPException(status_code=403, detail="User access restricted due to reports")
    
    query = f"SELECT hashed_password, verified FROM users WHERE user_id='{data.user_id}'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        hashed_password, verified = result
        if verified and hashed_password == data.hashed_password:
            conn.close()
            # add code for sending the user data, notifications
            empty_data = {}
            user_info = await get_user_info(data.user_id)
            user_notifications = await get_notifications(data.user_id)
            data = { **empty_data, **user_info, "notifications": user_notifications,  "message":"success"}
            # print (data)
            return data
        else:
            conn.close()
            raise HTTPException(status_code=401, detail="Incorrect password or unverified account")
            return False
        
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


async def products(data:model.Product, files: List[UploadFile] = File(...)):            #check the files code
    conn, cursor = database.make_db()
    cursor.execute("SELECT MAX(product_id) FROM products")
    result = cursor.fetchone()
    if result and result[0]:
        product_id = int(result[0]) + 1
    else:
        product_id = 100000
    
    query = f"""insert into products values ('{product_id}', '{data.seller_id}', '{data.sell_price}', '{data.cost_price}', '{data.title}', 0, '{data.usage}', '{data.description}', '{data.tags}')"""
    cursor.execute(query)

    # image_urls = []
    # for file in files:
    #     file_path = await save_uploaded_file(file)
    #     image_urls.append(file_path)
        
    # await insert_product_images(product_id, image_urls)
    conn.commit()
    conn.close()
    return {
        "pid": product_id 
    }

async def update_interests(product_id):
    conn, cursor = database.make_db()
    query = f"""UPDATE products SET nf_interests = (SELECT COUNT(*) FROM wishlist WHERE wishlist.product_id = '{product_id}') WHERE product_id = '{product_id}'"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def wishlist(data:model.Wishlist):
    conn, cursor = database.make_db()
    try:
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
        
        else:
            raise HTTPException(status_code=404, detail="Product not found")
    
    except Exception as e:
        #Error in adding to wishlist
        conn.rollback()
        raise HTTPException(status_code=500, detail= "Unternal server error. Please try again later")
    finally:
        conn.close()

async def get_wishlist(user_id: int):
    conn, cursor = database.make_db()
    query = f"""SELECT products.seller_id, products.sell_price, products.cost_price, 
                products.title, products.usage, products.description, users.name FROM 
                (select * from wishlist where buyer_id = {user_id}) 
                as w inner join products on w.product_id = products.product_id
                inner join users on products.seller_id = users.user_id"""
    cursor.execute(query)
    results = cursor.fetchall()
    return_value = []
    for result in results:
        data = {
            "seller_id":result[0],
            "sell_price":result[1],
            "cost_price":result[2],
            "title":result[3],
            "usage":result[4],
            "description":result[5],
            "name":result[6]
        }
        return_value.append(data)
    return return_value

async def transactions(data:model.Transactions):
    conn, cursor = database.make_db()
    try:
        query = f"SELECT sell_price, title, description FROM products WHERE product_id = '{data.product_id}'"
        cursor.execute(query)
        product_data = cursor.fetchone()

        if product_data:
            sell_price, title, description = product_data
            insert_query = f"INSERT INTO transactions (product_id, seller_id, buyer_id, cost, title, description) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (data.product_id, data.seller_id, data.buyer_id, sell_price, title, description))
            conn.commit()
            return data
        else:
            raise HTTPException(status_code=404, detail="Product not found")
        
    except Exception as e:
        #Error in loading transcation
        conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error. PLease try again later")
    finally:
        conn.close()
  
async def get_transactions(user_id: int):
    conn, cursor = database.make_db()
    sold_query = f"""SELECT buyer_id, cost, title, description FROM transactions WHERE seller_id = {user_id}"""
    cursor.execute(sold_query)
    sold_results = cursor.fetchall()
    return_value = {
        "sold_results": [],
        "bought_results": []
    }
    for result in sold_results:
        data = {
            "buyer_id": result[0],
            "cost": result[1],
            "title": result[2],
            "description": result[3]
        }
        return_value["sold_results"].append(data)
    bought_query = f"""SELECT seller_id, cost, title, description FROM transactions WHERE buyer_id = {user_id}"""
    cursor.execute(bought_query)
    bought_results = cursor.fetchall()
    for result in bought_results:
        data = {
            "seller_id": result[0],
            "cost": result[1],
            "title": result[2],
            "description": result[3]
        }
        return_value["bought_results"].append(data)
    return return_value

async def search(data: model.Search):           #do the code where spaces arent included
                                                #one idea is when you take the input and in the initial phase itself
                                                #convert title and description into a str with no spaces
                                                #but then the issue would be where the checking number of words exists 
                                                #may be then check number of words that are together                            

    conn, cursor = database.make_db()

    words = data.query.split()
    return_value = []
    for word in words:
        regex_word = f"%{word}%"
        search_query = f"""
SELECT s.product_id as product_id,
s.title as product_title,
s.sell_price as sell_price,
s.seller_name as seller_name,
s.seller_email as seller_email,
s.product_image as product_image 
FROM 
(SELECT p.product_id as product_id,
p.title as title,
p.description as description,
p.sell_price as sell_price,
i.image as product_image,
u.name as seller_name,
u.email as seller_email
FROM products as p
LEFT JOIN product_images as i on p.product_id = i.product_id
JOIN users as u on p.seller_id = u.user_id
) as s
WHERE s.title ILIKE '{regex_word}' or s.description ILIKE '{regex_word}'
"""
        cursor.execute(search_query)
        search_results = cursor.fetchall()
        for result in search_results:
            data = {
                "product_id":result[0],
                "product_title":result[1],
                "sell_price":result[2],
                "seller_name":result[3],
                "seller_email":result[4],
                "product_image":result[5]
            }
            if data in return_value:
                continue
            return_value.append(data)
    conn.close()
    print(return_value)
    return return_value

async def upload(data: model.ProductImage):
    # save the files locally
    # save the files in db
    conn, cursor = database.make_db()
    pid = data.pid
    files = []
    files.append(data.Image)
    try:
        for file in files:
            curr_dir = os.getcwd()
            file_path = f"{curr_dir}/stuff/file_buffer/{file.filename}"
            await file.save(file_path)
            print("File added")
            with open(file_path, 'rb') as f:
                file_data = f.read()
            query = f"""INSERT INTO product_images VALUES ({pid}, pg_read_binary_file('{file_path}')::bytea)"""
            cursor.execute(query)
            os.remove(file_path)
            print("File removed")
        conn.commit()
    except Exception as e:
        print(f"Could not upload file")

# async def upload(data: model.ProductImage):
#     conn, cursor = database.make_db()
#     pid = data.pid
#     files = []
#     files.append(data.Image1)
#     try:
#         for file in files:
#             curr_dir = os.getcwd()
#             file_bytes = await file.read()  # Read file content as bytes
#             file_path = f"{curr_dir}/stuff/file_buffer/{file.filename}"
#             with open(file_path, "wb") as f:
#                 f.write(file_bytes)  # Write file content as bytes
#             print("File added")
#             query = f"""INSERT INTO product_images VALUES (%s, %s)"""
#             cursor.execute(query, (pid, file_bytes))  # Insert binary data directly
#             print("File inserted into database")
#         conn.commit()
#     except Exception as e:
#         print(f"Could not upload file: {e}")
#     finally:
#         conn.close()


async def edit_profile(data: model.EditProfile):
    conn, cursor = database.make_db()
    user_id = data.user_id
    files = []
    files.append(data.photo)
    try:
        for file in files:
            curr_dir = os.getcwd()
            await file.save(f"{curr_dir}/stuff/file_buffer/{file.filename}")
            print("File added")
            file_path = f"{curr_dir}/stuff/file_buffer/{file.filename}"
            query = f"""UPDATE users SET photo = pg_read_binary_file('{file_path}')::bytea where user_id = {user_id}"""
            cursor.execute(query)
            os.remove(file_path)
            print("File removed")
        conn.commit()
    except Exception as e:
        print(f"Could not upload file")
        print(e)
    name_query = f"""UPDATE users SET name = {data.name} where user_id = {user_id}"""
    cursor.execute(name_query)
    conn.commit()
    conn.close()

async def report_user(data: model.Report):
    conn, cursor = database.make_db()
    query = f"SELECT seller_id FROM products WHERE product_id = {data.product_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        reported_id = result[0]
    cursor.execute("SELECT COUNT(*) FROM reports WHERE reporter_id = %s AND reported_id = %s",
                   (data.reporter_id, reported_id))
    if cursor.fetchone()[0] > 0:
        raise HTTPException(status_code=400, detail="User has already been reported by this reporter")

    cursor.execute("INSERT INTO reports (reporter_id, reported_id) VALUES (%s, %s)",
                   (data.reporter_id, reported_id))
    conn.commit()

    return {"message": "User reported successfully"}

async def view_profile(user_id: int):
    conn, cursor = database.make_db()
    query = f"""SELECT name, email, photo FROM users WHERE user_id = {user_id}"""
    cursor.execute(query)
    conn.close()
    result = cursor.fetchone()
    if result:
        name, email, photo = result
        return {"name": name, "email": email, "photo": photo}
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
async def get_products():
    conn, cursor = database.make_db()
    query = """
    SELECT 
        p.product_id,
        p.title AS product_title,
        p.sell_price,
        u.name AS seller_name,
        u.email AS seller_email,
        i.image AS product_image
    FROM 
        products p
    JOIN 
        users u ON p.seller_id = u.user_id
    LEFT JOIN 
        product_images i ON p.product_id = i.product_id
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    if results:
        products = []
        for row in results:
            product = {
                "product_id": row[0],
                "product_title": row[1],
                "sell_price": row[2],
                "seller_name": row[3],
                "seller_email": row[4],
                "product_image": row[5]
            }
            products.append(product)
        return products
    else:
        return []

async def get_specific_product(product_id: int):
    conn, cursor = database.make_db()
    query = f"""SELECT p.seller_id, u.name as seller_name, u.email as seller_email,
    p.sell_price, p.cost_price, p.title, p.usage, p.description
    FROM products p 
    INNER JOIN users u ON p.seller_id = u.user_id
    WHERE product_id = {product_id} """
    cursor.execute(query)
    result = cursor.fetchone()
    data = {
        "seller_id":result[0],
        "seller_name":result[1],
        "seller_email":result[2],
        "sell_price":result[3],
        "cost_price":result[4],
        "title":result[5],
        "usage":result[6],
        "description":result[7]
    }
    return data

async def products_on_sale(user_id: int):
    conn, cursor = database.make_db()
    query = f"""SELECT product_id, sell_price, cost_price, title, nf_interests, usage, description, tags FROM products WHERE seller_id = {user_id}"""
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    if results:
        products = []
        for row in results:
            product = {
                "product_id": row[0],
                "sell_price": row[1],
                "cost_price": row[2],
                "title": row[3],
                "nf_interests": row[4],
                "usage": row[5],
                "description": row[6]
                # "tags": row[7]
            }
            products.append(product)
        return products
    else:
        return []










# just checking
# async def fun(data:model.Product):
#     conn, cursor = database.make_db()
#     cursor.execute("SELECT MAX(product_id) FROM fun")
#     result = cursor.fetchone()
#     if result and result[0]:
#         product_id = int(result[0]) + 1
#     else:
#         product_id = 100000
    

#     concat = data.title.replace(" ", "").lower() + data.description.replace(" ", "").lower()

#     query = f"""insert into fun values ('{product_id}', '{concat}')"""
#     cursor.execute(query)

#     conn.commit()
#     conn.close()
#     return data
