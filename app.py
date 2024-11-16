# run with `flask --app app run --debug``

import os

from flask import (
    Flask,
    render_template,
    session,
    request,
    redirect,
    url_for,
    flash,
)

from flask_sqlalchemy import SQLAlchemy #need to install
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from spotipy import Spotify, CacheHandler
from spotipy.oauth2 import SpotifyOAuth

class CacheSessionHandler(CacheHandler):
    def __init__(self, session, token_key):
        self.token_key = token_key
        self.session = session

    def get_cached_token(self):
        return self.session.get(self.token_key)

    def save_token_to_cache(self, token_info):
        self.session[self.token_key] = token_info
        session.modified = True



# setup flask app stuff
app = Flask(__name__)
app.secret_key = "DEV"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'


# database stuff

    # to set up database, do:
    #   from app import app, db, Playlists, SongByPlaylist, Song, Artist
    #   db.create_all()
    # to clear database, do:
    # models.[TABLE TO CLEAR].query.delete()

db = SQLAlchemy(app)
app.app_context().push()

# models
class Playlists(db.Model):
    playlist_table_id = db.Column(db.Integer, primary_key=True)
    playlist_spotify_id = db.Column(db.String)
    playlist_name = db.Column(db.String)

#    def __init__(self, playlist_id, playlist_name):
#        self.playlist_id = playlist_id
#        self.playlist_name = playlist_name

    def __repr__(self):
        return f"Playlist: ('{self.playlist_id}', '{self.playlist_name}')"

class SongByPlaylist(db.Model):
    song_id = db.Column(db.String, primary_key=True)
    playlist_id = db.Column(db.String, nullable=False) 

    def __init__(self, song_id, playlist_id):
        self.song_id = song_id
        self.playlist_id = playlist_id

    def __repr__(self):
        return f"Song: ('{self.song_id}', '{self.playlist_id}')"

class Song(db.Model):
    song_id = db.Column(db.String(100), primary_key=True)
    song_name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer(), nullable=False)
    month = db.Column(db.Integer(), nullable=False)
    day = db.Column(db.Integer(), nullable=False)

    def __init__(self, song_id, song_name, year, month, day):
        self.song_id = song_id
        self.song_name = song_name
        self.year = year
        self.month = month
        self.day = day

    def __repr__(self):
        return f"Song: ('{self.song_id}', '{self.song_name}')"

class Artist(db.Model):
    artist_id = db.Column(db.String(50), primary_key=True)
    artist_name = db.Column(db.String(100), nullable=False)

    def __init__(self, artist_id, artist_name):
        self.artist_id = artist_id
        self.artist_name = artist_name

    def __repr__(self):
        return f"Song: ('{self.artist_id}', '{self.artist_name}')"


# TODO: add Genre, SongByArtist, SongByGenre
#https://www.geeksforgeeks.org/connect-flask-to-a-database-with-flask-sqlalchemy/#setting-up-sqlalchemy
# https://flask-sqlalchemy.readthedocs.io/en/stable/quickstart/#installation


# setup spotify stuff
SPOITFY_CLIENT_ID = "d511528d911b44e9a81863869ee60809"
SPOTIFY_CLIENT_SECRET = "2b40cfddb1c74814a4092114c8ffc206"

oauth_manager = SpotifyOAuth(
    client_id=SPOITFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri="http://localhost:5000",
    scope="user-read-email playlist-read-private playlist-read-collaborative user-library-read",
    cache_handler=CacheSessionHandler(session, "spotify_token"),
)


# app stuff
@app.route("/")
def homepage():
    jinja_env = {}

    if request.args.get("code") or oauth_manager.validate_token(
        oauth_manager.get_cached_token()
    ):
        oauth_manager.get_access_token(request.args.get("code"))
        return redirect("/spotify-info")

    return render_template(
        "index.html", spotify_auth_url=oauth_manager.get_authorize_url()
        # this is the login page
    )


# this is where we get spotify info
@app.route("/spotify-info", methods = ["GET"])
def show_spotify_info():
    if not oauth_manager.validate_token(oauth_manager.get_cached_token()):
        return redirect("/")

    sp = Spotify(auth_manager=oauth_manager)

    # get user's playlists
    playlists = sp.current_user_playlists()["items"]

    # put playlist info into database --- this can prob be turned into a function to be called later, along with info for other tables

    # try to put playlist info into database (if already exists, will go to except and pass on)
    try:
        # iterare through lists of playlists
        for i in range(0, len(playlists)):
            playlists[i]["table_id"] = i # assign int primary key bc it didn't want a string primary key

            # get playlist info
            playlist_table_id = playlists[i]["table_id"]
            playlist_id = playlists[i]["id"]
            playlist_name = playlists[i]["name"]

            # create playlist obj row using info
            new_playlist = Playlists(playlist_table_id = playlist_table_id, playlist_spotify_id = playlist_id, playlist_name = playlist_name)

            # add playlist obj to db and commit
            db.session.add(new_playlist)
            db.session.commit()
    except:
        pass

# this doesnt work==maybe bc it expects primary key to be an int
#    for playlist in playlists:
#        playlist_id = playlist["id"]
#        playlist_name = playlist["name"]

 #       new_playlist = Playlists(playlist_id=1, playlist_name="test")
 #       db.session.add(new_playlist)
 #       db.session.commit()

    #return render_template("spotify_info.html", spotify=sp)
    # random page to show playlists
    return render_template("spotify_info.html", ps=playlists)
    





if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, use_debugger=True)