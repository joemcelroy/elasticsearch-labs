from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from queue import Queue
from uuid import uuid4
from chat import ask_question, parse_stream_message
import threading
import os
import sys

from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__, static_folder="../frontend/build", static_url_path="/")
CORS(app)


@app.route("/")
def api_index():
    return app.send_static_file("index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    request_json = request.get_json()
    question = request_json.get("question")
    if question is None:
        return jsonify({"msg": "Missing question from request JSON"}), 400

    stream_queue = Queue()
    session_id = request.args.get("session_id", str(uuid4()))

    print("Chat session ID: ", session_id)

    threading.Thread(
        target=ask_question, args=(question, stream_queue, session_id)
    ).start()

    return Response(
        parse_stream_message(session_id, stream_queue), mimetype="text/event-stream"
    )


@app.cli.command()
def create_index():
    """Create or re-create the Elasticsearch index."""
    basedir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(f'{basedir}/../')

    from data import index_data
    index_data.main()


if __name__ == "__main__":
    app.run(port=3001, debug=True)
