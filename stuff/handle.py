from stuff import model
from stuff import database
from fastapi import HTTPException
from fastapi import UploadFile, File, Form
from typing import List
from datetime import datetime

from PIL import Image
from io import BytesIO

import bcrypt

import base64

import json

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

async def handle_register(data:model.User_For_Registration):
    conn,cursor=database.make_db()
    cursor.execute("SELECT COUNT(*) FROM reports WHERE reported_id = %s", (data.user_id,))
    num_reports = cursor.fetchone()[0]
    if num_reports >= 7:
        raise HTTPException(status_code=403, detail="User access restricted due to reports")
    otp = random.randrange(100000, 999999, 1)
    try:
        check_query = f"SELECT * FROM users WHERE user_id = '{data.user_id}'"
        cursor.execute(check_query)
        result = cursor.fetchone()
        if result is None:
            try:
                send_otp_email(data.email, otp)
            except Exception as e:
                raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
            query = f"""insert into users values('{data.user_id}', '{data.email}', '{data.hashed_password}', '{data.name}', '{otp}', FALSE)"""
            print(query)
            cursor.execute(query)
            pic_query = f"""insert into user_images values('{data.user_id}', NULL)"""
            cursor.execute(pic_query)
            conn.commit()
        else:
            verified_query = f"""SELECT verified FROM users WHERE user_id = '{data.user_id}'"""
            cursor.execute(verified_query)
            results = cursor.fetchall()
            verified = results[0][0]
            if not verified:
                try:
                    send_otp_email(data.email, otp)
                except Exception as e:
                    #error in sending otp
                    raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
                update_query = f"""update users set otp = {otp} where user_id = '{data.user_id}'"""
                cursor.execute(update_query)
                conn.commit()
            else:
                print("You've already registered")
                if result:  # User already exists
                    raise HTTPException(status_code=400, detail="User already registered")
    
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
    
    # if data.new_password != data.confirm_password:
        # raise HTTPException(status_code=400, detail="Passwords do not match")
    
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
        delete_query = f"""delete from change_password where user_id = '{data.user_id}'"""
        cursor.execute(delete_query)
        query = f"""insert into change_password values('{data.user_id}', '{data.new_password}', '{otp}')"""
        cursor.execute(query)
        conn.commit()
        return data
    # except Exception as e:
    #     #error in reseting password
    #     conn.rollback()  # Rollback any pending changes
    #     print(e)
    #     raise HTTPException(status_code=500, detail="Internal server error. Please try again later")
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
#     query = f"""
# select user_id, email, name, photo, verified from users where user_id = '{user_id}'
# """
    query = f"""
    SELECT u.user_id, u.email, u.name, ui.pic as photo, u.verified, u.hashed_password
    FROM users u 
    JOIN user_images ui ON u.user_id = ui.user_id
    WHERE u.user_id = '{user_id}'
    """
    conn, cursor = database.make_db()
    cursor.execute(query)
    result = cursor.fetchone()
    image_query = f"SELECT pic FROM user_images WHERE user_id = '{user_id}'"
    cursor.execute(image_query)
    image_result = cursor.fetchone()
    if image_result:
        image = image_result[0]
    else:
        image = None
    if image:
        image_file = f"{os.getcwd()}/stuff/file_buffer/{user_id}.png"
        # with open(image_file, "rb") as img_file:
        #     img_data = img_file.read()
        #     # Encode the image data as base64
        #     base64_img = base64.b64encode(img_data).decode()
        with open(image_file, "wb") as file:
            file.write(image)
        with open(image_file, "rb") as f:
            img_data = f.read()
            base64_image_data = base64.b64encode(img_data).decode()
    else:
        base64_image_data = None
    # results = results[0]
    if result:
        data = {
            "user_id": result[0],
            "email": result[1],
            "name": result[2],
            "photo": base64_image_data,
            "verified": result[4],
            "hashed_password": result[5]
        }
    if image:
        os.remove(image_file)
    return data


async def get_request_count(product_id: int, buyer_id: int):
    print("hello")
    conn, cursor = database.make_db()
    query = f"""SELECT COUNT(*) FROM notifications
                WHERE pid = {product_id} AND from_user = {buyer_id}"""
    print("query done")
    cursor.execute(query)
    result = cursor.fetchone()
    print(result[0])
    conn.close()
    if result:
        print("reached")
        return {"count": result[0]}

    else:
        print("else reached")
        return {"count": 0}

async def notify_request(data:model.Notification):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    seller_id_query = f"""select seller_id from products where product_id = '{data.pid}'"""
    cursor.execute(seller_id_query)
    result = cursor.fetchone()
    seller_id = result[0]
    if seller_id == data.buyer_id:
        raise HTTPException(status_code=400, detail="You cannot request your own product")
    query = f"""INSERT INTO notifications VALUES ('{data.buyer_id}', '{seller_id}', '{time}', 0, {data.pid})"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def notify_accept(data:model.Notifications):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    query = f"""INSERT INTO notifications VALUES ('{data.seller_id}', '{data.buyer_id}', '{time}', 1, {data.pid})"""
    cursor.execute(query)
    sold_query = f"""insert into notifications values ('{data.buyer_id}', '{data.seller_id}', '{time}', 3, {data.pid})"""
    cursor.execute(sold_query)
    update_query = f"""
update products set status = TRUE where product_id = {data.pid}
"""
    cursor.execute(update_query)
    delete_query = f"""delete from notifications where from_user = {data.buyer_id} and to_user = {data.seller_id} and type = 0 and pid = {data.pid}"""
    cursor.execute(delete_query)

    find_other = f"""select from_user from notifications where to_user = {data.seller_id} and pid = {data.pid} and type = 0"""
    cursor.execute(find_other)
    results = cursor.fetchall()


    for result in results:
        buyer_id = result[0]
        insert_query = f"""insert into notifications values('{data.seller_id}', '{buyer_id}', '{time}', 2, '{data.pid}')"""
        cursor.execute(insert_query)
    
    delete_other = f"""delete from notifications where to_user = {data.seller_id} and pid = {data.pid} and type = 0"""
    cursor.execute(delete_other)

    conn.commit()
    conn.close()

    transactions_data = model.Transactions(product_id=data.pid, seller_id=data.seller_id, buyer_id=data.buyer_id)
    result = await transactions(transactions_data)


    return result

async def notify_reject(data:model.Notifications):
    conn, cursor = database.make_db()
    time = datetime.today().strftime('%Y-%m-%d')
    delete_query = f"""delete from notifications where from_user={data.buyer_id} and to_user = {data.seller_id} and type = 0 and pid = {data.pid}"""
    cursor.execute(delete_query)
    query = f"""INSERT INTO notifications VALUES ('{data.seller_id}', '{data.buyer_id}', '{time}', 2, {data.pid})"""
    cursor.execute(query)
    conn.commit()
    conn.close()

# async def notify_message(data:model.Notifications):
#     conn, cursor = database.make_db()
#     time = datetime.today().strftime('%Y-%m-%d')
#     query = f"""INSERT INTO notifications VALUES ('{data.seller_id}', '{data.buyer_id}', '{time}', 4, {data.pid})"""
#     cursor.execute(query)
#     conn.commit()
#     conn.close()

async def get_notifications(user_id: int):
    # this function is to get the notifications from the user live and assist the login function
    """
    notifications will have time, from_user, to_user, type
    type = enum{REQUEST TO BUY, ACCEPTED TO SELL, REJECTED TO SELL, SOME MESSAGED YOU}
    It returns an array of objects of tuple of the order (<from_user_name>, <type_of_notification>, <time>)
    0 request to buy
    1 accepted to sell.. other person will get so and so seller sold the product to you
    2 rejected to sell
    3 sold the product.. you will get so and so buyer bought the product
    """
    query = f"""
select from_name, from_id, type, time, pid, product_title from 
(select u.name as from_name, n.from_user as from_id, n.time as time, n.pid as pid, n.type as type, 
    n.to_user as to_user, p.title as product_title 
    from notifications as n 
    inner join users as u on u.user_id = n.from_user
    inner join products as p on p.product_id = n.pid ) as sub
where to_user = {user_id}
"""
    print(query)
    # query = f"""
    # SELECT u.name AS from_name, n.from_user AS from_id, n.time AS time, n.pid AS pid, n.type AS type,
    #        n.to_user AS to_user, p.title AS product_title
    # FROM notifications AS n
    # INNER JOIN users AS u ON u.user_id = n.from_user
    # INNER JOIN products AS p ON p.product_id = n.pid
    # WHERE to_user = {user_id}
    # """
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
            "pid": result[4],
            "product_title": result[5]
        }
        
        fulldata.append(data)
    # print(fulldata)
    return fulldata

async def login(user_id: int):
    conn, cursor = database.make_db()
    report_query = f"""SELECT COUNT(*) FROM reports WHERE reported_id = {user_id}"""
    cursor.execute(report_query)
    num_reports = cursor.fetchone()[0]
    if num_reports >= 7:
        raise HTTPException(status_code=403, detail="User access restricted due to reports")
    
    query = f"SELECT verified FROM users WHERE user_id='{user_id}'"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        verified = result[0]
        if verified:
            # add code for sending the user data, notifications
            empty_data = {}
            user_info = await get_user_info(user_id)
            user_notifications = await get_notifications(user_id)
            # data = { **empty_data, **user_info, "notifications": user_notifications,  "message":"success"}
            data = { **empty_data, **user_info, "notifications": user_notifications,  "message":"success"}
            # print (data)
            return data
        else:
            conn.close()
            print("User is not verified")
            raise HTTPException(status_code=403, detail="User is not verified")
            return False
        
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    # return False

async def products(file: UploadFile = File(...), data: str = Form(...)):
    conn, cursor = database.make_db()
    cursor.execute("SELECT MAX(product_id) FROM products")
    result = cursor.fetchone()
    if result and result[0]:
        product_id = int(result[0]) + 1
    else:
        product_id = 100000
    # print(data)
    got = json.loads(data)
    # print(got)
    # print(file.filename)
    # cwd = os.getcwd()
    path = f"/tmp/{product_id}.png"
    print(path)
    # image_data = await file.read()
    # print(image_data)
    with open(path, "wb") as f:
        f.write(await file.read())
    print("Reached here")
    query = f"""insert into products values ('{product_id}', '{got['seller_id']}', '{got['sell_price']}', '{got['cost_price']}', '{got['title']}', 0, '{got['usage']}', '{got['description']}', '{got['tags']}', FALSE)"""
    cursor.execute(query)
    conn.commit()
    # print(image_data)
    upload_query = f"""insert into product_images values ('{product_id}', pg_read_binary_file('{path}')::bytea)"""
    print(upload_query)
    # image_query = f"""INSERT INTO product_images (product_id, image) VALUES (%s, %s)"""
    cursor.execute(upload_query)
    conn.commit()
    conn.close()
    os.remove(path)
    print("file removed")
    return {
        "pid": product_id 
    }

async def update_interests(product_id: int):
    conn, cursor = database.make_db()
    query = f"""UPDATE products SET nf_interests = (SELECT COUNT(*) FROM wishlist WHERE wishlist.product_id = '{product_id}') WHERE product_id = '{product_id}'"""
    cursor.execute(query)
    conn.commit()
    conn.close()

async def add_wishlist(data:model.Wishlist):
    conn, cursor = database.make_db()
    print(data)
    try:
        product_existing = f"SELECT * FROM wishlist WHERE product_id = '{data.product_id}' AND buyer_id = '{data.buyer_id}'"
        cursor.execute(product_existing)
        existing_result = cursor.fetchall()

        if existing_result:
            print("Product already exists")
            raise HTTPException(status_code=400, detail="Product already exists")
            return None
        
        else:
            print(existing_result)
            query = f"SELECT seller_id FROM products WHERE product_id = '{data.product_id}'"
            cursor.execute(query)
            result = cursor.fetchone()

            if result:
                seller_id = result[0]
                if seller_id == data.buyer_id:
                    print("You cannot add your own product to your wishlist")
                    raise HTTPException(status_code=400, detail="You cannot add your own product to your wishlist")
                    return None
                else:
                    insert_query = f"insert into wishlist values('{data.product_id}', '{seller_id}', '{data.buyer_id}')"
                    cursor.execute(insert_query)
                    conn.commit()

                    await update_interests(data.product_id)

                    return data
            
            else:
                raise HTTPException(status_code=404, detail="Product not found")
    
    # except Exception as e:
    #     # conn.rollback()
    #     print("Jere is the error")
        # raise HTTPException(status_code=500, detail= "Internal server error. Please try again later")
    finally:
        conn.close()

async def remove_wishlist(data: model.Wishlist):
    conn, cursor = database.make_db()
    query = f"""delete from wishlist where buyer_id = {data.buyer_id} and product_id = {data.product_id}"""
    cursor.execute(query)
    conn.commit()
    await update_interests(data.product_id)
    conn.close()

async def get_wishlist(user_id: int):
    conn, cursor = database.make_db()
    query = f"""SELECT products.product_id, products.seller_id, products.sell_price, products.cost_price, 
                products.title, products.usage, products.description, users.name FROM 
                (select * from wishlist where buyer_id = {user_id}) 
                as w inner join products on w.product_id = products.product_id
                inner join users on products.seller_id = users.user_id
                where products.status != true"""
    cursor.execute(query)
    results = cursor.fetchall()
    return_value = []
    for result in results:
        data = {
            "product_id":result[0],
            "seller_id":result[1],
            "sell_price":result[2],
            "cost_price":result[3],
            "title":result[4],
            "usage":result[5],
            "description":result[6],
            "name":result[7]
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
    # sold_query = f"""SELECT buyer_id, cost, title, description FROM transactions WHERE seller_id = {user_id}"""
    sold_query = f"""
    SELECT t.buyer_id, t.cost, t.title, t.description, u.name
    FROM transactions AS t
    JOIN users AS u ON t.buyer_id = u.user_id
    WHERE t.seller_id = {user_id}
    """
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
            "description": result[3],
            "name": result[4]
        }
        return_value["sold_results"].append(data)
    # bought_query = f"""SELECT seller_id, cost, title, description FROM transactions WHERE buyer_id = {user_id}"""
    bought_query = f"""
    SELECT t.seller_id, t.cost, t.title, t.description, u.name
    FROM transactions AS t
    JOIN users AS u ON t.seller_id = u.user_id
    WHERE t.buyer_id = {user_id}
    """
    cursor.execute(bought_query)
    bought_results = cursor.fetchall()
    for result in bought_results:
        data = {
            "seller_id": result[0],
            "cost": result[1],
            "title": result[2],
            "description": result[3],
            "name": result[4]
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
WHERE p.status != true
) as s
WHERE s.title ILIKE '{regex_word}' or s.description ILIKE '{regex_word}'
"""
        cursor.execute(search_query)
        search_results = cursor.fetchall()
        for result in search_results:
            product_id = result[0]
            image_query = f"SELECT image FROM product_images WHERE product_id = '{product_id}'"
            cursor.execute(image_query)
            image_result = cursor.fetchone()
            if image_result:
                image = image_result[0]
            else:
                image = None
            if image:
                image_file = f"{os.getcwd()}/stuff/file_buffer/{product_id}.png"
                # with open(image_file, "rb") as img_file:
                #     img_data = img_file.read()
                #     # Encode the image data as base64
                #     base64_img = base64.b64encode(img_data).decode()
                with open(image_file, "wb") as file:
                    file.write(image)
                with open(image_file, "rb") as f:
                  img_data = f.read()
                  base64_image_data = base64.b64encode(img_data).decode()
            else:
                base64_img = None
            data = {
                "product_id":result[0],
                "product_title":result[1],
                "sell_price":result[2],
                "seller_name":result[3],
                "seller_email":result[4],
                # "product_image":result[5]
                "product_image":base64_image_data
            }
            if data in return_value:
                continue
            return_value.append(data)
            os.remove(image_file)
    conn.close()

    # print(return_value)
    return return_value

# async def edit_profile(data: model.EditProfile):
#     conn, cursor = database.make_db()
#     user_id = data.user_id
#     files = []
#     files.append(data.photo)
#     try:
#         for file in files:
#             curr_dir = os.getcwd()
#             await file.save(f"{curr_dir}/stuff/file_buffer/{file.filename}")
#             print("File added")
#             file_path = f"{curr_dir}/stuff/file_buffer/{file.filename}"
#             query = f"""UPDATE users SET photo = pg_read_binary_file('{file_path}')::bytea where user_id = {user_id}"""
#             cursor.execute(query)
#             os.remove(file_path)
#             print("File removed")
#         conn.commit()
#     except Exception as e:
#         print(f"Could not upload file")
#         print(e)
#     name_query = f"""UPDATE users SET name = {data.name} where user_id = {user_id}"""
#     cursor.execute(name_query)
#     conn.commit()
#     conn.close()

async def edit_profile(file: UploadFile = File(...), data: str = Form(...)):
    conn, cursor = database.make_db()
    got = json.loads(data)
    path = f"/tmp/{got['user_id']}.png"
    print(path)
    with open(path, "wb") as f:
        f.write(await file.read())
    update_query = f"""update users set name = '{got['name']}' where user_id = {got['user_id']}"""    
    cursor.execute(update_query)
    conn.commit()

    upload_query = f"""update user_images set pic = pg_read_binary_file('{path}')::bytea where user_id = {got['user_id']}"""
    cursor.execute(upload_query)
    conn.commit()
    conn.close()
    os.remove(path)
    print("file removed")
    
    return None

async def edit_name(data: model.EditProfile):
    conn, cursor = database.make_db()
    update_query = f"""update users set name = '{data.name}' where user_id = {data.user_id}"""
    cursor.execute(update_query)
    conn.commit()
    conn.close()

async def edit_products(file: UploadFile = File(...), data: str = Form(...)):
    conn,cursor = database.make_db()
    got = json.loads(data)
    path = f"/tmp/{got['product_id']}.png"
    print(path)
    with open (path, "wb") as f:
        f.write(await file.read())
    update_query = f"""update products set 
                    sell_price = '{got['sell_price']}', 
                    cost_price = '{got['cost_price']}', 
                    title = '{got['title']}', 
                    usage = '{got['usage']}',
                    description = '{got['description']}'
                    where product_id = '{got['product_id']}'"""
    cursor.execute(update_query)
    conn.commit()
    
    upload_query = f"""update product_images set image = pg_read_binary_file('{path}')::bytea where product_id = {got['product_id']}"""
    cursor.execute(upload_query)
    conn.commit()
    conn.close()
    os.remove(path)
    print("file removed")

    return None

async def edit_product_details(data: model.Product):
    conn, cursor = database.make_db()
    update_query = f"""update products set 
                    sell_price = '{data.sell_price}',
                    cost_price = '{data.cost_price}', 
                    title = '{data.title}', 
                    usage = '{data.usage}',
                    description = '{data.description}'
                    where product_id = '{data.product_id}'"""
    cursor.execute(update_query)
    conn.commit()
    conn.close()

async def report_user(data: model.Report):
    conn, cursor = database.make_db()
    query = f"SELECT seller_id FROM products WHERE product_id = {data.product_id}"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        reported_id = result[0]
    if data.reporter_id == reported_id:
        print("You can't report yourself")
        raise HTTPException(status_code=400, detail="Reporter and reported user cannot be the same")
    else:
        cursor.execute("SELECT COUNT(*) FROM reports WHERE reporter_id = %s AND reported_id = %s",
                    (data.reporter_id, reported_id))
        if cursor.fetchone()[0] > 0:
            print("User has already been reported")
            raise HTTPException(status_code=400, detail="User has already been reported by this reporter")
        else:
            cursor.execute("INSERT INTO reports (reporter_id, reported_id) VALUES (%s, %s)",
                        (data.reporter_id, reported_id))
            conn.commit()

            return {"message": "User reported successfully"}

async def view_profile(user_id: int):
    conn, cursor = database.make_db()
    # query = f"""SELECT name, email FROM users WHERE user_id = {user_id}"""
    query = f"""
        SELECT u.name, u.email, ui.pic
        FROM users u
        LEFT JOIN user_images ui ON u.user_id = ui.user_id
        WHERE u.user_id = {user_id}
    """
    cursor.execute(query)
    conn.close()
    result = cursor.fetchone()
    image_query = f"SELECT pic FROM user_images WHERE user_id = '{user_id}'"
    cursor.execute(image_query)
    image_result = cursor.fetchone()
    if image_result:
        image = image_result[0]
    else:
        image = None
    if image:
        image_file = f"{os.getcwd()}/stuff/file_buffer/{user_id}.png"
        # with open(image_file, "rb") as img_file:
        #     img_data = img_file.read()
        #     # Encode the image data as base64
        #     base64_img = base64.b64encode(img_data).decode()
        with open(image_file, "wb") as file:
            file.write(image)
        with open(image_file, "rb") as f:
            img_data = f.read()
            base64_image_data = base64.b64encode(img_data).decode()
    else:
        base64_img = None
    if result:
        # name, email, photo = result
        data = {
            "name": result[0],
            "email": result[1],
            "pic": base64_image_data
        }    
        os.remove(image_file)
        return data

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
    WHERE
        p.status = FALSE
        AND u.user_id NOT IN (
            SELECT reported_id 
            FROM reports 
            GROUP BY reported_id 
            HAVING COUNT(*) >= 7
        )
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    if results:
        products = []
        for row in results:
            product_id = row[0]
            image_query = f"SELECT image FROM product_images WHERE product_id = '{product_id}'"
            cursor.execute(image_query)
            result = cursor.fetchone()
            if result:
                image = result[0]
            else:
                image = None
            if image:
                image_file = f"{os.getcwd()}/stuff/file_buffer/{product_id}.png"
                # with open(image_file, "rb") as img_file:
                #     img_data = img_file.read()
                #     # Encode the image data as base64
                #     base64_img = base64.b64encode(img_data).decode()
                with open(image_file, "wb") as file:
                    file.write(image)
                with open(image_file, "rb") as f:
                    img_data = f.read()
                    base64_image_data = base64.b64encode(img_data).decode()
            else:
                base64_img = None
            product = {
                "product_id": row[0],
                "product_title": row[1],
                "sell_price": row[2],
                "seller_name": row[3],
                "seller_email": row[4],
                # "product_image": base64_img
                "product_image": base64_image_data
            }
            products.append(product)
            os.remove(image_file)
        conn.close()
        # print(products)
        return products
    else:
        return []

async def get_specific_product(product_id: int):
    conn, cursor = database.make_db()
    # query = f"""SELECT p.seller_id, u.name as seller_name, u.email as seller_email,
    # p.sell_price, p.cost_price, p.title, p.usage, p.description, i.image
    # FROM products p 
    # INNER JOIN users u ON p.seller_id = u.user_id
    # LEFT JOIN product_images i ON p.product_id = i.product_id
    # WHERE product_id = {product_id} """
    query = f"""
    SELECT 
        p.seller_id,
        p.sell_price,
        p.cost_price,
        p.title,
        p.usage,
        p.description,
        u.name AS seller_name,
        u.email AS seller_email,
        i.image AS product_image
    FROM 
        products p
    JOIN 
        users u ON p.seller_id = u.user_id
    LEFT JOIN 
        product_images i ON p.product_id = i.product_id
    WHERE
        p.product_id = {product_id}
    """
    cursor.execute(query)
    result = cursor.fetchone()
    image_query = f"SELECT image FROM product_images WHERE product_id = '{product_id}'"
    cursor.execute(image_query)
    image_result = cursor.fetchone()
    if image_result:
        image = image_result[0]
    else:
        image = None
    if image:
        image_file = f"{os.getcwd()}/stuff/file_buffer/{product_id}.png"
        # with open(image_file, "rb") as img_file:
        #     img_data = img_file.read()
        #     # Encode the image data as base64
        #     base64_img = base64.b64encode(img_data).decode()
        with open(image_file, "wb") as file:
            file.write(image)
        with open(image_file, "rb") as f:
            img_data = f.read()
            base64_image_data = base64.b64encode(img_data).decode()
    else:
        base64_img = None
    if result:
        data = {
            "seller_id":result[0],
            "sell_price":result[1],
            "cost_price":result[2],
            "title":result[3],
            "usage":result[4],
            "description":result[5],
            "seller_name":result[6],
            "seller_email":result[7],
            "product_image": base64_image_data
        }
    os.remove(image_file)
    return data

async def products_on_sale(user_id: int):
    conn, cursor = database.make_db()
    query = f"""SELECT product_id, sell_price, cost_price, title, nf_interests, usage, description, tags FROM products WHERE seller_id = {user_id} and status = FALSE"""
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
                "description": row[6],
                "tags": row[7]
            }
            products.append(product)
        return products
    else:
        return []

async def remove_product(product_id: int):
    conn,cursor = database.make_db()
    delete_query = f"""delete from products where product_id = {product_id}"""
    cursor.execute(delete_query)
    photo_query = f"""delete from product_images where product_id = {product_id}"""
    cursor.execute(photo_query)
    conn.commit()
    conn.close()








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
