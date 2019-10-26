from flask import Flask, request, jsonify, Response
from .Cb import response
import jwt
from .Db.query import select, insert_update

app = Flask(__name__)


def log(f):
    def wrapper(*args, **kwargs):
        print("url:", request.url)
        print("cookies:", request.cookies)
        print("json body:", request.get_json())
        return f(*args, **kwargs)

    return wrapper


def auth(f):
    def wrapper(*args, **kwargs):
        c = request.cookies
        if c and "bearer_token" in c:
            try:
                print(jwt.decode(c["bearer_token"], "secret"))
                return f(*args, **kwargs)
            except jwt.exceptions.InvalidSignatureError:
                return "Unauthorised, invalid jwt", 401
        return "Unauthorised, invalid cookie", 401

    return wrapper


@app.route("/login", methods=["POST"], endpoint="login")
@log
def login():
    body = request.get_json()
    if body:
        if "uid" in body and "pwd" in body:
            res = select("SELECT * FROM students WHERE college_uid=%s;", (body["uid"],))
            if res[0]["password"] == body["pwd"]:
                r = Response({
                    "bearer_token": jwt.encode({"id": res[0]["id"]}, "secret")
                })
                r.headers.set('Access-Control-Allow-Origin', "*")
                r.set_cookie("bearer_token", jwt.encode({"id": res[0]["id"]}, "secret"), domain="127.0.0.1",
                             max_age=10000,
                             samesite=False)
                return r
    return "Invalid username or password", 401


@app.route('/chat', methods=["GET"], endpoint="chat")
@log
@auth
def chat():
    if "mesg" in request.args:
        r = Response(
            response=response.response(request.args.get("mesg"),
                                       jwt.decode(request.cookies["bearer_token"], "secret")["id"],
                                       response.model))
        return r
    else:
        return "The mesg arg is absent", 400


@app.route("/students-data", methods=["GET"], endpoint="students-data")
@log
@auth
def f():
    args = request.args
    if "uid" in args:
        return jsonify(
            select("SELECT * FROM students,attrs WHERE student_id = id and college_uid=%s;", (args["uid"],)))
    elif "branch" in args:
        return jsonify(select("SELECT * FROM students,attrs WHERE student_id = id and branch=%s;", (args["branch"],)))
    elif "student_name" in args:
        return jsonify(
            select("SELECT * FROM students,attrs WHERE student_id = id and name=%s;", (args["student_name"],)))
    else:
        return "required arg not found", 400
