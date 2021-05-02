import os
from dotenv import load_dotenv

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Load API Key from .env file
load_dotenv()

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQL to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    result = []
    total = 0

    # Getting the required records from the database
    rows = db.execute("SELECT share_name, SUM(share_amt) FROM transactions WHERE user_id = :user_id GROUP BY share_name;", user_id = session["user_id"])

    # Iterating over each row in returned query
    for row in rows:
        #Creating a dictionary object that contains all the values of one row
        resDict = dict()
        resDict["symbol"] = row["share_name"]

        # Looking up the symbol name using IEX API
        symDict = lookup(row["share_name"])

        resDict["shares"] = row["SUM(share_amt)"]
        resDict["name"] = symDict["name"]
        resDict["price"] = usd(symDict["price"])
        resDict["total"] = usd(row["SUM(share_amt)"] * symDict["price"])

        # Calculating the total amount of money that the user currently has in shares
        total += row["SUM(share_amt)"] * symDict["price"]

        result.append(resDict)

    # Adding the total cash that the user currently has by retrieving the current balance from the database
    row = db.execute("SELECT cash FROM users WHERE id = :uid;", uid = session["user_id"])
    cash = row[0]["cash"]
    resDict = {
        "symbol": 'CASH',
        "shares": '',
        "name": 'Cash Balance',
        "price": '',
        "total": usd(cash)
        }
    result.append(resDict)

    total += cash
    total = usd(total)

    return render_template("index.html", result=result, total=total)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # If user accesses page via GET
    if request.method == "GET":
        return render_template("buy.html")

    # If user accesses page via submitting the form (POST)
    else:
        # Check if symbol field is empty
        if not request.form.get("symbol"):
            return render_template("buy.html")

        # Check if shares is a positive integer
        shares = int(request.form.get("shares"))
        if shares <= 0:
            return render_template("buy.html")

        # Looking up the symbol name using IEX API
        symDict = lookup(request.form.get("symbol"))
        if not symDict:
            return apology("Invalid Symbol Name", 400)

        # Calculating the buy price
        buy_price = shares * symDict["price"]

        # Retrieves the amount of cash that the user currently has from the database
        row = db.execute("SELECT cash FROM users WHERE id = :user_id;", user_id=session["user_id"])
        cash = row[0]["cash"]

        # Checking if current balance is sufficient to buy the selected shares
        if cash < buy_price:
            return apology("Insufficient balance to buy selected shares", 400)

        # Inserting the transaction log into the database
        name = symDict["symbol"]
        price = symDict["price"]
        db.execute("INSERT INTO transactions (user_id, share_name, share_amt, share_price) VALUES (:uid, :name, :amt, :price);", uid=session["user_id"], name=name, amt=shares, price=price)

        # Updating the user's balance in the database
        balance = cash - buy_price
        db.execute("UPDATE users SET cash = :balance WHERE id = :user_id;", balance=balance, user_id=session["user_id"])

        return redirect("/")


@app.route("/changepwd", methods=["GET", "POST"])
@login_required
def changepwd():

    # If the user accesses the page via GET
    if request.method == "GET":
        return render_template("change.html")

    # If the user accesses the page via submitting the form (POST)
    else:

        # Checking if the username or password is empty
        if not request.form.get("old") or not request.form.get("new"):
            return render_template("change.html")

        # Checking if the passwords do not match
        if request.form.get("new") != request.form.get("confirm"):
            return render_template("change.html")

        # Checking if the length of the password is atleast 8 characters
        if len(request.form.get("new")) < 8:
            return render_template("change.html")

        # Retrieving the old password hash from the database
        row = db.execute("SELECT hash FROM users WHERE id = :uid;", uid = session["user_id"])
        old_hash = row[0]["hash"]

        # Checking if the old password hash matches with the given old password
        if not check_password_hash(old_hash, request.form.get("old")):
            return apology("Old passwords do not match", 403)

        # Generating a new password hash
        new_hash = generate_password_hash(request.form.get("new"))

        # Updating the password in the database
        db.execute("UPDATE users SET hash = :new_hash WHERE id = :uid", new_hash=new_hash, uid = session["user_id"])

        return redirect("/")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    result = []

    # Getting the required records from the database
    rows = db.execute("SELECT share_name, share_amt, share_price, time FROM transactions WHERE user_id = :uid ORDER BY time DESC;", uid=session["user_id"])

    # Iterating over all the rows returned by the query
    for row in rows:
        # Creating a dictionary object which holds all the data for one row
        resDict = dict()
        resDict["symbol"] = row["share_name"]

        # Looking up the symbol name using IEX API
        symDict = lookup(row["share_name"])
        resDict["name"] = symDict["name"]
        shares = row["share_amt"]

        # Checking if the transaction was a purchase or a sale
        if shares > 0:
            resDict["transact"] = "BUY"
        else:
            resDict["transact"] = "SELL"

        resDict["shares"] = shares
        resDict["price"] = row["share_price"]
        resDict["time"] = row["time"]

        result.append(resDict)

    return render_template("history.html",result=result)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # If user accesses page via GET
    if request.method == "GET":
        return render_template("quote.html")

    # If user accesses page via submitting the form (POST)
    else:
        sym = request.form.get("symbol")

        # Checking if symbol is provided
        if not sym:
            return render_template("quote.html")

        # Looking up the symbol name using IEX API
        symDict = lookup(sym)

        # Checking if the symbol is invalid
        if not symDict:
            return apology("Invalid Symbol Name", 400)

        # Passing necessary values to quoted.html
        name = symDict["name"]
        sym = symDict["symbol"]
        cost = usd(symDict["price"])
        return render_template("quoted.html", name=name, sym=sym, cost=cost)


@app.route("/register", methods=["GET", "POST"])
def register():
    # If user accesses page via GET
    if request.method == "GET":
        return render_template("register.html")

    # User accesses page via submitting the form (POST)
    else:
        # Check for blank username field or blank password field
        if not request.form.get("username") or not request.form.get("password"):
            return render_template("register.html")

        # Check for password match
        if request.form.get("password") != request.form.get("confirmation"):
            return render_template("register.html")

        # Checking if the password is atleast 8 characters long
        if len(request.form.get("password")) < 8:
            return render_template("register.html")

        # Check if username already exists
        check = db.execute("SELECT * FROM users WHERE username = :username", username = request.form.get("username"))
        if len(check) != 0:
            return apology("Username already exists", 400)

        # Insert new user and password hash into database
        user = request.form.get("username")
        pwd_hash = generate_password_hash(request.form.get("password"))
        db.execute("INSERT INTO users (username, hash) VALUES (:user, :pwd);", user = user, pwd = pwd_hash)

        # Retrieving the ID number of the user
        row = db.execute("SELECT id FROM users WHERE username = :user;", user=user)
        session["user_id"] = row[0]["id"]

        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # If user accesses the page via GET
    if request.method == "GET":

        # Query the database to retrieve all the stocks that the user has invested in
        rows = db.execute("SELECT share_name, SUM(share_amt) FROM transactions WHERE user_id = :user_id GROUP BY share_name;", user_id = session["user_id"])

        # Checking if the user has no shares to sell
        if len(rows) == 0:
            return apology("No shares to sell!", 400)
        return render_template("sell.html",rows=rows)

    # If user accesses the page by submitting the form (POST)
    else:
        # Getting the symbol of the shares the user is going to sell
        symbol = request.form.get("symbol")

        # Querying the database to retrieve the total number of shares the user has in the mentioned company
        sell = db.execute("SELECT SUM(share_amt) FROM transactions WHERE user_id = :uid AND share_name = :sym GROUP BY share_name;", uid=session["user_id"], sym=symbol)

        # Checking if the user has any shares to sell in the mentioned company
        if len(sell) == 0:
            return apology("The selected share does not exist", 400)

        shares = sell[0]["SUM(share_amt)"]
        # Getting the number of shares the user is willing to sell
        sharesSell = request.form.get("shares")
        if not sharesSell:
            return apology("Invalid number of shares", 400)
        sharesSell = int(sharesSell)

        # Checking if the user has enough shares to sell
        if sharesSell > shares:
            return apology("Exceeded number of shares to sell!", 400)

        # Looking up the symbol name using IEX API and calculating the sale price
        symDict = lookup(symbol)
        sell_price = sharesSell * symDict["price"]

        # Retrieving the current cash balance of the user
        row = db.execute("SELECT cash FROM users WHERE id = :uid;",uid=session["user_id"])
        cash = row[0]["cash"]
        balance = cash + sell_price

        # Inserting the transaction log into the database
        price = symDict["price"]
        sharesSell *= -1
        db.execute("INSERT INTO transactions (user_id, share_name, share_amt, share_price) VALUES (:uid, :name, :amt, :price);",uid=session["user_id"],name=symbol,amt=sharesSell,price=price)

        # Updating the user's cash balance
        db.execute("UPDATE users SET cash = :balance WHERE id = :uid;", balance=balance, uid=session["user_id"])

        return redirect("/")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
