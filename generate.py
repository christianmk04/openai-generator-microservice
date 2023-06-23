from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os 
import openai
openai.api_type = "azure"
openai.api_base = "https://gptsmu.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

app = Flask(__name__)
CORS(app)

# GENERATE CHAT COMPLETION
@app.route('/generate_chat_completion/<string:user_api_key>', methods=['POST'])
def generate_cs(user_api_key):

    request_data = request.get_json()

    openai.api_key = user_api_key
    completion = openai.ChatCompletion.create(
        engine="gpt35",
        messages=request_data['messages'],
        max_tokens=2048,
        temperature=1.1,
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        stop=None
    )

    return jsonify(
        {
            'response': completion,
            'code' : 200,
            'message' : 'Successfully generated prompt for chat completion'
        }
    )

##################################################################################################################################################################################################
##################################################################################################################################################################################################
##################################################################################################################################################################################################
'''
FUNCTIONS HERE ARE TO BE USED FOR API CALLS FROM OTHER SOURCES SUCH AS POSTMAN OR OTHER INTERFACES

FUNCTIONS IN THIS SECTION INCLUDE:

- CASE STUDY
    - GENERATE CASE STUDY (api_get_cs)

- INDEPENDENT QUESTIONS AND ANSWERS
    - GENERATE QUESTIONS AND ANSWERS (api_get_qa)

- CASE STUDY QUESTIONS AND ANSWERS
    - GENERATE CASE STUDY + RELATED QUESTIONS AND ANSWERS (api_get_csqa)
'''

# API ROUTES FOR OTHER APPLICATIONS TO CALL AND USE 

# API ROUTE TO GENERATE CASE STUDY
@app.route('/api_get_cs/<string:api_key>/<string:main_topic>/<string:sub_topic>', methods=['GET'])
def api_get_cs(api_key, main_topic, sub_topic):

    # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
    mongo_retrieve_endpoint = "https://urp-resource-uploader.onrender.com/get_case_study/manual/" + main_topic + "/" + sub_topic
    try:
        response = requests.get(mongo_retrieve_endpoint)
    except Exception as e:
        print("Error")
        print(e)

        # GET DATA FROM MONGO MICROSERVICE RESPONSE
    json_data = response.json()
    data = json_data["data"][0]

    ref_case_study = data["content"]

    # SET API KEY - CHECK IF API KEY IS VALID OR ENTERED
    openai.api_key = api_key

    if api_key == '':
        return jsonify({"error": "Unable to proceed. Please enter in API key!"})
    
    # GENERATE CHAT COMPLETION
    try:
        completion = openai.ChatCompletion.create(
            engine = "gpt35",
            messages = [
                {"role": "system", "content": "You are an instructor teaching an Agile and DevOps course, your job is to provide questions and answers for students for the purpose of assessing students purposes. You are currently chatting with a Professor of the course, who is asking you for questions and answers about Agile and DevOps."},
                {"role": "user", "content": f"Can you provide me with a sample case study about {main_topic} that focuses on {sub_topic}? Skip the pleasantries of acknowledging the user and start generating the case study immediately. (Meaning, do not start with 'Sure, here's a case study for...')."},
                {"role": "assistant", "content": f"{ref_case_study}"},
                {"role": "user", "content": f"Please provide me with another case study about {main_topic} that focuses on {sub_topic} following the same format as what you have just generated. Skip the pleasantries of acknowledging the user and start generating the case study immediately as before. (Meaning, do not start with 'Sure, here's a case study for...')"},
            ],
            temperature = 1.1,
            max_tokens = 2048,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None
        )
    except Exception as e:
        return jsonify({"error": e})
    
    generated_case_study = completion.choices[0].message.content

    # UPLOAD CASE STUDY TO DB
    mongo_upload_endpoint = "https://urp-resource-uploader.onrender.com/upload_cs"
    cs_json = {
        "content": generated_case_study,
        "main_topic": main_topic,
        "sub_topic": sub_topic,
        "mode": "api_call"

    }

    try:
        response = requests.post(mongo_upload_endpoint, json=cs_json)
        print(response.text)
    except Exception as e:
        print("Error")
        print(e)
    
    return jsonify(
        {
            "case study": generated_case_study,
            "message" : f"Case study generated for {main_topic} focusing on {sub_topic}. Case study uploaded to database."
        }
    )



# API TO GENERATE QUESTIONS AND ANSWERS
@app.route('/api_get_qa/<string:api_key>/<string:sub_topic>', methods=['GET'])
def api_get_qa(api_key, sub_topic):

    sub_topics = ["Automation", "Software Design", "Version Control", "Software Lifecycle", "Agile Methodologies", "Software Security"]

    # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
    mongo_retrieve_endpoint = "https://urp-resource-uploader.onrender.com/get_ind_questions" + "/manual" + "/" + sub_topic
    try:
        response = requests.get(mongo_retrieve_endpoint)
    except Exception as e:
        print("Error")
        print(e)

    # FORMAT QUESTIONS AND ANSWERS INTO STRING TO BE PUT INTO THE CHAT COMPLETION MESSAGE 
    questions_string = ""
    answers_string = ""

        # GET DATA FROM MONGO MICROSERVICE RESPONSE
        # DATA RETRIEVED IS THE REFERENCE QUESTIONS AND ANSWERS
    json_data = response.json()
    data = json_data["data"]

        # FORMAT QUESTIONS AND ANSWERS 
    for i in range(len(data)):
        questions_string += f'{i+1}. ' + data[i]["question"] + "\n"
        answers_string += f'{i+1}. ' + data[i]["answer"] + "\n"

    print(questions_string)
    print(answers_string)

    # SET API KEY - CHECK IF API KEY IS VALID OR ENTERED
    openai.api_key = api_key

    if api_key == '':
        return jsonify({"error": "Unable to proceed. Please enter in API key!"})
    
    # GENERATE CHAT COMPLETION
    try:
        completion = openai.ChatCompletion.create(
            engine = "gpt35",
            messages = [
                {"role": "system", "content": "You are an instructor teaching an Agile and DevOps course, your job is to provide questions and answers for students for the purpose of assessing students purposes. You are currently chatting with a Professor of the course, who is asking you for questions and answers about Agile and DevOps. "},
                {"role": "user", "content": f"Can you provide me with sample questions and answers about {sub_topic} under Agile/DevOps? Provide the questions and answers in a way where it will require more critical thinking. Format your response in this way:\n\n 'Questions: \n1.\n2.\n3. \n\n Answers: \n1.\n2.\n3.' \n\n Skip the pleasantries of acknowledging the user and start generating the questions and answers immediately. (Meaning, do not start with 'Sure, here's a questions and answers for...')"},
                {"role": "assistant", "content": f"Questions:\n{questions_string}\nAnswers:\n{answers_string}"},
                {"role": "user", "content": "Please provide me with 10 more questions and answers following the same format as what you have just generated. Skip the pleasantries of acknowledging the user and start generating the questions and answers immediately. (Meaning, do not start with 'Sure, here's a questions and answers for...')"},
            ],
            temperature = 1.1,
            max_tokens = 2048,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None
        )
    except Exception as e:
        return jsonify({"error": e})
    
    answers_unformatted = completion.choices[0].message.content.split("Answers:")[1]
    questions_unformatted = completion.choices[0].message.content.split("Answers:")[0].split("Questions:")[1]
    
    mongo_upload_endpoint = "https://urp-resource-uploader.onrender.com/upload_ind_qa"
    qa_json = {
        "mode": "api_call",
        "sub_topic": sub_topic,
        "questions": questions_unformatted,
        "answers": answers_unformatted
    }
    try:
        response = requests.post(mongo_upload_endpoint, json=qa_json)
        print(response)
    except Exception as e:
        print("Error")
        print(e)

    questions_formatted_arr = []
    answers_formatted_arr = []

    questions_split_arr = questions_unformatted.split("\n")
    answers_split_arr = answers_unformatted.split("\n")

    for i in range(len(questions_split_arr)):
        if questions_split_arr[i] != '':
            questions_formatted_arr.append(questions_split_arr[i])
    
    for i in range(len(answers_split_arr)):
        if answers_split_arr[i] != '':
            answers_formatted_arr.append(answers_split_arr[i])

    return jsonify(
        {
            "questions" : questions_formatted_arr,
            "answers" : answers_formatted_arr,
            "message" : f"Questions and answers generated for {sub_topic}. Uploaded generated questions and answers to the database."

        }
    )


# API ENDPOINT TO GENERATE CASE STUDY, QUESTIONS AND ANSWERS
@app.route('/api_get_csqa/<string:api_key>/<string:main_topic>/<string:sub_topic>', methods=['GET'])
def api_get_csqa(api_key, main_topic, sub_topic):

    # CHECK IF SUB_TOPIC IS IN THE LIST OF SUB_TOPICS
    sub_topics = ["Automation", "Software Design", "Version Control", "Software Lifecycle", "Agile Methodologies", "Software Security"]
    if sub_topic not in sub_topics:
        # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
        mongo_retrieve_endpoint = "https://urp-resource-uploader.onrender.com/get_csqa/manual/" + main_topic + "/" + sub_topic
    else:
        # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
        mongo_retrieve_endpoint = "https://urp-resource-uploader.onrender.com/get_csqa/automatic/" + main_topic + "/" + sub_topic
    
    try:
        response = requests.get(mongo_retrieve_endpoint)
        data = response.json()
    except Exception as e:
        print("Error")
        print(e)
    
    case_study = data["case_study"]
    questions = data["questions"]
    answers = data["answers"]

    # FORMAT QUESTIONS AND ANSWERS INTO STRINGS
    questions_string = ""
    answers_string = ""

    for i in range(len(questions)):
        questions_string += f'{i+1}. ' + questions[i] + "\n"
        answers_string += f'{i+1}. ' + answers[i] + "\n"

    # SET API KEY - CHECK IF API KEY IS VALID OR ENTERED
    openai.api_key = api_key

    if api_key == '':
        return jsonify({"error": "Unable to proceed. Please enter in API key!"})

    # GENERATE CHAT COMPLETION
    try:
        completion = openai.ChatCompletion.create(
            engine = "gpt35",
            messages = [
                {"role": "system", "content": "You are an instructor teaching an Agile and DevOps course, your job is to provide questions and answers for students for the purpose of assessing students purposes. You are currently chatting with a Professor of the course, who is asking you for questions and answers about Agile and DevOps. "},
                # REFERENCE PROMPT ENGINEERING FOR CASE STUDY
                {"role": "user", "content": f"Can you provide me with a sample case study about {main_topic} that focuses on {sub_topic}? Skip the pleasantries of acknowledging the user and start generating the case study immediately. (Meaning, do not start with 'Sure, here's a case study for...')."},
                {"role": "assistant", "content": f"{case_study}"},
                # REFERENCE PROMPT ENGINEERING FOR QUESTIONS AND ANSWERS
                {"role": "user", "content": f"Can you provide me with sample questions and answers about the case study above? Where the questions are about {main_topic}, focusing on {sub_topic}? Provide the questions and answers in a way where it will require more critical thinking. Format your response in this way:\n\n 'Questions: \n1.\n2.\n3. \n\n Answers: \n1.\n2.\n3.' \n\n Skip the pleasantries of acknowledging the user and start generating the questions and answers immediately. (Meaning, do not start with 'Sure, here's a case study/questions and answers for...')"},
                {"role": "assistant", "content": f"Questions:\n{questions_string}\nAnswers:\n{answers_string}"},
                {"role": "user", "content": f"Please provide me with another case study, and 10 sample questions and sample answers for the case study above. Have the case study, questions and answers be about {main_topic} which focuses on {sub_topic}. Follow the same format as what you have just generated, such as denoted in the triple apostrophe delimiters: \n\n ''' Case Study:\n (Generated Case Study)\n\nQuestions: \n1.\n2.\n3.\n\n Answers:\n1.\n2.\n3.\n\n ''' \n\n Skip the pleasantries of acknowledging the user and start generating the questions and answers immediately. (Meaning, do not start with 'Sure, here's a case study/questions and answers for...')"},
            ],
            temperature = 1.1,
            max_tokens = 2048,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None
        )
    except Exception as e:
        return jsonify({"error": e})
    
    # FORMAT CASE STUDY, QUESTIONS AND ANSWERS INTO STRINGS
    content = completion.choices[0].message.content

    # GET QUESTIONS AND ANSWERS FIRST
    questions_unformatted = content.split("Answers:")[0].split("Questions:")[1]
    answers_unformatted = content.split("Answers:")[1]
    
    questions_formatted_arr = []
    answers_formatted_arr = []

    questions_split_arr = questions_unformatted.split("\n")
    answers_split_arr = answers_unformatted.split("\n")

    for i in range(len(questions_split_arr)):
        if questions_split_arr[i] != '' and questions_split_arr[i] != ' ':
            questions_formatted_arr.append(questions_split_arr[i])

    for i in range(len(answers_split_arr)):
        if answers_split_arr[i] != '' and answers_split_arr[i] != ' ':
            answers_formatted_arr.append(answers_split_arr[i])

    # GET CASE STUDY
    generated_case_study = content.split("Answers:")[0].split("Questions:")[0].split("Case Study:")[1]

    # SET UP MONGO UPLOAD CS TO MONGO MICROSERVICE
    mongo_upload_cs_endpoint = "https://urp-resource-uploader.onrender.com/upload_cs"
    new_cs = {
        "main_topic" : main_topic,
        "sub_topic" : sub_topic,
        "content" : generated_case_study,
        "mode": "api_call"
    }
    try:
        response = requests.post(mongo_upload_cs_endpoint, json=new_cs)
        print(response)
    except Exception as e:
        print("Error")
        print(e)

    # SET UP MONGO UPLOAD RELATED QA TO MONGO MICROSERVICE
    mongo_upload_qa_endpoint = "https://urp-resource-uploader.onrender.com/upload_qa_for_cs"
    new_qa_data = {
        "main_topic" : main_topic,
        "sub_topic" : sub_topic,
        "mode": "api_call",
        "content": generated_case_study,
        "questions": questions_unformatted,
        "answers": answers_unformatted,
    }
    try:
        response = requests.post(mongo_upload_qa_endpoint, json=new_qa_data)
        print(response)
    except Exception as e:
        print("Error")
        print(e)

    return jsonify(
        {
            "case_study" : generated_case_study,
            "questions" : questions_formatted_arr,
            "answers" : answers_formatted_arr,
            "message" : f"Case study, questions and answers generated for {main_topic} focusing on {sub_topic}. Uploaded all to the database.",
        }
    )

# FLASK APP ROUTE
if __name__ == '__main__':
    app.run(port=5002, debug=True)