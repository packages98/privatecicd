from flask import Flask, redirect, render_template, request, session, jsonify, flash, url_for, send_file
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo import MongoClient
import certifi  # SSL 인증서 검증을 위한 모듈
import gridfs
from redis import Redis
from io import BytesIO
from bson import ObjectId
import socket


client = MongoClient('mongodb://root:VMware1!@MongoDBCluster:27017')
db = client['test']  # 사용할 데이터베이스 선택
users_collection = db['users']  # 사용할 컬렉션 선택
production = db['production']
cart_collection = db['cart']
pay_history = db['pay_history']

fs = gridfs.GridFS(db) # gridfs를 이용하여 image 저장할 콜렉션 지정


app = Flask(__name__)
app.config["SECRET_KEY"] = "ABCD"


# 레디스 사용
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_REDIS"] = Redis(
    host='clustercfg.lss.epfrnm.apn2.cache.amazonaws.com:6379',  # Private Subnet에 있는 Redis 엔드포인트
    port=6379,  # Redis 기본 포트
    decode_responses=False
)

'''
# 파일시스템 사용
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)
'''

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods = ["GET"])
def index():
        if request.method == "GET":
            products = production.find()
            products_list = []
            for product in products:
                products_list.append({
                    "id": product.get("_id"),
                    "name": product.get("name"),
                    "price": product.get("price"),
                    "image_id": product.get("image_id"),
                    "image_name": product.get("image_name")
                })
            return render_template("main.html", products = products_list)
        


@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":
            user_name = request.form.get("user_name")
            user_id = request.form.get("user_id")
            user_passoword1 = request.form.get("user_password_1")
            user_passoword2 = request.form.get("user_password_2")
            customer_type = request.form.get('customer_type')
 

            if not user_name or not user_id or not user_passoword1 or not user_passoword2:
                 flash("비어있는 칸이 존재합니다.")
                 return redirect("/register")
            elif user_passoword1 != user_passoword2:
                 flash("비밀번호가 다릅니다.")
                 return redirect ("/register")
            elif users_collection.find_one({"user_id": user_id}):
                flash("중복 ID가 존재합니다.")
                return redirect("/register")
            else:
                hash_password = generate_password_hash(user_passoword1)
                users_collection.insert_one({"username": user_name, "user_id": user_id, "password": hash_password, "customer_type": customer_type, "credit": 0, "rank": "브론즈"})
                flash("회원가입이 완료되었습니다.")
                return redirect("/")


     
@app.route("/login", methods = ["GET"])
def login():
     if request.method == "GET":
         return render_template("login.html")

@app.route("/login_check", methods = ["POST"])
def login_check():
    if request.method == "POST":
        user_id = request.form.get("username")
        user_password = request.form.get("password")

        if not user_id or not user_password:
            flash("잘못된 비밀번호 및 아이디 입니다.")
            return redirect('/login')
        else:
            user = users_collection.find_one({'username': user_id})
            if not user:
                flash("잘못된 비밀번호 및 아이디 입니다.")
                return redirect('/login')
            elif not (check_password_hash(user["password"], user_password)):
                flash("잘못된 비밀번호 및 아이디 입니다.")
                return redirect('/login')
            else:
                flash("로그인 성공!")
                session["user_info"] = {"user_id": str(user["_id"]), "username": user["username"], "customer_type": user["customer_type"]}
                return redirect('/')



@app.route("/logout", methods = ["GET"])
def logout():
    session.clear()
    flash("로그아웃 완료!")
    return redirect("/")


#/image/ObjectID로 들어가면 이미지가 출력됨
@app.route('/image/<image_id>')
def images(image_id):
    try:
        image = fs.get(ObjectId(image_id))
        img_bytes = image.read()
        return send_file(BytesIO(img_bytes), mimetype='image/jpeg')
    except Exception as e:
        return str(e)
    

@app.route('/cart', methods = ["GET"])
def cart():
    if request.method == "GET":
        user_id = session["user_info"]["user_id"]
        carts = cart_collection.find({"user_id": user_id})
        carts_list = [cart for cart in carts]
        total_price = 0
        for cart in carts_list:
            product = production.find_one({"_id": ObjectId(cart["product_id"])})
            if product:
                total_price += int(product["price"]) * int(cart["quantity"])

        return render_template("cart.html", carts_list = carts_list, total_price = total_price)


@app.route('/product/<product_id>', methods=["GET", "POST"])
def product(product_id):
    if request.method == "GET":
        try:
            object_id = ObjectId(product_id)
        except Exception as e:
            return str(e)
        
        product_detail = production.find_one({"_id": object_id})
        return render_template("product.html", product_detail=product_detail)
    
    if request.method == "POST":
        if 'user_info' not in session:
            flash('먼저 로그인을 해주세요')
            return redirect('/login')
        else:
            try:
                quantity = int(request.form.get("quantity"))
                object_id = ObjectId(product_id)
                product = production.find_one({"_id": object_id})
                
                if product:
                    stock = int(product["stock"])
                    if quantity > stock:
                        flash('재고가 부족합니다.')
                        return redirect(f'/product/{product_id}')
                    
                    cart_collection.insert_one({
                            "user_id": session["user_info"]["user_id"],
                            "product_id": str(product["_id"]),
                            "quantity": quantity,
                            "name": product["name"],
                            "price": product["price"],
                            "image_id": product["image_id"]
                            })
                    production.update_one({"_id": object_id}, {"$set": {"stock": stock - quantity}})
                    flash('상품을 담았습니다')
                    return redirect("/")
                else:
                    flash('상품을 찾을 수 없습니다.')
                    return redirect("/")
            except Exception as e:
                flash(str(e))
                return redirect(f'/product/{product_id}')


@app.route("/remove_item", methods = ["POST"])
def remove_item():
    if request.method == "POST":
        item_id = request.form.get("item_id")
        cart_item = cart_collection.find_one({"_id": ObjectId(item_id), "user_id": session["user_info"]["user_id"]})
        product_id = cart_item["product_id"]
        quantity = cart_item["quantity"]
        print(item_id, product_id, quantity)
        cart_collection.delete_one({"_id": ObjectId(item_id), "user_id": session["user_info"]["user_id"]})
        production.update_one({"_id": ObjectId(product_id)}, {"$inc": {"stock": quantity}})
        flash("항목이 성공적으로 삭제되었습니다.")
        return redirect('/cart')


@app.route("/register_product", methods=["GET", "POST"])
def register_product():
    if request.method == "GET":
        return render_template("register_product.html")
    if request.method == "POST":
        img = request.files.get("image")
        name = request.form.get("name")
        detail = request.form.get("explanation")
        origin = request.form.get("origin")
        stock = request.form.get("stock")
        price = request.form.get("price")

        # 필수 필드가 비어 있는지 확인
        if not img or not name or not detail or not origin or not stock or not price:
            flash('모든 필드를 채워주세요.')
            return redirect("/register_product")

        filename = img.filename
        file_id = fs.put(img, filename=filename)

        production.insert_one({
            'name': name,
            'detail': detail,
            'origin': origin,
            'stock': stock,
            'price': price,
            'image_id': file_id,
            'image_name': filename
        })

        flash('등록 완료')
        return redirect("/register_product")

@app.route("/pay", methods = ["POST"])
def pay():
    if request.method == "POST":
        return redirect ("/")
    
@app.route("/mypage", methods = ["GET"])
def mypage():
    return render_template("mypage.html")
    



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='8080')






'''
# mongodb 이미지 리스트 가져와서 get_image.html 파일로 보냄





# 파일이름을 찾아 리스트 가져옴
@app.route('/find_name',methods=["GET"])
def find_name():
    # 이미지 파일 리스트 가져오기
    images = fs.find()
    filenames = [image.filename for image in images]
    print(filenames)
    return render_template('get_images_filename.html', filenames=filenames)


    @app.route('/image_filename/<filename>')
def image(filename):
    try:
        image = fs.find_one({'filename': filename})
        if image:
            img_bytes = image.read()
            return send_file(BytesIO(img_bytes), mimetype='image/jpeg')
        else:
            return "Image not found", 404
    except Exception as e:
        return str(e)

        





@app.route('/find', methods=["GET"])
def find():
    # 이미지 파일 리스트 가져오기
    images = fs.find()
    image_ids = [str(image._id) for image in images]
    return render_template('main.html', image_ids=image_ids)



'''


# CICD 테스트 주석 (온프레미스)