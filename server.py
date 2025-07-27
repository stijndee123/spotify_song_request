from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///queued_songs_test.db'
db = SQLAlchemy(app)

# Lees credentials en tokens uit environment variables
client_id = os.getenv('SPOTIFY_CLIENT_ID')
client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
refresh_token = os.getenv('SPOTIFY_REFRESH_TOKEN')

scope = "user-modify-playback-state,user-read-playback-state"

# Setup SpotifyOAuth zonder interactie, met refresh token
sp_oauth = SpotifyOAuth(client_id=client_id,
                        client_secret=client_secret,
                        redirect_uri=redirect_uri,
                        scope=scope)

def get_spotify_client():
    # Vernieuw access token met de refresh token
    token_info = sp_oauth.refresh_access_token(refresh_token)
    access_token = token_info['access_token']
    return spotipy.Spotify(auth=access_token)

sp = get_spotify_client()

past_track_uri = ""
print(" * User logged in: " + sp.current_user()['display_name'])

class playedSongs(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uri = db.Column(db.String(64))

def checkSong():
    try:
        with app.app_context():
            global past_track_uri, sp
            sp = get_spotify_client()  # vernieuw token bij elk interval
            current_track = sp.current_playback()
            current_track_uri = current_track['item']['uri']
            if current_track_uri != past_track_uri:
                past_track_uri = current_track_uri
                song = playedSongs(uri=current_track_uri)
                db.session.add(song)
                db.session.commit()
                print("song: " + current_track['item']['name'] + " added to database")
    except Exception as e:
        print("no song playing or error:", e)

def startScheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=checkSong, trigger="interval", seconds=30)
    scheduler.start()

@app.route('/song_queue/search')
def home():
    song_name = request.args.get('name')
    if song_name:
        global sp
        sp = get_spotify_client()
        tracks = sp.search(song_name, limit=20, type='track')
        tracks = tracks['tracks']['items']
        return render_template('results.html', tracks=tracks)
    return render_template('search.html')

@app.route('/song_queue/api/queue', methods=['POST'])
def addToQueue():
    try:
        global sp
        sp = get_spotify_client()
        uri = request.get_data(as_text=True)
        sp.add_to_queue(uri=uri)
        return jsonify({"message": "received"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/song_queue/queue')
def queue():
    global sp
    sp = get_spotify_client()
    queue = sp.queue()
    currently_playing = queue['currently_playing']
    queue = queue['queue']
    return render_template('queue.html', currently_playing=currently_playing, queue=queue)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    startScheduler()
    app.run(use_reloader=False, debug=True, host='0.0.0.0', port=8000)
