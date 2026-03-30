import os
from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
# Render par secret key secure rakhne ke liye
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

# ✅ MongoDB Atlas Connection
mongo_uri = os.environ.get("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["movie_rating_db"]

# Collections ko global define kar diya taaki har function ko milein
users = db["users"]
movies = db["movies"]
ratings = db["ratings"]

@app.route('/')
def home():
    return redirect(url_for('index'))

@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = {
            "name": request.form["name"],
            "email": request.form["email"],
            "password": request.form["password"],
            "role": "user"
        }
        users.insert_one(user)
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = users.find_one({"email": email, "password": password})
        if user:
            session["user"] = user["email"]
            session["role"] = user["role"]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid login"
    return render_template("login.html")  

@app.route('/dashboard')
def dashboard():
    role = session.get("role")
    movie_list = movies.find()
    movie_data = []
    for movie in movie_list:
        movie_ratings = list(ratings.find({"movie_id": str(movie["_id"])}))
        avg = sum(int(r["rating"]) for r in movie_ratings) / len(movie_ratings) if movie_ratings else 0
        movie_data.append({"movie": movie, "avg_rating": round(avg, 1)})
    
    total_movies = movies.count_documents({})
    total_ratings = ratings.count_documents({})
    return render_template("dashboard.html", movies=movie_data, total_movies=total_movies, total_ratings=total_ratings, role=role)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add_movie', methods=["GET","POST"])
def add_movie():
    if session.get("role") != "admin":
        return redirect(url_for('dashboard'))
    if request.method == "POST":
        movies.insert_one({
            "movieName": request.form["movieName"],
            "genre": request.form["genre"],
            "releaseDate": request.form["releaseDate"],
            "poster": request.form["poster"],
            "youtubeUrl": request.form.get("youtubeUrl"),
            "fullMovieLink": request.form.get("fullMovieLink")
        })
        return redirect(url_for('movies_page')) # ✅ Redirect add kiya
    return render_template("add_movie.html")

@app.route('/delete_movie/<id>')
def delete_movie(id):
    if session.get("role") != "admin":
        return redirect(url_for('dashboard'))
    # ✅ Id ko ObjectId mein convert kiya
    movies.delete_one({"_id": ObjectId(id)})
    ratings.delete_many({"movie_id": id})
    return redirect(url_for('movies_page'))

@app.route('/admin_login', methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        if request.form["email"] == "admin@gmail.com" and request.form["password"] == "admin123":
            session["user"] = "Admin"
            session["role"] = "admin"
            return redirect(url_for('dashboard')) # ✅ Dashboard par bheja
        else:
            return "Invalid Admin Login"
    return render_template("admin_login.html")

@app.route('/movies')
def movies_page():
    movie_list = movies.find()
    movie_data = []
    for movie in movie_list:
        movie_ratings = list(ratings.find({"movie_id": str(movie["_id"])}))
        total = len(movie_ratings)
        avg = sum(int(r["rating"]) for r in movie_ratings) / total if total > 0 else 0
        movie_data.append({
            "movie": movie,
            "avg_rating": round(avg, 1),
            "total_ratings": total
        })
    return render_template("movies.html", movies=movie_data)

@app.route('/rate/<movie_id>', methods=['POST'])
def rate(movie_id):
    # ✅ 'ratings' collection use kiya
    ratings.insert_one({
        "movie_id": movie_id,
        "rating": int(request.form['rating'])
    })
    return redirect(url_for('movies_page'))

@app.route('/watch/<id>')
def watch_movie(id):
    movie = movies.find_one({"_id": ObjectId(id)})
    return render_template("watch_movie.html", movie=movie)

if __name__ == "__main__":
    app.run(debug=True)
