import flask
from flask import Flask, jsonify
app = Flask(__name__)

from application.settings    import APPLICATION_NAME

@app.route('/info')
def hello_world():
    return jsonify({
        'framework': 'Flask {}'.format(flask.__version__),
        'application': APPLICATION_NAME,
    })