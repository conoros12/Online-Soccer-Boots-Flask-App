from flask import Flask, render_template, session, redirect, url_for, g, request, flash
from database import get_db, close_db
from forms import RegistrationForm, LoginForm, AddBootForm, ReviewForm, EditBootForm, CheckoutForm
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os

app = Flask(__name__)
app.teardown_appcontext(close_db)
app.config["SECRET_KEY"] = "this-is-my-secret-key"
app.config["SESSION_TYPE"] = "filesystem"
app.config["UPLOAD_FOLDER"] = "static/images"
Session(app)

"""Login for admin is username: admin  password: 123"""


@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user != 'admin':
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view






@app.route("/")
def index():
    return render_template("index.html", title='Conors boots')

@app.route("/boots")
def boots():
    db = get_db()
    boots = db.execute("""SELECT *
                       FROM boots;""").fetchall()
    return render_template("boots.html", boots=boots)


@app.route("/boot/<int:boot_id>", methods=["GET", "POST"])
@login_required
def boot(boot_id):
    form = ReviewForm()
    db = get_db()
    boot = db.execute("""SELECT * FROM boots
                WHERE boot_id = ?;""", (boot_id, )).fetchone()
    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        db.execute("""INSERT INTO reviews (user_id, boot_id, rating, review)
                   VALUES (?, ?, ?, ?);""", (g.user, boot_id, rating, review))
        db.commit()
        get_db()
    reviews = db.execute("""SELECT * FROM reviews
                        WHERE boot_id = ?;""", (boot_id, )).fetchall()


    return render_template("boot.html", 
                           boot=boot, form=form, 
                           reviews=reviews)

@app.route("/cart")
@login_required
def cart():
    if "cart" not in session:
        
        session["cart"] = {}
        session.modified = True

    names = {}
    db = get_db()

    for boot_id in session["cart"]:
        boot = db.execute("""SELECT * FROM boots
                          WHERE boot_id = ?;""", (boot_id, )).fetchone()
        name = boot["boot_name"]
        names[boot_id] = name
    return render_template("cart.html", 
                           cart=session["cart"], names=names)


@app.route("/add_to_cart/<int:boot_id>")
@login_required
def add_to_cart(boot_id):
    if "cart" not in session:
        session["cart"] = {}
    if boot_id not in session["cart"]:
        session["cart"][boot_id] = 1
    else:
        session["cart"][boot_id] = session["cart"][boot_id] + 1
    session.modified = True
    return redirect( url_for("cart") )


@app.route("/remove_from_cart/<int:boot_id>/")
@login_required
def remove_from_cart(boot_id):
    if "cart" in session and boot_id in session["cart"]:
        if session["cart"][boot_id] > 1:
            session["cart"][boot_id] -= 1
        else:
            del session["cart"][boot_id]
        session.modified = True
    return redirect(url_for("cart"))
        



@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        clash = db.execute("""
                SELECT * FROM users
                WHERE user_id = ?;""", (user_id,)).fetchone()
        if clash is not None:
            form.user_id.errors.append("This user name is already taken!")
        else:
            db.execute("""
                INSERT INTO users (user_id, password)
                VALUES (?, ?);""",
                (user_id, generate_password_hash(password)))
            db.commit()
            return redirect( url_for("login") )
    return render_template("register.html",form=form)


@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_id = form.user_id.data
        password = form.password.data
        db = get_db()
        user_in_db = db.execute("""
            SELECT * FROM users
            WHERE user_id = ?;""", (user_id, )).fetchone()
        
        if user_in_db is None:
            form.user_id.errors.append("No such user name!")
        elif not check_password_hash(
                    user_in_db["password"], password):
            form.password.errors.append("Incorrect password!")
        else:
            session.clear()
            session["user_id"] = user_id
            session.modified = True
            next_page = request.args.get("next")
            if not next_page:
                next_page = url_for("index")
            return redirect(next_page)
    return render_template("login.html",form=form)

@app.route("/logout")
def logout():
    session.clear()
    session.modified = True
    return redirect( url_for("index") )

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    db = get_db()
    boots = db.execute("""SELECT * FROM boots
                       WHERE boot_name LIKE ? OR description LIKE ?;""", (f"%{query}%", f"%{query}%")).fetchall()
    return render_template("search_results.html", boots=boots, query=query)


@app.route("/add_boots", methods = ["GET", "POST"])
@admin_required
def add_boots():
    form = AddBootForm()
    if request.method == "POST":
        boot_name = form.boot_name.data
        price = form.price.data
        description = form.description.data
        image = form.image.data
        filename = image.filename
        image.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], filename))

        db = get_db()
        db.execute("""INSERT INTO boots (boot_name, price, description, image)
                   VALUES (?, ?, ?, ?);""", (boot_name, price, description, filename))
        db.commit()

        return redirect( url_for("boots") )
    
    return render_template("admin_add_boot.html", form=form)

@app.route("/delete_boot/<int:boot_id>")
@admin_required
def delete_boot(boot_id):
    db = get_db()
    db.execute("""DELETE FROM boots
               WHERE boot_id = ?;""", (boot_id, ))
    db.commit()
    return redirect( url_for("boots") )
    


@app.route("/edit_boot/<int:boot_id>", methods=["GET", "POST"])
@admin_required
def edit_boot(boot_id):
    form = EditBootForm()
    db = get_db()
   
    print(form.errors)
    if form.validate_on_submit():
        boot_name = form.boot_name.data
        price = form.price.data
        description = form.description.data
        

        db.execute("""UPDATE boots
                        SET boot_name = ?, price = ?, description = ?
                        WHERE boot_id = ?;""", (boot_name, price, description, boot_id))
        db.commit()
        return redirect( url_for("boots") )
        
    return render_template("admin_edit_boot.html", form=form, )

@app.route("/wishlist")
@login_required
def wishlist():
    db = get_db()
    wishlist = db.execute("""SELECT boots.* FROM wishlist
                          JOIN boots ON wishlist.boot_id = boots.boot_id
                          WHERE wishlist.user_id = ?;""",(g.user, )).fetchall()
    return render_template("wishlist.html", wishlist=wishlist)

@app.route("/add_to_wishlist/<int:boot_id>", methods=["GET", "POST"])
@login_required
def add_to_wishlist(boot_id):
    db = get_db()
    #Check for clash
    clash = db.execute("""SELECT * FROM wishlist
                        WHERE user_id = ? AND boot_id = ?;""",(g.user, boot_id)).fetchone()
    if clash is None:
        db.execute("""INSERT INTO wishlist (user_id, boot_id)
                    VALUES (?, ?);""", (g.user, boot_id))
        db.commit()
    return redirect(url_for("boot", boot_id=boot_id))



@app.route("/remove_from_wishlist/<int:boot_id>")
@login_required
def remove_from_wishlist(boot_id):
    db = get_db()
    db.execute("""DELETE FROM wishlist
               WHERE user_id = ? AND boot_id = ?;""", (g.user, boot_id))
    db.commit()
    return redirect(url_for("wishlist"))

@app.route("/delete_review/<int:boot_id>")
@admin_required
def delete_review(boot_id):
    db = get_db()
    db.execute("""DELETE FROM reviews
               WHERE user_id = ? AND boot_id = ?;""", (g.user, boot_id))
    db.commit()
    return redirect(url_for("boot", boot_id=boot_id))


@app.route("/order_confirmed")
@login_required
def order_confirmed():
    return render_template("order_confirmed.html")


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    db = get_db()
    cart = session.get("cart", {})



    form = CheckoutForm()
    boots = {}
    total_price = 0

    for boot_id, quantity in cart.items():
        boot = db.execute("""SELECT boot_id, boot_name, price
                          FROM boots 
                          WHERE boot_id = ?;""", (boot_id, )).fetchone()
        if boot:
            boots[boot_id] = {
                "name": boot["boot_name"],
                "price": boot["price"],
                "quantity": quantity,
            }
            total_price += boot["price"] * quantity

    if request.method == "POST":

        # Insert order into database
        order = db.execute(
            """INSERT INTO orders (user_id, total_cost) 
            VALUES (?, ?);""", (g.user, total_price))
        
        order_id = order.lastrowid
        db.commit()

        # Insert order items
        for boot_id, details in boots.items():
            db.execute(
                """INSERT INTO order_items (order_id, boot_id, quantity, price_per_unit) 
                VALUES (?, ?, ?, ?);""", (order_id, boot_id, details["quantity"], details["price"]))
        
        db.commit()
        session["cart"] = {}
        session.modified = True

        return redirect(url_for("order_confirmed"))

    return render_template("checkout.html", cart=cart, boots=boots,
                            total_price=total_price, form=form)


@app.route("/credits")
def credits():
    return render_template("credits.html")
     