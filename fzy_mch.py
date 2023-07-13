from flask import Flask, request
from flask_cors import CORS
from loguru import logger
import jellyfish
from fuzzywuzzy import fuzz
import csv

app = Flask(__name__)
CORS(app)



def gen_resp(code, msg, data):
    return {
            "respcode": str(code), 
            "respdesc" : msg,
            "data" : data      
    }

def jaro_winkler_distance(str1, str2, prefix_weight=0.1, threshold=0.7):
    # Compute Jaro distance
    len1, len2 = len(str1), len(str2)
    match_distance = max(len1, len2) // 2 - 1
    matchestring1 = [-1] * len(str1)
    matchestring2 = [-1] * len(str2)
    matches = 0
    for i in range(len1):
        low, high = max(0, i - match_distance), min(i + match_distance + 1, len2)
        for j in range(low, high):
            if str1[i] == str2[j] and matchestring2[j] == -1:
                matchestring1[i] = j
                matchestring2[j] = i
                matches += 1
                break
    if matches == 0:
        return 0
    transpositions = 0
    k = 0
    for i in range(len1):
        if matchestring1[i] != -1:
            while k < len2:
                if matchestring2[k] != -1:
                    if matchestring1[i] == k:
                        k += 1
                        break
                    else:
                        k += 1
                else:
                    k += 1
            if str1[i] != str2[matchestring1[i]]:
                transpositions += 1
    transpositions //= 2
    jaro_distance = (matches / len1 + matches / len2 + (matches - transpositions) / matches) / 3.0
    # Compute Jaro-Winkler distance
    jaro_winkler_distance = jaro_distance
    prefix_len = 0
    for i in range(min(len1, len2)):
        if str1[i] == str2[i]:
            prefix_len += 1
        else:
            break
    prefix_len = min(prefix_len, 4)
    jaro_winkler_distance += prefix_len * prefix_weight * (1 - jaro_distance)
    # return jaro_winkler_distance if jaro_winkler_distance >= threshold else 0.0
    return jaro_winkler_distance


@app.route('/fuzzy',methods = ['POST'])
def fuzzy_match_api():
    # logger.info("Entering to personal messages tracker api")

    try:
        response = request.json
    except Exception as e:
        logger.error("at request.json: ", e)
        #logger.info(f'Invalid json txnid:{txnid}')
        return gen_resp(401,"invalid request","")

    try:
        string1 = str(response['string1']).replace("Mr.", "").replace("Mr ", "").replace("Mrs.", "").replace("Mrs ", "").replace("Miss ", "").lower()
        string2 = str(response['string2']).replace("Mr.", "").replace("Mr ", "").replace("Mrs.", "").replace("Mrs ", "").replace("Miss ", "").lower()

    except Exception as e:
        logger.error("at reading strings: ", e)
        return gen_resp(402,"Missing Keys","")

    data = [
        jellyfish.jaro_winkler(string1, string2),
        fuzz.token_set_ratio(string1, string2),
        fuzz.token_sort_ratio(string1, string2),
        jellyfish.levenshtein_distance(string1, string2),
        fuzz.ratio(string1, string2)
        ]
            
    data.sort()
    finalvalue = {
        "string1": string1,
        "string2": string2,
        "fuzzy_match_ratio": data[-1]}
    
    with open('fuzzy_match.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        # writer.writerow(finalvalue.keys())
        writer.writerow(finalvalue.values())

    
    try:
        return gen_resp(200,"success",finalvalue)
    except Exception as e:
        return gen_resp(500, "Error", "")


if __name__ == '__main__':
    app.run(threaded=False, host='localhost', port=int(5004), debug=True)