from flask import Flask, request, render_template, redirect, jsonify
import pandas as pd

app = Flask(__name__)

#Login Page
@app.route('/', methods=['GET'])
def home():
    try:
        return render_template('login.html'), 200
    except Exception as e:
        error_message = f"Error rendering template: {e}"
        return jsonify({'error': error_message}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        username = request.form['UserID']
        password = request.form['Password']

        authenticated, role = authenticate(username,password)

        if authenticated:
            user = get_user_from_username(username)
            login_user(user)
        else:
            return "Invalid UserID or Password", 401
        
        return redirect(url_for('security.security')), 302
    except HTTPException as http_error:
        return jsonify({'error': str(http_error)}), http_error.code
    except Exception as e:
        return jsonify({'error': f"Internal Server Error: {e}"}), 500







if __name__ == "__main__":
    app.run(host='0.0.0.0', port="5000", debug=True)
