from flask import Flask, request, jsonify, make_response
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from flask_cors import CORS
from dotenv import load_dotenv
import os
import atexit
import firebase_admin
import pyrebase
from firebase_admin import firestore, auth, credentials
import json
import time
from openai import OpenAI
import re
from datetime import datetime, timedelta,timezone
from detection import loading_models, prediction

food_or_not_food_model,healthy_junk_indian_model,fruits_vegetables_model,indian_foods_model = loading_models()

load_dotenv()

def count_tokens(sentence):
    pattern = r'\w+|[^\w\s]'
    tokens = re.findall(pattern, sentence)
    return len(tokens)

def configFirebase_admin():
    try:
        path = os.getcwd() + "/key.json"
        cred = credentials.Certificate(path)
        return firebase_admin.initialize_app(cred)
    except Exception as e:
        print(e)

def configPyrebase_auth():
    cred = json.loads(os.getenv("FIREBASE"))
    firebase = pyrebase.initialize_app(cred)
    return firebase.auth()

def is_admin():
    if 'user' in request.cookies:
        print("isAdmin : " + request.cookies.get('user') == os.getenv("ADMIN_SECRET"))
        print("isUser : " + request.cookies.get('user') != os.getenv("ADMIN_SECRET"))
        return request.cookies.get('user') == os.getenv("ADMIN_SECRET")
    print("not a Admin and not a User : ")
    return False

def get_food_recommender_answer(question,ASSISTANT_ID):
    client = OpenAI()
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ]
    )
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
    print(f"👉 Run Created: {run.id}")
    while run.status != "completed":
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print(f"🏃 Run Status: {run.status}")
        time.sleep(1)
    else:
        print(f"🏁 Run Completed!")
    message_response = client.beta.threads.messages.list(thread_id=thread.id)
    messages = message_response.data
    latest_message = messages[0]
    return latest_message.content[0].text.value


Deliveredapp = Flask(__name__)
CORS(Deliveredapp, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers="*")

UPLOAD_FOLDER = './uploads'
Deliveredapp.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

Deliveredapp.secret_key = os.getenv("SECRET_KEY")

@Deliveredapp.route('/', methods=['GET'])
def home():
    return "<h1>Welcome to nutrispy!</h1>", 200

@Deliveredapp.route('/contact', methods=['POST'])
def contactFirebase():
    if request.method == 'POST':
        configFirebase_admin()
        db = firestore.client()
        data = request.json
        contact_ref = db.collection("contacts").document()
        contact_ref.set(data)
        return jsonify({"response": "Success", "statusCode": 201, "data": "Data has been sent"})

@Deliveredapp.route('/contact', methods=['GET','DELETE'])
def contact_operations():
    if not is_admin():
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Admin privileges required"})
    
    configFirebase_admin()
    db = firestore.client()
    
    if request.method == 'GET':
        contacts_ref = db.collection("contacts").stream()
        contacts = [{"id": contact.id, **contact.to_dict()} for contact in contacts_ref]
        if contacts:
            return jsonify({"response": "success", "statusCode": 200, "data": contacts})
        else:
            return jsonify({"response": "Failed", "statusCode": 404, "data": "No contacts found"})
    
    elif request.method == 'DELETE':
        contacts_ref = db.collection("contacts")
        contacts = contacts_ref.stream()
        for contact in contacts:
            contact.reference.delete()
        return jsonify({"response": "success", "status": 200, "data": "All contacts deleted successfully"}) 

@Deliveredapp.route('/contact/<contact_id>', methods=['DELETE'])
def deleteContact(contact_id):
    if not is_admin():
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Admin privileges required"})
    
    configFirebase_admin()
    db = firestore.client()
    contact_ref = db.collection("contacts").document(contact_id)
    contact = contact_ref.get()
    if contact.exists:
        contact_ref.delete()
        return jsonify({"response": "success", "status": 200, "message": "Contact deleted successfully"})
    else:
        return jsonify({"response": "failure", "status": 404, "message": "Contact not found"})

@Deliveredapp.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        if 'user' in request.cookies:
            return jsonify({"response": "Failed", "statusCode": 400, "data": "User is already logged in"})
        
        email = request.json['email']
        password = request.json['password']
        user = None
        try:
            authenticate = configPyrebase_auth()
            configFirebase_admin()
            user = auth.get_user_by_email(email=email)
            
            if user:
                try:
                    auth_user = authenticate.sign_in_with_email_and_password(user.email, password)
                    if user.email == os.getenv("ADMIN_EMAIL"):
                        user_type = "admin"
                    else:
                        user_type = "user"
                    resp = make_response(jsonify({"response": "Success", "statusCode": 200, "data": {"userType": user_type, "message": f"Successfully logged in. Welcome {auth_user['email']}"} }))
                    resp.set_cookie('user', auth_user['localId'],samesite='Strict', httponly=False)
                    return resp
                except Exception as e:
                    return jsonify({"response":"Failed","statusCode":404,"data": "Invalid Password" })
            else:
                return jsonify({"response": "Failed", "statusCode": 404, "data":f"Invalid, No user with email id present {email}"})
        except Exception as e:
            return jsonify({"response": "Failed", "statusCode": 404, "data": e.args[0] } )

@Deliveredapp.route('/logout', methods=['GET'])  
def logout():
    if 'user' in request.cookies:
        resp = make_response(jsonify({"response": "Success", "statusCode": 200, "data": "Successfully logged out"}))
        resp.set_cookie('user',samesite='Strict', httponly=False, expires=0)
        return resp
    else:
        return jsonify({"response":"Failed","statusCode":404,"data":"First login to log out !"})

@Deliveredapp.route('/detect', methods=['GET','POST'])
def food_detection():
    if is_admin():
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Admins cannot access this route"})
    elif 'user' in request.cookies:
        if request.method == 'POST':
            if 'image' not in request.files:
                return 'there is no image in form!'
            file1 = request.files['image']
            path = os.path.join(Deliveredapp.config['UPLOAD_FOLDER'], "image.png")
            file1.save(path)
            output = prediction(path,food_or_not_food_model,healthy_junk_indian_model,fruits_vegetables_model,indian_foods_model)
        return jsonify({"response": "Success", "statusCode": 200, "data":output})
    else:
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Login to use this feature"})


@Deliveredapp.route('/detect/data', methods=['GET','POST'])
def data_storage():
    if is_admin():
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Admins cannot access this route"})
    elif 'user' in request.cookies:
        user_id = request.cookies.get('user')
        configFirebase_admin()
        db = firestore.client()
        user_conv_ref = db.collection('users').document(user_id).collection('detection_data')

        # Current time
        now = datetime.now(timezone.utc)

        if request.method == 'POST':
            detection_data = request.json
            detection_data['timestamp'] = now
            user_conv_ref.add(detection_data)
            answer = get_food_recommender_answer(question=str(detection_data),ASSISTANT_ID = os.getenv("DETECTION_OVERVIEW_ASSISTANT_ID"))
            return jsonify({"response": "Success", "statusCode": 200, "data": answer})
        else:
            # Calculate the time one week ago from now
            one_week_ago = now - timedelta(days=7)

            # Delete old data
            old_data_query = user_conv_ref.where('timestamp', '<', one_week_ago)
            old_data = old_data_query.stream()
            for data in old_data:
                user_conv_ref.document(data.id).delete()

            # Fetch the latest data
            user_conv_query = user_conv_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
            latest_detection_data = user_conv_query.stream()
            final_detection_data = [{"id": data.id, **data.to_dict()} for data in latest_detection_data]
            return jsonify({"response": "Success", "statusCode": 200, "data": final_detection_data})
    else:
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Login to use this feature"})


@Deliveredapp.route('/recommend', methods=['GET','POST'])
def recommendation():
    if is_admin():
        return jsonify({"response": "unauthorized", "statusCode": 401, "data": "Admins cannot access this route"})
    elif 'user' not in request.cookies:
        return jsonify({"response": "Failed", "statusCode": 401, "data": "User not logged in"})
    
    user_id = request.cookies.get('user')

    configFirebase_admin()
    db = firestore.client()
    
    if request.method == 'POST':
        question = request.json["question"]
        if(count_tokens(question) > 100):
            return jsonify({"response": "Failed", "statusCode": 404,"data": "Request cannot exceed 100 tokens."})
        answer = get_food_recommender_answer(question=str(question),ASSISTANT_ID = os.getenv("NUTRISPY_ASSISTANT_ID"))
        conversation = {
            "question" : question,
            "answer" : answer,
            "timestamp": datetime.datetime.now()
        }
        
        user_conv_ref = db.collection('users').document(user_id).collection('conversations')
        new_conv_ref = user_conv_ref.add(conversation)
        
        user_conv_query = user_conv_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(11)  # Fetch 11 to check for excess
        
        latest_conversations = user_conv_query.get()
        
        if len(latest_conversations) > 10:
            excess_conversations = latest_conversations[10:]
            for conv in excess_conversations:
                conv.reference.delete()
        
        return jsonify({"response": "Success", "statusCode": 200, "data": answer})
    
    elif request.method == 'GET':
        user_conv_ref = db.collection('users').document(user_id).collection('conversations')
        user_conv_query = user_conv_ref.order_by('timestamp').limit(10)
        latest_conversations = user_conv_query.stream()
        conversations_data = [{"id": conv.id, **conv.to_dict()} for conv in latest_conversations]
        
        return jsonify({"response": "Success", "statusCode": 200, "data": conversations_data})

@Deliveredapp.route('/check_session')
def check_session():
    if 'user' in request.cookies:
        return jsonify({"User ID" : request.cookies.get('user')})
    else:
        return jsonify({"User ID" : None})

app = Flask(__name__)

def clear_session():
    resp = make_response(jsonify({"response": "Success", "statusCode": 200, "data": "Session cleared successfully"}))
    resp.set_cookie('user_id', '', expires=0)
    return resp

atexit.register(clear_session)

app.wsgi_app = DispatcherMiddleware(NotFound, {"/api/v1": Deliveredapp})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30000, debug=True)
