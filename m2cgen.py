from os import environ
import logging
import requests
import model
import json
import traceback
import ipfshttpclient
import asyncio

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]

logger.info(f"HTTP rollup_server url is {rollup_server}")

client = ipfshttpclient.connect('http://127.0.0.1:5001')

state_path = "/state"

#ipfs aux functions

# async def finish_tx(rollup_server_url):
#     try:
#         response = requests.post(f"{rollup_server_url}/finish", json={})
#         response.raise_for_status()
#         print("Finish tx request sent.")
#     except requests.RequestException as e:
#         print(f"Error finishing tx: {e}")

async def exist_file_ipfs(path):
    try:
        client.files.stat(path)
        return True
    except Exception as e:
        if "file does not exist" in str(e):
            return False
        raise

async def read_file_ipfs(path):
    try:
        return client.cat(path).decode('utf-8')
    except Exception as e:
        if "file does not exist" in str(e):
            return ""
        raise

async def write_file_ipfs(path, data):
    exist = await exist_file_ipfs(path)
    if exist:
        client.files.rm(path)  # Remove file if exists
    client.files.write(path, data.encode(), create=True)

#aux m2cgen functions


def classify(input):
    """
    Predicts a given input's classification using the model generated with m2cgen
    """
    # computes the score from the input
    score = model.score(input)

    # interprets the score to retrieve the predicted class index
    class_index = None
    if isinstance(score, list):
        class_index = score.index(max(score))
    else:
        if (score > 0):
            class_index = 1
        else:
            class_index = 0

    # returns the class specified by the predicted index
    return model.classes[class_index]


def format(input):
    """
    Transforms a given input so that it is in the format expected by the m2cgen model
    """
    formatted_input = {}
    for key in input.keys():
        if key in model.columns:
            # key in model: just copy the value
            formatted_input[key] = input[key]
        else:
            # key not in model: it may need to be transformed due to One Hot Encoding
            # - in OHE, there is a column for each possible key/value combination
            # - a OHE column has value 1 if the entry contains the key/value combination
            # - for each key, there is an extra column <key>_nan for unknown values
            ohe_key = key + "_" + str(input[key])
            ohe_key_unknown = key + "_nan"
            if ohe_key in model.columns:
                formatted_input[ohe_key] = 1
            else:
                formatted_input[ohe_key_unknown] = 1

    # builds output as a list/array with one entry for each column in the model
    output = []
    for column in model.columns:
        if column in formatted_input:
            # uses known value for columns present in input
            output.append(formatted_input[column])
        else:
            # uses value 0 for columns not present in the input (all other OHE columns)
            output.append(0)
    return output

def m2cgen(input):
    logger.info(f"Received data {data}")

    try:
        # retrieves input as string
        logger.info(f"Received input: '{input}'")

        # converts input to the format expected by the m2cgen model
        input_json = json.loads(input)
        input_formatted = format(input_json)

        # computes predicted classification for input and returns the predicted classification
        predicted = classify(input_formatted)
        logger.info(f"Data={input}, Predicted: {predicted}")
        return predicted

    except Exception as e:
        msg = f"Error processing data {data}\n{traceback.format_exc()}"
        logger.error(msg)
        

# data = requests.get(rollup_server + "/get_tx")
# logger.info(f"Got tx {data.content}")

# predicted = m2cgen(data.content)
# logger.info(f"Result of the prediction : {predicted}")

# requests.post(rollup_server + "/finish", json={})

async def main():
    if not await exist_file_ipfs(state_path):
        client.files.mkdir(state_path)

    try:
        data = requests.get(rollup_server + "/get_tx")
        logger.info(f"Got tx {data.content}")
        predictions = m2cgen(data.content)
        logger.info(f"Result of the prediction : {predictions}")
        await write_file_ipfs(f"{state_path}/predictions.json", json.dumps({"predictions": predictions}))
        requests.post(rollup_server + "/finish", json={})
    else:
        print("Invalid input or response format.")

if __name__ == "__main__":
    asyncio.run(main())
