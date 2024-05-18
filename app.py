from flask import Flask, render_template, request, jsonify
from flask import redirect, url_for, session
from flask_session import Session
import requests
# import prompt as pr
import json
from bs4 import BeautifulSoup
import boto3
from boto3.dynamodb.conditions import Key
import os
from utils.autograder import AutoGrader
from decimal import Decimal

AWS_S3_CREDS = {
    "aws_access_key_id":"",
    "aws_secret_access_key":""
}

# AWS Cognito configuration
COGNITO_REGION = 'us-east-2'
COGNITO_USER_POOL_ID = 'us-east-2_HwZ44KvGn'
COGNITO_APP_CLIENT_ID = '7l2peolctv8q0gs9b6j0it84ur'

cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION, **AWS_S3_CREDS)

# DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-2', **AWS_S3_CREDS) 
table = dynamodb.Table('UserScores')

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Route for handling the index page
@app.route('/')
def index():
    return render_template('index.html')

# Route for handling the form submission and showing results
@app.route('/login', methods=['GET', 'POST'])
def login_function():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Authenticate user with Cognito
        try:
            response = cognito_client.initiate_auth(
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': email,
                    'PASSWORD': password
                },
                ClientId=COGNITO_APP_CLIENT_ID
            )
            session['logged_in'] = True
            session['user_email'] = email
            # session['access_token'] = response['AuthenticationResult']['AccessToken']
            return redirect(url_for('result'))  # Redirect to index page after successful login
        except Exception as e:
            error_message = str(e)
            return render_template('login.html', error_message=error_message)
        
    return render_template('login.html')

@app.route('/logout', methods=["POST"])
def logout():
    session['logged_in'] = False
    session.pop('user_email', None)
    return redirect(url_for('index'))

# Route for handling the form submission and showing results
@app.route('/signup', methods=['GET', 'POST'])
def signup_function():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if the email is from the sjsu.edu domain
        if not email.endswith('@sjsu.edu'):
            return render_template('signup.html', error_message='Access restricted. Please use your SJSU email.')
        
        try:
            # Attempt to register the user
            cognito_client.sign_up(
                ClientId=COGNITO_APP_CLIENT_ID,
                Username=email,
                Password=password,
                UserAttributes=[
                    {
                        'Name': 'email',
                        'Value': email
                    }
                ]
            )
            return redirect(url_for('confirm', email=email))  # Redirect to the confirmation page
        except cognito_client.exceptions.UsernameExistsException:
            return render_template('signup.html', error_message='This email is already used.')
        except Exception as e:
            return render_template('signup.html', error_message=str(e))
    return render_template('signup.html')

@app.route('/confirm', methods=['GET', 'POST'])
def confirm():
    email = request.args.get('email', '')  # Get email from query parameters if GET
    if request.method == 'POST':
        code = request.form['code']
        try:
            cognito_client.confirm_sign_up(
                ClientId=COGNITO_APP_CLIENT_ID,
                Username=email,
                ConfirmationCode=code
            )
            return redirect(url_for('login_function'))  # Redirect to login page after confirming
        except Exception as e:
            return render_template('confirm.html', email=email, error_message=str(e))
    return render_template('confirm.html', email=email, error_message='')


# Dictionary to store initial code templates for each PDF
initial_code_templates = {
    "Sum2.pdf": "def add(a, b):",
    "KnightAttack.pdf": "def knight_attack(n, kr, kc, pr, pc):",
    # Add more templates for other PDFs as needed
}

@app.route('/get_initial_code', methods=['POST'])
def get_initial_code():
    pdf_name = request.json.get('pdf_name')
    initial_code = initial_code_templates.get(pdf_name, "# No initial code available\n")
    return jsonify({"initial_code": initial_code})

# Route for handling the form submission and showing results
@app.route('/result', methods=['GET', 'POST'])
def result():
    if not session.get('logged_in'):
        return redirect(url_for('login_function'))
    
    pdf_files = [f for f in os.listdir('static/pdf') if f.endswith('.pdf')]
    user_email = session.get('user_email')
    
    # Fetch user scores from DynamoDB
    response = table.query(
        KeyConditionExpression=Key('user_email').eq(user_email)
    )
    user_scores = {item['pdf_name']: item['best_score'] for item in response.get('Items', [])}

    return render_template('result.html', pdf_files=pdf_files, user_email=user_email, initial_code="", user_scores=user_scores)
    # return render_template('result.html')

@app.route('/submit_code', methods=['POST'])
def submit_code():
    if not session.get('logged_in'):
        return redirect(url_for('login_function'))
    
    user_email = session['user_email']
    question = request.form['selectedQuestion']
    file = request.files['file']
    filename = file.filename
    user_directory = os.path.join('uploads', question)
    question_directory = os.path.join(user_directory, question)
    if not os.path.exists(question_directory):
        os.makedirs(question_directory)
    filepath = os.path.join(question_directory, filename)
    file.save(filepath)

    # Grade the solution
    grader = AutoGrader(question, filepath)
    passed_tests, total_tests, score, results = grader.grade()

    # Check and update best score in DynamoDB
    score = Decimal(score).quantize(Decimal('0.00'))  # Ensure score is a Decimal
    response = table.get_item(
        Key={
            'user_email': user_email,
            'pdf_name': question
        }
    )
    if 'Item' in response:
        best_score = response['Item']['best_score']
        if score > best_score:
            table.update_item(
                Key={
                    'user_email': user_email,
                    'pdf_name': question
                },
                UpdateExpression='SET best_score = :val1',
                ExpressionAttributeValues={
                    ':val1': score
                }
            )
    else:
        print(type(score), score)
        table.put_item(
            Item={
                'user_email': user_email,
                'pdf_name': question,
                'best_score': score
            }
        )

    result = {
        'testsPassed': passed_tests,
        'totalTests': total_tests,
        'score': f'{score}%',
        'results': results
    }
    print(result)
    return jsonify(result)

@app.route('/get_best_score', methods=['POST'])
def get_best_score():
    user_email = session['user_email']
    pdf_name = request.json.get('pdf_name')
    
    response = table.get_item(
        Key={
            'user_email': user_email,
            'pdf_name': pdf_name
        }
    )
    
    best_score = response['Item']['best_score'] if 'Item' in response else "Make your first attempt, you can do it!!"
    return jsonify({"best_score": best_score})

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True, host='0.0.0.0', port='8080')
