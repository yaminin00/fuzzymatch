# import jellyfish
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
    matches1 = [-1] * len(str1)
    matches2 = [-1] * len(str2)
    matches = 0
    for i in range(len1):
        low, high = max(0, i - match_distance), min(i + match_distance + 1, len2)
        for j in range(low, high):
            if str1[i] == str2[j] and matches2[j] == -1:
                matches1[i] = j
                matches2[j] = i
                matches += 1
                break
    if matches == 0:
        return 0
    transpositions = 0
    k = 0
    for i in range(len1):
        if matches1[i] != -1:
            while k < len2:
                if matches2[k] != -1:
                    if matches1[i] == k:
                        k += 1
                        break
                    else:
                        k += 1
                else:
                    k += 1
            if str1[i] != str2[matches1[i]]:
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

def choose_value(lst):
    if (lst[1] == lst[2] == lst[3] and lst[0] == lst[4]) or (lst[1] == lst[2] and lst[0] == lst[4]):
        return lst[1]
    elif lst[1] == lst[2] == lst[3]:
        return lst[1]
    elif (lst[1] == lst[2]):
        return lst[1]
    elif (lst[2] == lst[3] and lst[0] != lst[4]):
        return lst[4]
    else:
        return max(lst)


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

        # print(string1)
        # print(string2)
    except Exception as e:
        logger.error("at reading strings: ", e)
        return gen_resp(402,"Missing Keys","")



    # Calculate the ratio of similarity between the two strings
    try:
        data = [
            # "ratio" : fuzz.ratio(string1, string2),
            # "partial_ratio" : fuzz.partial_ratio(string1, string2),
            # "token_sort_ratio" : fuzz.token_sort_ratio(string1, string2),
            # "token_set_ratio" : fuzz.token_set_ratio(string1, string2),
            # "jaro_distance" : jellyfish.jaro_similarity(string1, string2),
            # "jaro_wrinkler" : jellyfish.jaro_winkler_similarity(string1, string2),
            jellyfish.jaro_winkler_similarity(string1, string2),
            fuzz.token_set_ratio(string1, string2)/100,
            fuzz.token_sort_ratio(string1, string2)/100,
            fuzz.ratio(string1, string2)/100,
            jaro_winkler_distance(string1, string2),
            # jellyfish.levenshtein_distance(string1, string2)/100
        ]

        final_data = { "string1" : string1,
                       "string2" : string2,
                       "result" : choose_value(data)
                    }
    
        with open('fuzzy_match_testing.csv', mode='a', newline='') as file:
                writer = csv.writer(file)
                # writer.writerow(final_data.keys())
                writer.writerow(final_data.values())


        # logger.info("jellyfish.jaro_winkler_similarity, fuzz.token_set_ratio, fuzz.token_sort_ratio, fuzz.ratio, jaro_winkler_distance, jellyfish.levenshtein_distance")
        logger.info(f"{string1}, {string2}: {data}")
        # data.sort()
        # finalvalue = data[-1]
        return gen_resp(200,"success",choose_value(data))
    except Exception as e:
        logger.error("at calling jaro_wrinkler_distance function: ", e)
        return gen_resp(500,"error","")


    # try:
    #     jw_distance = fuzz.ratio(string1, string2)
    #     return gen_resp(200,"success",jw_distance)
    # except Exception as e:
    #     logger.error("at calling jaro_wrinkler_distance function: ", e)
    #     return gen_resp(500,"error","")

    # try:
    #     jw_distance = jellyfish.jaro_winkler(string1, string2)
    #     return gen_resp(200,"success",jw_distance)
    # except Exception as e:
    #     logger.error("at calling jaro_wrinkler_distance function: ", e)
    #     return gen_resp(500,"error","")


    # try:
    #     jw_distance=jaro_winkler_distance(string1, string2, prefix_weight=0.1, threshold=0.7)
    #     return gen_resp(200,"success",jw_distance)
    # except Exception as e:
    #     logger.error("at calling jaro_wrinkler_distance function: ", e)
    #     return gen_resp(500,"error","")
    

if __name__ == '__main__':
    app.run(threaded=False, host='localhost', port=int(5004), debug=True)