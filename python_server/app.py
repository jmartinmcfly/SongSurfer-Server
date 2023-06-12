from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import os
import tiktoken

load_dotenv()

app = Flask(__name__)
print("Running on http:/$/localhost:5000")
print("CORS ORIGINS: " + os.getenv("CORS_ORIGINS"))
CORS(app, origins="*")

# TODO: play with this
MAX_TOKENS = 3500


# TODO: Test this
@app.route("/openai-python/trim-tokens", methods=["POST"])
def trim_tokens():
    """
    Trims down the tokens in a message to ChatGPT to match
    max token requirements.

    ---
    tags:
      - Tokens
    requestBody:
      description: JSON object containing message with tokens
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              messages:
                type: array
                items:
                  type: object
                  properties:
                    role:
                      type: string
                      description: The role of the message ('user' 'system' or 'assistant')
                    content:
                      type: string
                      description: The content of the message
    responses:
      200:
        description: Token trimming successful
        content:
          application/json:
            schema:
              type: object
              properties:
                trimmedMessages:
                  type: array
                  items:
                    type: object
                    properties:
                      role:
                        type: string
                        description: The role of the message ('user' 'system' or 'assistant')
                      content:
                        type: string
                        description: The content of the message
              example:
                trimmedMessages: [
                  {
                    "role": "user",
                    "content": "Hello, how are you?"
                  },
                  {
                    "role": "assistant",
                    "content": "I'm doing well, thanks. How can I help you today?"
                  }
                ]
      400:
        description: Invalid request body
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Failure message
                  example: "Invalid request body"
      500:
        description: Server error
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Failure message
                  example: "Server error"
    """

    request_body = request.json
    response = None

    if (not request_body) or ("messages" not in request.json):
        response = make_response(jsonify({"message": "Invalid request body"}), 400)
    else:
        messageObjects = request_body["messages"]
        print("messageObjects:")
        for obj in messageObjects:
            print(obj)
            print("\n\n\n")
        messagesContent = []
        print("here")
        # create an array of just the message contents
        for message in messageObjects:
            messagesContent.append(message["content"])
        try:
            # count tokens
            totalTokens = num_tokens_from_messages(messagesContent)
            print("messageObjects:")
            for obj in messageObjects:
                print(obj)
                print("\n\n\n")

            # trim tokens iteratively until we're under the limit
            while totalTokens > MAX_TOKENS:
                # keep the prompt message, trim the oldest session message (user or assitant)
                messageObjects = messageObjects[:1] + messageObjects[2:]
                messagesContent = messagesContent[:1] + messagesContent[2:]
                print("messageObjects:")
                for obj in messageObjects:
                    print(obj)
                    print("\n\n\n")
                totalTokens = num_tokens_from_messages(messagesContent)

            response = make_response(jsonify({"trimmedMessages": messageObjects}), 200)
            response.headers.add("Access-Control-Allow-Origin", "*")

            return response
        except Exception as e:
            print("EXCEPTION!")
            print(e)
            response = make_response(
                jsonify({"message": "Server error: " + str(e)}), 500
            )
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response


@app.route("/<path:path>")
def catch_all(path):
    return "You reached %s" % path


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    total_length = 0
    for message in messages:
        total_length += len(message)

    print("total length: " + str(total_length))

    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo-0301":  # note: future models may deviate from this
        num_tokens = 0
        for message in messages:
            num_tokens += (
                4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            )
            num_tokens += len(encoding.encode(message))

        num_tokens += 2  # every reply is primed with <im_start>assistant
        print("num tokens: " + str(num_tokens))

        return num_tokens
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not presently implemented for model {model}.
  See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )


# run the app
if __name__ == "__main__":
    app.run(debug=True)
