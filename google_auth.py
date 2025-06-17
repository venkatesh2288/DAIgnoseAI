import json
import os
import requests
from app import db
from flask import Blueprint, redirect, request, url_for, flash
from flask_login import login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Get the current domain for redirect URL
REPLIT_DEV_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN")
if REPLIT_DEV_DOMAIN:
    REDIRECT_URL = f'https://{REPLIT_DEV_DOMAIN}/google_login/callback'
else:
    REDIRECT_URL = 'http://localhost:5000/google_login/callback'

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    print(f"✓ Google OAuth configured successfully")
    print(f"✓ Redirect URL: {REDIRECT_URL}")
else:
    print(f"""
=== GOOGLE OAUTH SETUP REQUIRED ===
Current redirect URL: {REDIRECT_URL}

Setup steps:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add this exact URL to Authorized redirect URIs: {REDIRECT_URL}
4. Copy Client ID and Client Secret to Replit Secrets

Without this setup, Google login will show 'refused to connect' error.
""")

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_oauth_status")
def oauth_status():
    """Diagnostic page to check OAuth configuration"""
    from flask import render_template_string
    
    status = {
        "client_id_configured": bool(GOOGLE_CLIENT_ID),
        "client_secret_configured": bool(GOOGLE_CLIENT_SECRET),
        "client_id": GOOGLE_CLIENT_ID[:20] + "..." if GOOGLE_CLIENT_ID else None,
        "redirect_url": REDIRECT_URL,
        "discovery_url_accessible": False
    }
    
    try:
        response = requests.get(GOOGLE_DISCOVERY_URL, timeout=5)
        status["discovery_url_accessible"] = response.status_code == 200
        status["google_response"] = response.status_code
    except Exception as e:
        status["google_error"] = str(e)
    
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Google OAuth Configuration Status</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header bg-primary text-white">
                            <h4><i class="fab fa-google me-2"></i>Google OAuth Configuration Status</h4>
                        </div>
                        <div class="card-body">
                            <div class="row mb-4">
                                <div class="col-md-6">
                                    <h5>Current Configuration</h5>
                                    <ul class="list-group">
                                        <li class="list-group-item d-flex justify-content-between">
                                            Client ID Configured
                                            {% if status.client_id_configured %}
                                                <span class="badge bg-success"><i class="fas fa-check"></i></span>
                                            {% else %}
                                                <span class="badge bg-danger"><i class="fas fa-times"></i></span>
                                            {% endif %}
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between">
                                            Client Secret Configured
                                            {% if status.client_secret_configured %}
                                                <span class="badge bg-success"><i class="fas fa-check"></i></span>
                                            {% else %}
                                                <span class="badge bg-danger"><i class="fas fa-times"></i></span>
                                            {% endif %}
                                        </li>
                                        <li class="list-group-item d-flex justify-content-between">
                                            Google Services Accessible
                                            {% if status.discovery_url_accessible %}
                                                <span class="badge bg-success"><i class="fas fa-check"></i></span>
                                            {% else %}
                                                <span class="badge bg-danger"><i class="fas fa-times"></i></span>
                                            {% endif %}
                                        </li>
                                    </ul>
                                </div>
                                <div class="col-md-6">
                                    <h5>Configuration Details</h5>
                                    <p><strong>Client ID:</strong><br><code>{{ status.client_id or 'Not configured' }}</code></p>
                                    <p><strong>Redirect URL:</strong><br><code>{{ status.redirect_url }}</code></p>
                                </div>
                            </div>
                            
                            <div class="alert alert-warning">
                                <h5><i class="fas fa-exclamation-triangle me-2"></i>Setup Checklist</h5>
                                <p>If Google login shows "refused to connect", verify these settings in Google Cloud Console:</p>
                                <ol>
                                    <li>Go to <a href="https://console.cloud.google.com/apis/credentials" target="_blank">Google Cloud Console - Credentials</a></li>
                                    <li>Find your OAuth 2.0 Client ID (or create one)</li>
                                    <li>Click "Edit" on your OAuth client</li>
                                    <li>Under "Authorized redirect URIs", add exactly:<br>
                                        <code class="bg-light p-2 d-block mt-2">{{ status.redirect_url }}</code>
                                    </li>
                                    <li>Save the configuration</li>
                                    <li>Ensure the OAuth consent screen is configured with your app details</li>
                                    <li>Set application type to "Web application"</li>
                                </ol>
                            </div>
                            
                            <div class="alert alert-info">
                                <h5><i class="fas fa-info-circle me-2"></i>Troubleshooting</h5>
                                <ul class="mb-0">
                                    <li><strong>"refused to connect"</strong> - Usually means redirect URI mismatch</li>
                                    <li><strong>Make sure the redirect URI is exactly:</strong> {{ status.redirect_url }}</li>
                                    <li><strong>Check OAuth consent screen</strong> - Must be configured with app name and details</li>
                                    <li><strong>Verify application type</strong> - Should be "Web application"</li>
                                </ul>
                            </div>
                            
                            <div class="mt-3">
                                <a href="/login" class="btn btn-primary">Back to Login</a>
                                <button onclick="window.location.reload()" class="btn btn-secondary">Refresh Status</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(template, status=status)


@google_auth.route("/google_login")
def login():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Google OAuth is not configured. Please contact administrator.', 'error')
        return redirect(url_for('login'))
    
    try:
        # Try to get Google's discovery document with timeout and better error handling
        response = requests.get(GOOGLE_DISCOVERY_URL, timeout=10)
        response.raise_for_status()
        google_provider_cfg = response.json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=REDIRECT_URL,
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except requests.exceptions.ConnectionError:
        flash('Cannot connect to Google services. Please check your internet connection or try again later.', 'error')
        return redirect(url_for('login'))
    except requests.exceptions.Timeout:
        flash('Google login timed out. Please try again.', 'error')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Failed to initiate Google login: {str(e)}', 'error')
        return redirect(url_for('login'))


@google_auth.route("/google_login/callback")
def callback():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        flash('Google OAuth is not configured. Please contact administrator.', 'error')
        return redirect(url_for('login'))
    
    try:
        code = request.args.get("code")
        if not code:
            flash('Authorization failed. Please try again.', 'error')
            return redirect(url_for('login'))
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=REDIRECT_URL,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        if token_response.status_code != 200:
            flash('Failed to get access token from Google. Please try again.', 'error')
            return redirect(url_for('login'))

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        if userinfo_response.status_code != 200:
            flash('Failed to get user information from Google. Please try again.', 'error')
            return redirect(url_for('login'))

        userinfo = userinfo_response.json()
        
        if not userinfo.get("email_verified"):
            flash('Google email not verified. Please verify your email with Google first.', 'error')
            return redirect(url_for('login'))

        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", userinfo.get("name", users_email.split('@')[0]))

        # Check if user exists
        user = User.query.filter_by(email=users_email).first()
        if not user:
            # Create new user with unique username
            base_username = users_name
            username = base_username
            counter = 1
            
            # Ensure username is unique
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User()
            user.username = username
            user.email = users_email
            # Set a random password for Google users (they won't use it)
            user.set_password(os.urandom(24).hex())
            
            try:
                db.session.add(user)
                db.session.commit()
                flash(f'Welcome to DAIgnoseAI, {username}! Your account has been created.', 'success')
            except Exception as db_error:
                db.session.rollback()
                print(f"Database error creating user: {str(db_error)}")
                flash('Error creating account. Please try again.', 'error')
                return redirect(url_for('login'))
        else:
            flash(f'Welcome back, {user.username}!', 'success')

        login_user(user, remember=True)
        return redirect(url_for('dashboard'))

    except Exception as e:
        print(f"Google OAuth Error: {str(e)}")  # Debug logging
        flash(f'Google authentication error: {str(e)}', 'error')
        return redirect(url_for('login'))