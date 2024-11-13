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


from spotipy import Spotify, CacheHandler
from spotipy.oauth2 import SpotifyOAuth

SPOITFY_CLIENT_ID = "d511528d911b44e9a81863869ee60809"
SPOTIFY_CLIENT_SECRET = "2b40cfddb1c74814a4092114c8ffc206"


class CacheSessionHandler(CacheHandler):
    def __init__(self, session, token_key):
        self.token_key = token_key
        self.session = session

    def get_cached_token(self):
        return self.session.get(self.token_key)

    def save_token_to_cache(self, token_info):
        self.session[self.token_key] = token_info
        session.modified = True


app = Flask(__name__)
app.secret_key = "DEV"
oauth_manager = SpotifyOAuth(
    client_id=SPOITFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri="http://localhost:5000",
    scope="user-read-email playlist-read-private playlist-read-collaborative user-library-read",
    cache_handler=CacheSessionHandler(session, "spotify_token"),
)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)


class Playlists(db.model):
    playlist_id = db.Column(db.Integer(100), primary_key=True)
    playlist_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Playlist: ('{self.playlist_id}', '{self.playlist_name}')"

class SongByPlaylist(db.model):
    song_id = db.Column(db.Integer(100), primary_key=True)
    playlist_id = db.Column(db.String(100), nullable=False) 

    def __repr__(self):
        return f"Song: ('{self.song_id}', '{self.playlist_id}')"

class Song(db.model):
    song_id = db.Column(db.String(100), primary_key=True)
    song_name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer(4), nullable=False)
    mon5h = db.Column(db.Integer(2), nullable=False)
    day = db.Column(db.Integer(2), nullable=False)

    def __repr__(self):
        return f"Song: ('{self.song_id}', '{self.song_name}')"

class Artist(db.model):
    artist_id = db.Column(db.Integer(100), primary_key=True)
    artist_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"Song: ('{self.artist_id}', '{self.artist_name}')"

# TODO: add Genre, SongByArtist, SongByGenre
#https://www.geeksforgeeks.org/connect-flask-to-a-database-with-flask-sqlalchemy/#setting-up-sqlalchemy

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
    )


@app.route("/spotify-info")
def show_spotify_info():
    if not oauth_manager.validate_token(oauth_manager.get_cached_token()):
        return redirect("/")

    sp = Spotify(auth_manager=oauth_manager)

    playlists = sp.current_user_playlists()["items"]

    #return render_template("spotify_info.html", spotify=sp)
    return render_template("spotify_info.html", ps=playlists)
    


if __name__ == "__main__":
    app.run(debug=True, use_reloader=True, use_debugger=True)