from flask import *
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from sqlalchemy import *
from sqlalchemy.orm import Session
from wtforms import *
from wtforms.validators import *
import requests
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
Bootstrap(app)

# ======================================================== #
#                        Movie db api                      #
# ======================================================== #
MOVIE_DB_API_KEY = '5aac83564138d166f70c1a439e9b297f'
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

# ======================================================== #
#                          Data base                       #
# ======================================================== #
app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top_movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# =================== CREATE DATABASE ==================#
# =================== CREATE DATABASE ==================#
engine = create_engine('sqlite:///top_movies.db')
session = Session(engine)

db = SQLAlchemy(app)

# ==================== CREATE TABLE ===================#
class Movie(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(250), unique=True)
    year = Column(Integer)
    description = Column(String(500))
    rating = Column(Float)
    ranking = Column(Integer)
    review = Column(String)
    img_url = Column(String(250))


with app.app_context():
    db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# with app.app_context():
#     db.session.add(new_movie)
#     db.session.commit()
# ======================================================== #
#                         Forms                           #
# ======================================================== #

class FindMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


# ======================================================== #
#                         @app.routes                      #
# ======================================================== #

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating.desc()).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = i +1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add_movie():
    form = FindMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data

        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        data = response.json()["results"]
        return render_template("select.html", options=data)
    return render_template("add.html", form=form)


@app.route("/find")
def find_movie():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate_movie", id=new_movie.id))


@app.route("/edit", methods=["GET", "POST"])
def rate_movie():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
