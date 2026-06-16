from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1> Home Page </h1>"

@app.route("/login")
def login():
    return render_template('auth/login.html')

@app.route("/register")
def register():
    return render_template('auth/register.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)