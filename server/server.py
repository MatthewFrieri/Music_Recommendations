import requests
import urllib.parse

from datetime import datetime
from flask import Flask, redirect, request, jsonify, session


CLIENT_ID = 'f322ea13e6df4e98afbfc25fbf3eb07b'
CLIENT_SECRET = '2ede704a36e94aaca091ebfb5e19eeab'
REDIRECT_URI = 'http://localhost:5000/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'


app = Flask(__name__)
app.secret_key = '23SDF32F-23F23KJFKK-FSDFK4-FSDFJ899'


@app.route('/')
def index():
    return 'Click here to login <a href="/login">Login with Spotify</a>'


@app.route('/login')
def login():

    scope = 'user-read-private user-read-email'

    params = {
        'client_id': CLIENT_ID, 
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': False  # Make True if you want the user to have to login each time
    }

    # urlencode just encodes the params into key=value&key2=value2 ...
    auth_url = f'{AUTH_URL}?{urllib.parse.urlencode(params)}'

    # auth_url = 
    # https://accounts.spotify.com/authorize
    # ?
    # client_id=f322ea13e6df4e98afbfc25fbf3eb07b
    # &response_type=code
    # &scope=user-read-private+user-read-email
    # &redirect_uri=https%3A%2F%2Flocalhost%3A5000%2Fcallback
    # &show_dialog=True

    return redirect(auth_url)


@app.route('/callback')
def callback():

    # Catch errors early
    if 'error' in request.args:
        return redirect('/')

    if 'code' in request.args:
        # Prepare post request to get the access_token, refresh_token, and expires_in

        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()
        
        # Save these values in the session
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']  # The timestamp when the access_token expires
        
        return redirect('/playlists')


@app.route('/playlists')
def playlists():

    # Catch errors early
    if 'access_token' not in session:
        return redirect('/')

    # If the access_token is expired, refresh it
    if datetime.now().timestamp() > session['expires_at']: 
        return redirect('/refresh-token')


    # Retrieve the user's playslists with a get request

    headers = {
        'Authorization': f'Bearer {session['access_token']}'
    }

    response = requests.get(f'{API_BASE_URL}me/playlists', headers=headers)
    playlists = response.json()
    return jsonify(playlists)



@app.route('/refresh-token')
def refresh_token():

    # Catch errors early
    if 'refresh_token' not in session:
        return redirect('/login')
    
    # Double check that the access_token has expired
    if datetime.now().timestamp() > session['expires_at']: 

        # Prepare post request to get a new access_token and expires_in using the refresh_token
        req_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']  # The timestamp when the access_token expires

        return redirect('/playlists')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
