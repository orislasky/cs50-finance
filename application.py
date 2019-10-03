import os
import requests
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    
    
    userinfo= db.execute("SELECT * FROM purchase WHERE username = :username; ",username=session.get("username"))
    cash= db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session.get("user_id"))
    userPu={}
    i=0
    usersCash= cash[0]["cash"]
    num=0.0
    while i<len(userinfo):
        symbol=userinfo[i]["symbol"]
        lookupInfo= lookup(symbol)
        if "name" in lookupInfo:
            name= lookupInfo["name"]
        if "price" in lookupInfo:
             price=usd(lookupInfo["price"]) 
        total=lookupInfo["price"]*userinfo[i]["amount"]
        num=float(total)+float(num)
        userPu[i] = {
            'symbol': userinfo[i]["symbol"],
            'name': name,
            'shares': userinfo[i]["amount"],
            'price': price,
            'total': usd(total)
        }
        i+=1
        
    num = usd(float(usersCash)+float(num))
    userPu[i+1] ={
        'symbol': "cash",
        'name':"",
        'shares':"",
        'price':"",
        'total': usd(usersCash)
    }
    
       
    
    
    
    myLookup = userPu,
    return render_template("index.html", Myloop=myLookup,total=num)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        if not  request.form.get("symbol"):
          return apology("must add compony symble!!", code=200) 
          
        if not lookup(request.form.get("symbol")):
            return apology("no match found!!", code=403)
        
        if not request.form.get("shares"):
             return apology("ivalide number of shares to buy!!!", code=420)
        
        if int(request.form.get("shares"))<=0:
             return apology("ivalide number of shares to buy!!!", code=420)
             
        
        amntMon=db.execute("SELECT * FROM users WHERE id = :user_id", user_id=session.get("user_id"))
        price=0.0
        if "price" in lookup(request.form.get("symbol")):
            price = lookup(request.form.get("symbol"))["price"]
            
        shares = request.form.get("shares")
        symbol=request.form.get("symbol")
        
        total= amntMon[0]["cash"]
        if total<(price*float(shares)):
            return apology("You dont have enough MONEY!", code=4545)
        # making a new table for puchases
        
        user = amntMon[0]["username"]
        timeNow=datetime.datetime.today()
        
        exists=db.execute("SELECT COUNT(1) FROM purchase WHERE symbol = :symbol AND username=:username;", symbol=symbol, username=user)
        print(exists)
        if exists[0]["COUNT(1)"]==0:
            db.execute("INSERT INTO purchase(username,symbol,amount,price,date_time) VALUES(:user,:symbol, :shares,:price,:timeNow);", user=user,symbol=symbol, shares=shares, price=price,timeNow=timeNow)
        else: 
            amount=db.execute("SELECT amount FROM purchase WHERE username = :username AND symbol=:symbol; ",username=session.get("username"), symbol=request.form.get("symbol"))
            sharesLeft=amount[0]["amount"]+int(shares)
            db.execute("UPDATE purchase SET amount = :shares WHERE  username = :username AND symbol=:symbol; ", shares=sharesLeft, username=session.get("username"), symbol=request.form.get("symbol"))
        #insertin to history table 
        
        db.execute("INSERT INTO history(username,symbol,action,amount,price,date_time) VALUES(:user,:symbol,'buy',:shares,:price,:timeNow);",user=session.get("username"),symbol=symbol, shares=shares, price=price,timeNow=timeNow)
        #intshares = int(shares)
        #if (historyinsert):
        money=total-int(shares)*price
        
    
        db.execute("UPDATE users SET cash=:money WHERE id = :user_id",money=money, user_id=amntMon[0]["id"])
        return redirect("/")


        
        
        
        #if (amntMon<(request.form.get("shares"))*int(lookup(request.form.get("symbol").price))):
        # return apology("You dont have enough money to buy so meny stocks", code = 5000)
        
        
             
        

        
         


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    httPar=request.args.get('username')
    print(httPar)
    userExist=db.execute("SELECT COUNT(1) FROM users WHERE username = :username;", username=httPar)
    exists=userExist[0]["COUNT(1)"]
    if len(httPar)>=1 and exists==0:
        return jsonify("true")
    else:
        return jsonify("false")
    
    
    
    


    
    
  

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    userPu={}
    userHistory=db.execute("SELECT * FROM history WHERE username=:username;",username=session.get("username"))
    print(userHistory)
    i=0
    while i < len(userHistory):
        userPu[i] = {
            'action': userHistory[i]["action"],
            'symbol': userHistory[i]["symbol"],
            'price': userHistory[i]["price"],
            'shares': userHistory[i]["amount"],
            'date_time': userHistory[i]["date_time"] 
            
        }
        i=i+1
    return render_template("history.html", Myloop=userPu)
        



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
        session["username"] = request.form.get("username")

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
    if request.method=="GET":
        return render_template("quote.html")
        
    else:
        symble = request.form.get("symbol")
        myLookup = lookup(symble)
        #print(myLookup[1]['price'])
        return render_template("quoted.html", Myloop=myLookup)
        #url = f"https://cloud-sse.iexapis.com/stable/stock/{symble}/quote?token=pk_bc6ee7b8d3d04499a57f1b70819dd2cc"
        #r = requests.get(url)
        
        
        
        
    #return apology("TODO")

@app.route("/register", methods=["GET"])
def registerGet():
    return render_template("register.html")

    

@app.route("/register", methods=["POST"])
def register():
    """Register user"""
    
    if not request.form.get("username"):
        return apology("must provide with username", code = 400)
        # making sure that the user name 
    rows = db.execute("SELECT * FROM users WHERE username = :username",username=request.form.get("username"))
    #if len(rows) >0:
        #return apology("invalid username", code = 450)
    if not request.form.get("password"):
        return apology("must include password", code=450)
    if request.form.get("password") != request.form.get("confirmation"):
        return apology(check_password_hash(rows[0]["hash"], request.form.get("password")))
        
    hashpass=request.form.get("password")
    newPass=generate_password_hash(hashpass,"sha256")
    
    insert = db.execute("INSERT INTO users (username, hash) VALUES (:username, :password);",username=request.form.get("username"),password=newPass)
    
    return redirect("/login")
    

        
    


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method=="GET":
        userPu=db.execute("SELECT symbol FROM purchase WHERE username = :username; ",username=session.get("username"))
        return render_template("sell.html", Myloop=userPu)
    else:
        userPu=db.execute("SELECT amount FROM purchase WHERE username = :username AND symbol=:symbol; ",username=session.get("username"), symbol=request.form.get("symbol"))
        if not request.form.get("symbol"):
            return apology("must input symbol", code=590)
        if int(request.form.get("shares"))<=0:
            return apology("must input a valid number of shares to sell", code=590)
        if int(request.form.get("shares"))>=userPu[0]["amount"]:
            return apology("you dont have this meny shares to sell", code=590)
        
        price=0.0
        symbolInfo= lookup(request.form.get("symbol"))
        if "price" in symbolInfo:
            price=symbolInfo["price"]
        totalPrice=float(request.form.get("shares"))*price
        DBcash= db.execute("select cash FROM users WHERE username=:username",username=session.get("username"))
        
        cash= DBcash[0]["cash"]
        cash= cash+totalPrice
        # updates th euser cash table
        db.execute("UPDATE users SET cash = :cash WHERE username=:username",cash=cash,username=session.get("username"))
        #updates the purchase 
        sharesLeft=userPu[0]["amount"]-int(request.form.get("shares"))
        if sharesLeft==0:
            db.execute("DELETE FROM purchase WHERE  username = :username AND symbol=:symbol; ",username=session.get("username"), symbol=request.form.get("symbol"))
        else:
            db.execute("UPDATE purchase SET amount = :shares WHERE  username = :username AND symbol=:symbol; ", shares=sharesLeft, username=session.get("username"), symbol=request.form.get("symbol"))
        user= session.get("username")
        symbol=request.form.get("symbol")
        shares=int(request.form.get("shares"))
        timeNow=datetime.datetime.today()
        
        #inserting to history table
        db.execute("INSERT INTO history(username,symbol,action,amount,price,date_time) VALUES(:user,:symbol,'sell',:shares,:price,:timeNow);", user=session.get("username"),symbol=symbol, shares=shares, price=price,timeNow=timeNow)
        return redirect("/")
        


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
