from os import environ
import logging
import requests
import json
import traceback
import ipfshttpclient2

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]

logger.info(f"HTTP rollup_server url is {rollup_server}")

try:
    client = ipfshttpclient2.connect('/dns/localhost/tcp/5001/http')
except Exception as e:
    logger.error(f"Failed to connect to IPFS client: {e}")
    raise SystemExit(e)

state_path = "/state"

def exist_file_ipfs(path):
    try:
        client.files.stat(path)
        return True
    except Exception as e:
        if "file does not exist" in str(e):
            return False
        raise

def write_file_ipfs(path, data):
    exist = exist_file_ipfs(path)
    if exist:
        client.files.rm(path)  # Remove file if exists
    client.files.write(path, data.encode(), create=True)

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
    logger.info(f"Received data {input}")

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


if not exist_file_ipfs(state_path):
        client.files.mkdir(state_path)

data = requests.get(rollup_server + "/get_tx")
logger.info(f"Got tx {data.content}")

predictions = m2cgen(data.content)
logger.info(f"Got predictions: {predictions}")

if predictions is not None:
    logger.info(f"Result of the prediction : {predictions}")
    client.files.write(state_path+"/predictions.json", data.encode(), create=True)
    #write_file_ipfs(f"{state_path}/predictions.json", json.dumps({"predictions": predictions}))
    finish_response = requests.post(rollup_server + "/finish", json={})
else:
    logger.error("Failed to get transaction data")


