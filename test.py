from flask import Flask, jsonify, make_response, request, redirect
import pyodbc
import logging
from flask_cors import CORS
from postmarker.core import PostmarkClient
from uuid import uuid4
import time
import requests
from dotenv import find_dotenv, load_dotenv
from os import environ as env
import mysql.connector
from mysql.connector import pooling


app = Flask(__name__)

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
CORS(app, resources={r"/*": {"origins": ["https://dev.xcitesolutions.com.au/"]}})

TOKENMANAGEMENT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IklEQTE1T2FjNzRXb2tmRFU0cE1RSSJ9.eyJpc3MiOiJodHRwczovL2Rldi1wY3I3MGQ0MnVieGJrMTZqLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJpRlpvb1JqYmt5TWpwc2NzVVNsME9JMDBoNTBNWVoxOEBjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9kZXYtcGNyNzBkNDJ1YnhiazE2ai51cy5hdXRoMC5jb20vYXBpL3YyLyIsImlhdCI6MTczNDM5ODM5MCwiZXhwIjoxNzM0NDg0NzkwLCJndHkiOiJjbGllbnQtY3JlZGVudGlhbHMiLCJhenAiOiJpRlpvb1JqYmt5TWpwc2NzVVNsME9JMDBoNTBNWVoxOCJ9.Ezf7siJLMl-qiOOl1uGiZ_fR8E6CA9QYfI-FIx70chCmFJp-xwDMUqmF_eRSBKCXogntsQxiIL-f_UjY0YgQ8WYmsxV-vho0Gy4FFSd2TtILUvDwPM7ahMTtA71voDj2W40jErh8qpe7X43nTmvlLJiKI_N33iJ6vXbLmAD32NCDPCISn8WxN8Uq4oVQ4DtaGNKivVafKvORRw186oTACFqrWcEvOJT7B_HKgvydEP7fWKhEg5qHn3Pgylod2uzMmwBMeHtOIdnE0Rk9PHI7vU4L4SRX9EWUG87eCXQt9emHXTAodmTc65ZemgI8lOvhhTCrFaJX4Zpu3-cLk-gXHQ"
# Postmark client configuration
POSTMARK_SERVER_TOKEN = "01106150-1ba9-412a-bd34-3c83b9a69166"
postmark_client = PostmarkClient(server_token=POSTMARK_SERVER_TOKEN)
AUTH0_DOMAIN = "dev-pcr70d42ubxbk16j.us.auth0.com"
CLIENT_ID = "iFZooRjbkyMjpscsUSl0OI00h50MYZ18"
CLIENT_SECRET = "BS0R0OlDwfvNYXrwiQ0am5S_yGk82fL6uIi0k_pqdDyaYn--dPLdjFzWekhOTpSO"
# AUDIENCE = "http://127.0.0.1:5000"

# Simple token store (use a database for production)
email_tokens = {}
TOKEN_EXPIRATION_SECONDS = 3600  # Tokens valid for 1 hour

# Database connection string
connection = mysql.connector.connect(

    host="xcite-rds.cqdlazquunbi.ap-southeast-2.rds.amazonaws.com",
    user="admin",
    password="emaxC192g47",
    database="xcite-db"
)

AUTH0_MANAGEMENT_API_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6IklEQTE1T2FjNzRXb2tmRFU0cE1RSSJ9.eyJpc3MiOiJodHRwczovL2Rldi1wY3I3MGQ0MnVieGJrMTZqLnVzLmF1dGgwLmNvbS8iLCJzdWIiOiJJaHNTMnJRNlZmeXlHNE9MTmk1bG5CNzFoOGhEVVowMUBjbGllbnRzIiwiYXVkIjoiaHR0cHM6Ly9kZXYtcGNyNzBkNDJ1YnhiazE2ai51cy5hdXRoMC5jb20vYXBpL3YyLyIsImlhdCI6MTczNTc4MDE0NywiZXhwIjoxNzM1ODY2NTQ3LCJzY29wZSI6InJlYWQ6Y2xpZW50X2dyYW50cyBjcmVhdGU6Y2xpZW50X2dyYW50cyBkZWxldGU6Y2xpZW50X2dyYW50cyB1cGRhdGU6Y2xpZW50X2dyYW50cyByZWFkOnVzZXJzIHVwZGF0ZTp1c2VycyBkZWxldGU6dXNlcnMgY3JlYXRlOnVzZXJzIHJlYWQ6dXNlcnNfYXBwX21ldGFkYXRhIHVwZGF0ZTp1c2Vyc19hcHBfbWV0YWRhdGEgZGVsZXRlOnVzZXJzX2FwcF9tZXRhZGF0YSBjcmVhdGU6dXNlcnNfYXBwX21ldGFkYXRhIHJlYWQ6dXNlcl9jdXN0b21fYmxvY2tzIGNyZWF0ZTp1c2VyX2N1c3RvbV9ibG9ja3MgZGVsZXRlOnVzZXJfY3VzdG9tX2Jsb2NrcyBjcmVhdGU6dXNlcl90aWNrZXRzIHJlYWQ6Y2xpZW50cyB1cGRhdGU6Y2xpZW50cyBkZWxldGU6Y2xpZW50cyBjcmVhdGU6Y2xpZW50cyByZWFkOmNsaWVudF9rZXlzIHVwZGF0ZTpjbGllbnRfa2V5cyBkZWxldGU6Y2xpZW50X2tleXMgY3JlYXRlOmNsaWVudF9rZXlzIHJlYWQ6Y29ubmVjdGlvbnMgdXBkYXRlOmNvbm5lY3Rpb25zIGRlbGV0ZTpjb25uZWN0aW9ucyBjcmVhdGU6Y29ubmVjdGlvbnMgcmVhZDpyZXNvdXJjZV9zZXJ2ZXJzIHVwZGF0ZTpyZXNvdXJjZV9zZXJ2ZXJzIGRlbGV0ZTpyZXNvdXJjZV9zZXJ2ZXJzIGNyZWF0ZTpyZXNvdXJjZV9zZXJ2ZXJzIHJlYWQ6ZGV2aWNlX2NyZWRlbnRpYWxzIHVwZGF0ZTpkZXZpY2VfY3JlZGVudGlhbHMgZGVsZXRlOmRldmljZV9jcmVkZW50aWFscyBjcmVhdGU6ZGV2aWNlX2NyZWRlbnRpYWxzIHJlYWQ6cnVsZXMgdXBkYXRlOnJ1bGVzIGRlbGV0ZTpydWxlcyBjcmVhdGU6cnVsZXMgcmVhZDpydWxlc19jb25maWdzIHVwZGF0ZTpydWxlc19jb25maWdzIGRlbGV0ZTpydWxlc19jb25maWdzIHJlYWQ6aG9va3MgdXBkYXRlOmhvb2tzIGRlbGV0ZTpob29rcyBjcmVhdGU6aG9va3MgcmVhZDphY3Rpb25zIHVwZGF0ZTphY3Rpb25zIGRlbGV0ZTphY3Rpb25zIGNyZWF0ZTphY3Rpb25zIHJlYWQ6ZW1haWxfcHJvdmlkZXIgdXBkYXRlOmVtYWlsX3Byb3ZpZGVyIGRlbGV0ZTplbWFpbF9wcm92aWRlciBjcmVhdGU6ZW1haWxfcHJvdmlkZXIgYmxhY2tsaXN0OnRva2VucyByZWFkOnN0YXRzIHJlYWQ6aW5zaWdodHMgcmVhZDp0ZW5hbnRfc2V0dGluZ3MgdXBkYXRlOnRlbmFudF9zZXR0aW5ncyByZWFkOmxvZ3MgcmVhZDpsb2dzX3VzZXJzIHJlYWQ6c2hpZWxkcyBjcmVhdGU6c2hpZWxkcyB1cGRhdGU6c2hpZWxkcyBkZWxldGU6c2hpZWxkcyByZWFkOmFub21hbHlfYmxvY2tzIGRlbGV0ZTphbm9tYWx5X2Jsb2NrcyB1cGRhdGU6dHJpZ2dlcnMgcmVhZDp0cmlnZ2VycyByZWFkOmdyYW50cyBkZWxldGU6Z3JhbnRzIHJlYWQ6Z3VhcmRpYW5fZmFjdG9ycyB1cGRhdGU6Z3VhcmRpYW5fZmFjdG9ycyByZWFkOmd1YXJkaWFuX2Vucm9sbG1lbnRzIGRlbGV0ZTpndWFyZGlhbl9lbnJvbGxtZW50cyBjcmVhdGU6Z3VhcmRpYW5fZW5yb2xsbWVudF90aWNrZXRzIHJlYWQ6dXNlcl9pZHBfdG9rZW5zIGNyZWF0ZTpwYXNzd29yZHNfY2hlY2tpbmdfam9iIGRlbGV0ZTpwYXNzd29yZHNfY2hlY2tpbmdfam9iIHJlYWQ6Y3VzdG9tX2RvbWFpbnMgZGVsZXRlOmN1c3RvbV9kb21haW5zIGNyZWF0ZTpjdXN0b21fZG9tYWlucyB1cGRhdGU6Y3VzdG9tX2RvbWFpbnMgcmVhZDplbWFpbF90ZW1wbGF0ZXMgY3JlYXRlOmVtYWlsX3RlbXBsYXRlcyB1cGRhdGU6ZW1haWxfdGVtcGxhdGVzIHJlYWQ6bWZhX3BvbGljaWVzIHVwZGF0ZTptZmFfcG9saWNpZXMgcmVhZDpyb2xlcyBjcmVhdGU6cm9sZXMgZGVsZXRlOnJvbGVzIHVwZGF0ZTpyb2xlcyByZWFkOnByb21wdHMgdXBkYXRlOnByb21wdHMgcmVhZDpicmFuZGluZyB1cGRhdGU6YnJhbmRpbmcgZGVsZXRlOmJyYW5kaW5nIHJlYWQ6bG9nX3N0cmVhbXMgY3JlYXRlOmxvZ19zdHJlYW1zIGRlbGV0ZTpsb2dfc3RyZWFtcyB1cGRhdGU6bG9nX3N0cmVhbXMgY3JlYXRlOnNpZ25pbmdfa2V5cyByZWFkOnNpZ25pbmdfa2V5cyB1cGRhdGU6c2lnbmluZ19rZXlzIHJlYWQ6bGltaXRzIHVwZGF0ZTpsaW1pdHMgY3JlYXRlOnJvbGVfbWVtYmVycyByZWFkOnJvbGVfbWVtYmVycyBkZWxldGU6cm9sZV9tZW1iZXJzIHJlYWQ6ZW50aXRsZW1lbnRzIHJlYWQ6YXR0YWNrX3Byb3RlY3Rpb24gdXBkYXRlOmF0dGFja19wcm90ZWN0aW9uIHJlYWQ6b3JnYW5pemF0aW9uc19zdW1tYXJ5IGNyZWF0ZTphdXRoZW50aWNhdGlvbl9tZXRob2RzIHJlYWQ6YXV0aGVudGljYXRpb25fbWV0aG9kcyB1cGRhdGU6YXV0aGVudGljYXRpb25fbWV0aG9kcyBkZWxldGU6YXV0aGVudGljYXRpb25fbWV0aG9kcyByZWFkOm9yZ2FuaXphdGlvbnMgdXBkYXRlOm9yZ2FuaXphdGlvbnMgY3JlYXRlOm9yZ2FuaXphdGlvbnMgZGVsZXRlOm9yZ2FuaXphdGlvbnMgY3JlYXRlOm9yZ2FuaXphdGlvbl9tZW1iZXJzIHJlYWQ6b3JnYW5pemF0aW9uX21lbWJlcnMgZGVsZXRlOm9yZ2FuaXphdGlvbl9tZW1iZXJzIGNyZWF0ZTpvcmdhbml6YXRpb25fY29ubmVjdGlvbnMgcmVhZDpvcmdhbml6YXRpb25fY29ubmVjdGlvbnMgdXBkYXRlOm9yZ2FuaXphdGlvbl9jb25uZWN0aW9ucyBkZWxldGU6b3JnYW5pemF0aW9uX2Nvbm5lY3Rpb25zIGNyZWF0ZTpvcmdhbml6YXRpb25fbWVtYmVyX3JvbGVzIHJlYWQ6b3JnYW5pemF0aW9uX21lbWJlcl9yb2xlcyBkZWxldGU6b3JnYW5pemF0aW9uX21lbWJlcl9yb2xlcyBjcmVhdGU6b3JnYW5pemF0aW9uX2ludml0YXRpb25zIHJlYWQ6b3JnYW5pemF0aW9uX2ludml0YXRpb25zIGRlbGV0ZTpvcmdhbml6YXRpb25faW52aXRhdGlvbnMgcmVhZDpzY2ltX2NvbmZpZyBjcmVhdGU6c2NpbV9jb25maWcgdXBkYXRlOnNjaW1fY29uZmlnIGRlbGV0ZTpzY2ltX2NvbmZpZyBjcmVhdGU6c2NpbV90b2tlbiByZWFkOnNjaW1fdG9rZW4gZGVsZXRlOnNjaW1fdG9rZW4gZGVsZXRlOnBob25lX3Byb3ZpZGVycyBjcmVhdGU6cGhvbmVfcHJvdmlkZXJzIHJlYWQ6cGhvbmVfcHJvdmlkZXJzIHVwZGF0ZTpwaG9uZV9wcm92aWRlcnMgZGVsZXRlOnBob25lX3RlbXBsYXRlcyBjcmVhdGU6cGhvbmVfdGVtcGxhdGVzIHJlYWQ6cGhvbmVfdGVtcGxhdGVzIHVwZGF0ZTpwaG9uZV90ZW1wbGF0ZXMgY3JlYXRlOmVuY3J5cHRpb25fa2V5cyByZWFkOmVuY3J5cHRpb25fa2V5cyB1cGRhdGU6ZW5jcnlwdGlvbl9rZXlzIGRlbGV0ZTplbmNyeXB0aW9uX2tleXMgcmVhZDpzZXNzaW9ucyBkZWxldGU6c2Vzc2lvbnMgcmVhZDpyZWZyZXNoX3Rva2VucyBkZWxldGU6cmVmcmVzaF90b2tlbnMgY3JlYXRlOnNlbGZfc2VydmljZV9wcm9maWxlcyByZWFkOnNlbGZfc2VydmljZV9wcm9maWxlcyB1cGRhdGU6c2VsZl9zZXJ2aWNlX3Byb2ZpbGVzIGRlbGV0ZTpzZWxmX3NlcnZpY2VfcHJvZmlsZXMgY3JlYXRlOnNzb19hY2Nlc3NfdGlja2V0cyBkZWxldGU6c3NvX2FjY2Vzc190aWNrZXRzIHJlYWQ6Zm9ybXMgdXBkYXRlOmZvcm1zIGRlbGV0ZTpmb3JtcyBjcmVhdGU6Zm9ybXMgcmVhZDpmbG93cyB1cGRhdGU6Zmxvd3MgZGVsZXRlOmZsb3dzIGNyZWF0ZTpmbG93cyByZWFkOmZsb3dzX3ZhdWx0IHJlYWQ6Zmxvd3NfdmF1bHRfY29ubmVjdGlvbnMgdXBkYXRlOmZsb3dzX3ZhdWx0X2Nvbm5lY3Rpb25zIGRlbGV0ZTpmbG93c192YXVsdF9jb25uZWN0aW9ucyBjcmVhdGU6Zmxvd3NfdmF1bHRfY29ubmVjdGlvbnMgcmVhZDpmbG93c19leGVjdXRpb25zIGRlbGV0ZTpmbG93c19leGVjdXRpb25zIHJlYWQ6Y29ubmVjdGlvbnNfb3B0aW9ucyB1cGRhdGU6Y29ubmVjdGlvbnNfb3B0aW9ucyByZWFkOnNlbGZfc2VydmljZV9wcm9maWxlX2N1c3RvbV90ZXh0cyB1cGRhdGU6c2VsZl9zZXJ2aWNlX3Byb2ZpbGVfY3VzdG9tX3RleHRzIHJlYWQ6Y2xpZW50X2NyZWRlbnRpYWxzIGNyZWF0ZTpjbGllbnRfY3JlZGVudGlhbHMgdXBkYXRlOmNsaWVudF9jcmVkZW50aWFscyBkZWxldGU6Y2xpZW50X2NyZWRlbnRpYWxzIHJlYWQ6b3JnYW5pemF0aW9uX2NsaWVudF9ncmFudHMgY3JlYXRlOm9yZ2FuaXphdGlvbl9jbGllbnRfZ3JhbnRzIGRlbGV0ZTpvcmdhbml6YXRpb25fY2xpZW50X2dyYW50cyIsImd0eSI6ImNsaWVudC1jcmVkZW50aWFscyIsImF6cCI6Ikloc1MyclE2VmZ5eUc0T0xOaTVsbkI3MWg4aERVWjAxIn0.Dj76Bp1HdX6GjYc3H_BSqpn8SrrvpsEPvQME7gQp2Dw6MqrUJYay3QlmEnuDJ1INGCeYl8Q6NX_IJWcEknslwVb77huz52NosVOmZ39B2z5cv9k6sSQKSJHUwPdflBN5gqAYYADn6aou3dcSyc3IZwjooEX-xACcH9vrPP7A6n8Ztlx9wT5v_FDHTu6Wrf4WC3chrN0PLUB-Ch0PJ_j33tXAQInfmBgWrzDszwEDCc-6BlnYppWYslJBcQqzMfx22vcFt6R4pfRjlFYOOvAxXKmVdy2TznZ8rD5fSGhMJRupA1eNLZbTst-IoOF9CTUygBjcm5BgSbiS6N9BLHcb-g"
@app.route("/create_user", methods=["POST"])
def create_user():
    # Check if the request contains necessary data
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Prepare the payload for the new user
    user_data = {
        "email": email,
        "password": password,
        "connection": "Username-Password-Authentication",  # Auth0's default database connection
        "email_verified": True,  # Set to True if email is verified
    }

    # Make a POST request to the Auth0 Management API to create the user
    response = requests.post(
        f'https://{env.get("AUTH0_DOMAIN")}/api/v2/users',
        headers={
            'Authorization': f'Bearer {AUTH0_MANAGEMENT_API_TOKEN}',
            'Content-Type': 'application/json',
        },
        json=user_data
    )

    if response.status_code == 201:
        return jsonify({"message": "User created successfully!", "user": response.json()}), 201
    else:
        return jsonify({"error": "Failed to create user", "details": response.json()}), response.status_code
    
@app.route("/password_change", methods=["POST"])
def password_change():
    # Extract the email from the request
    data = request.get_json()
    email = data.get("email")
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    # Prepare the request to trigger the password change email
    password_reset_data = {
        "client_id": env.get("AUTH0_CLIENT_ID"),  # Your Auth0 Application Client ID
        "email": email,
        "connection": "Username-Password-Authentication",  # Auth0's default database connection
    }

    # Make a POST request to the Auth0 Management API to send the password reset email
    response = requests.post(
        f'https://{AUTH0_DOMAIN}/dbconnections/change_password',
        headers={
            'Authorization': f'Bearer {AUTH0_MANAGEMENT_API_TOKEN}',
            'Content-Type': 'application/json',
        },
        json=password_reset_data
    )

    if response.status_code == 200:
        return jsonify({"message": "Password change email sent successfully."}), 200
    else:
        return jsonify({"error": "Failed to send password change email", "details": response.json()}), response.status_code
@app.route("/accessVerify", methods=["POST"])
def access_verify():
    try:
        data = request.json
        email = data.get("email")

        if not email:
            logging.error("Email is required for access verification.")
            return jsonify({"error": "Email is required"}), 400

        logging.info(f"Access verification requested for email: {email}")

        # Verify user access
        connection = mysql.connector.connect(
            host="xcite-rds.cqdlazquunbi.ap-southeast-2.rds.amazonaws.com",
            user="admin",
            password="emaxC192g47",
            database="xcite-db"
        )
        if connection.is_connected():
            cursor = connection.cursor()

        try:
            cursor.execute("SELECT access FROM Employees WHERE email = %s", (email,))
            result = cursor.fetchone()

            if result:
                access = result[0]  # result is a tuple, access is the first element
                is_admin = access.lower() == "admin"  # Check if the access is admin
                logging.info(f"Access check complete for email: {email}, access: {access}")

                # Create response and add CORS headers
                return  make_response(jsonify({"access": is_admin}), 200)

            else:
                logging.info(f"No user found with email: {email}")
                return jsonify({"error": "User not found"}), 404
        except Exception as e:
            logging.error(f"Error querying database for access: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
        finally:
            if cursor:
                cursor.close()

    except Exception as e:
        logging.error(f"Error in access verification: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        # Ensure the connection is returned to the pool
        if connection.is_connected():
            connection.close()

@app.route("/getcontacts", methods=["GET"])
def get_contacts():
    logging.info("Processing request to get contacts.")
    connection = None
    cursor = None
    try:
        # Establish connection to the database
        connection = mysql.connector.connect(
            host="xcite-rds.cqdlazquunbi.ap-southeast-2.rds.amazonaws.com",
            user="admin",
            password="emaxC192g47",
            database="xcite-db"
        )

        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT id, company, role, firstName, lastName, email, phone, access FROM Employees")

            # Fetch and format results
            contacts = [
                {
                    "id": row[0],
                    "company": row[1],
                    "role": row[2],
                    "firstName": row[3],
                    "lastName": row[4],
                    "email": row[5],
                    "phone": row[6],
                    "access": row[7],
                }
                for row in cursor.fetchall()
            ]

            logging.info(f"Successfully retrieved {len(contacts)} contacts.")
            
            # Prepare response
            return make_response(jsonify(contacts), 200)
            
    except mysql.connector.InterfaceError as conn_err:
        logging.error(f"Database connection error: {conn_err}")
        return jsonify({"error": "Could not connect to the database. Please try again later."}), 500

    except mysql.connector.Error as db_err:
        logging.error(f"Database error occurred: {db_err}")
        return jsonify({"error": "Database query failed. Please contact support."}), 500

    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

    finally:
        # Ensure resources are properly closed
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

            
@app.route("/createEmployee", methods=["POST"])
def create_employee():
    try:
        data = request.json
        company = data.get("company")
        role = data.get("role")
        first_name = data.get("firstName")
        last_name = data.get("lastName")
        email = data.get("email")
        phone = data.get("phone")
        access = data.get("access")
        employee_id = data.get("id")

        if not all([company, role, first_name, last_name, email, phone, access, employee_id]):
            logging.error("Missing required employee data.")
            return jsonify({"error": "All employee fields are required"}), 400

        logging.info(f"Received new employee data: {data}")

        # Insert the new employee into the database
        connection = mysql.connector.connect(
            host="xcite-rds.cqdlazquunbi.ap-southeast-2.rds.amazonaws.com",
            user="admin",
            password="emaxC192g47",
            database="xcite-db"
        )

        if connection.is_connected():
            cursor = connection.cursor()
        # Correct the query to pass parameters as a tuple or dictionary
        query = """
            INSERT INTO Employees (id, company, role, firstName, lastName, email, phone, access)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (employee_id, company, role, first_name, last_name, email, phone, access))

        # Commit the transaction
        connection.commit()

        logging.info(f"Employee {first_name} {last_name} added successfully.")
        return jsonify({"message": "Employee created successfully"}), 201

    except pyodbc.Error as db_err:
        logging.error(f"Database error occurred: {db_err}")
        return jsonify({"error": "Database query failed. Please contact support."}), 500

    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500
    finally:
    # Ensure the connection is returned to the pool
        cursor.close()
        connection.close()

@app.route('/deleteEmployee', methods=['DELETE'])
def delete_employee():
    connection = None
    cursor = None
    try:
        # Establish connection to the database
        connection = mysql.connector.connect(
            host="xcite-rds.cqdlazquunbi.ap-southeast-2.rds.amazonaws.com",
            user="admin",
            password="emaxC192g47",
            database="xcite-db"
        )

        if not connection.is_connected():
            return jsonify({"error": "Database connection failed"}), 500

        cursor = connection.cursor()

        # Parse employee IDs from request
        employee_ids = employee_ids = request.json.get("ids", [])
        if not employee_ids:
            return jsonify({"error": "No employee IDs provided"}), 400

        # Perform the delete operation for each ID
        for emp_id in employee_ids:
            cursor.execute("DELETE FROM Employees WHERE id = %s", (emp_id,))

        # Commit the transaction
        connection.commit()

        return jsonify({"message": f"Deleted {cursor.rowcount} employees successfully"})

    except mysql.connector.Error as db_err:
        app.logger.error(f"Database error: {db_err}")
        return jsonify({"error": "Database error occurred"}), 500

    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


@app.route("/updateEmployee", methods=["PUT"])
def update_employee():
    connection = None
    cursor = None
    try:
        # Parse request JSON
        employee_data = request.json
        logging.info(f"Received update request for employee data: {employee_data}")

        employee_id = employee_data.get("id")
        company = employee_data.get("company")
        role = employee_data.get("role")
        first_name = employee_data.get("firstName")
        last_name = employee_data.get("lastName")
        email = employee_data.get("email")
        phone = employee_data.get("phone")

        if not employee_id:
            return jsonify({"error": "Employee ID is required for updating."}), 400

        # Establish connection to MySQL database
        connection = mysql.connector.connect(
            host="xcite-rds.cqdlazquunbi.ap-southeast-2.rds.amazonaws.com",
            user="admin",
            password="emaxC192g47",
            database="xcite-db"
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # SQL query to update employee details
            query = """
                UPDATE Employees
                SET company = %s, role = %s, firstName = %s, lastName = %s, email = %s, phone = %s
                WHERE id = %s
            """
            cursor.execute(query, (company, role, first_name, last_name, email, phone, employee_id))
            connection.commit()

            logging.info(f"Successfully updated employee with ID: {employee_id}")
            return jsonify({"message": f"Employee with ID {employee_id} updated successfully."}), 200

    except mysql.connector.Error as db_err:
        logging.error(f"Database error occurred: {db_err}")
        return jsonify({"error": "Database query failed. Please contact support."}), 500

    except Exception as e:
        logging.error(f"Unexpected error occurred: {str(e)}")
        return jsonify({"error": "An unexpected error occurred. Please try again later."}), 500

    finally:
        # Ensure cursor and connection are closed
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# @app.route('/verify', methods=['GET'])
# def verify_email():
#     try:
#         token = request.args.get("token")
#         if not token:
#             return redirect("http://localhost:3000/verify?status=error&message=Token is required")
        
#         token_data = email_tokens.get(token)
#         if not token_data:
#             return redirect("http://localhost:3000/verify?status=error&message=Invalid or expired token")
        
#         # Check if the token has expired
#         elapsed_time = time.time() - token_data["created_at"]
#         if elapsed_time > TOKEN_EXPIRATION_SECONDS:
#             del email_tokens[token]  # Optionally delete expired tokens
#             return redirect("http://localhost:3000/verify?status=error&message=Token has expired")
        
#         # Mark the user as verified in the database
#         email = token_data["email"]
#         with pyodbc.connect(connection_string) as conn:
#             cursor = conn.cursor()
#             cursor.execute("UPDATE Employees SET verified = 1 WHERE email = ?", email)
#             conn.commit()

#         # Remove the token after successful verification
#         del email_tokens[token]

#         redirect_url = f"https://dev-pcr70d42ubxbk16j.us.auth0.com/authorize?response_type=code&client_id=kSokpC43OMc4xESHAGgYwCIQrwCjZzV3&redirect_uri=http://localhost:3000/dashboard"
#         return redirect(redirect_url)

#     except Exception as e:
#         logging.error(f"Error in email verification: {e}")
#         return redirect("http://localhost:3000/verify?status=error&message=Internal server error")



# POSTMARK_API_URL = "https://api.postmarkapp.com/email/withTemplate"

# @app.route("/sendVerificationEmail", methods=["POST"])
# def send_verification_email():
#     try:
#         data = request.json
#         email = data.get("email")
#         name = data.get("name")

#         if not email:
#             logging.error("Email is required to send verification.")
#             return jsonify({"error": "Email is required"}), 400
        
#         if not name:
#             logging.error("Name is required to send verification.")
#             return jsonify({"error": "Name is required"}), 400

#         # Generate a unique token
#         token = str(uuid4())
#         email_tokens[token] = {"email": email, "created_at": time.time()}

#         # Generate the verification link
#         verification_link = f"http://localhost:3000/verify?token={token}"

#         # Prepare the template payload
#         payload = {
#             "TemplateId": 38333485,  # Replace with your actual template ID
#             "TemplateAlias": "user-invitation",  # Replace with your actual template alias
#             "TemplateModel": {
#                 "action_url": verification_link,  # This depends on your template variables
#                 "name": name,
#                 "invite_sender_name": "xciteSolutions",
#                 "product_name": "MallFit"
                
#             },
#             "From": "amelia.khor@xcitesolutions.com.au",  # Replace with your sender email
#             "To": email,
            
#             "TrackOpens": True,
#             "InlineCss": True
#         }

#         # Send the email via Postmark
#         headers = {
#             "X-Postmark-Server-Token": POSTMARK_SERVER_TOKEN,
#             "Content-Type": "application/json",
#         }

#         response = requests.post(POSTMARK_API_URL, json=payload, headers=headers)

#         # Check the response
#         if response.status_code == 200:
#             logging.info(f"Verification email sent to {email}")
#             return jsonify({"message": "Verification email sent"}), 200
#         else:
#             logging.error(f"Failed to send verification email: {response.json()} - {response.status_code}")
#             return jsonify({"error": "Failed to send verification email"}), 500

#     except Exception as e:
#         logging.error(f"Error sending verification email: {e}")
#         return jsonify({"error": "An unexpected error occurred"}), 500

# @app.route('/send-invite', methods=['POST'])
# def send_invitation():
#     data = request.json
#     email = data["email"]
#     name = data["name"]

#     # Get Management API token
#     token = get_management_token()

#     # Use the Management API to send the invitation
#     url = f"https://{AUTH0_DOMAIN}/api/v2/users"
#     headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
#     payload = {
#         "email": email,
#         "name": name,
#         "connection": "email",  # Or any configured connection
#         "email_verified": False
#     }
#     response = requests.post(url, json=payload, headers=headers)
#     if response.status_code == 201:
#         return jsonify({"message": "User invited successfully"}), 201
#     else:
#         return jsonify({"error": response.json()}), response.status_code


# def verify_token():
#     token = request.headers.get('Authorization')
#     if not token:
#         return {'message': 'Token is missing'}, 401

#     try:
#         # Decode the token and verify it
#         decoded_token = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
#     except jwt.ExpiredSignatureError:
#         return {'message': 'Token has expired'}, 401
#     except jwt.InvalidTokenError:
#         return {'message': 'Invalid token'}, 401

#     # Attach user info to request if needed
#     request.user = decoded_token


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)


