from flask import Flask

app = Flask(__name__)

print('chegou até aqui')

@app.route("/")
def hello():
    return "Hello World Flask - Alpine"


if __name__ == '__main__':
    app.run(host="0.0.0.0")
