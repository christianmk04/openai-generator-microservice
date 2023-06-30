from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os 
from dotenv import load_dotenv
import openai
openai.api_type = "azure"
openai.api_base = "https://gptsmu.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

app = Flask(__name__)
CORS(app)

load_dotenv()
generate_api_key = os.getenv("AZURE_OPENAI_API_KEY")

# SET API KEY - CHECK IF API KEY IS VALID OR ENTERED
openai.api_key = generate_api_key

# GENERATE CHAT COMPLETION
@app.route('/generate_chat_completion', methods=['POST'])
def generate_cs():

    request_data = request.get_json()

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

# ENDPOINTS
get_case_study_endpoint = "https://urp-resource-uploader.onrender.com/get_case_study"
upload_cs_endpoint = "https://urp-resource-uploader.onrender.com/upload_cs"
get_ind_questions_endpoint = "https://urp-resource-uploader.onrender.com/get_ind_questions"
upload_ind_qa_endpoint = "https://urp-resource-uploader.onrender.com/upload_ind_qa"
get_csqa_endpoint = "https://urp-resource-uploader.onrender.com/get_csqa/"
upload_qa_for_cs_endpoint = "https://urp-resource-uploader.onrender.com/upload_qa_for_cs"

# API ROUTES FOR OTHER APPLICATIONS TO CALL AND USE 

# API ROUTE TO GENERATE CASE STUDY
@app.route('/api_get_cs', methods=['GET', "POST"])
def api_get_cs():
    input_data = request.get_json()
    api_key = input_data["api_key"]
    main_topic = input_data["main_topic"]
    sub_topic = input_data["sub_topic"]

    sub_topics = ["Automation", "Software Design", "Versioning", "Software Process", "XP", "Support", "Testing", "Security"]

    # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
    if sub_topic in sub_topics:
        raw_data = {
            "main_topic": main_topic,
            "sub_topic": sub_topic,
            "mode" : "automatic"
        }
    else:
        raw_data = {
            "main_topic": main_topic,
            "sub_topic": sub_topic,
            "mode" : "manual"
        }
    
    try:
        response = requests.post(get_case_study_endpoint, json=raw_data)
    except Exception as e:
        print("Error")
        print(e)

    # GET DATA FROM MONGO MICROSERVICE RESPONSE
    json_data = response.json()
    ref_case_study = json_data["data"]["content"]

    if api_key == '':
        return jsonify({"error": "Unable to proceed. Please enter in API key!"})
    
    # GENERATE CHAT COMPLETION
    try:
        completion = openai.ChatCompletion.create(
            engine = "gpt35",
            messages = [
                {"role": "system", "content": "You are an instructor teaching an Agile and DevOps course, your job is to provide questions and answers for students for the purpose of assessing students purposes."},
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
    mongo_upload_endpoint = upload_cs_endpoint
    cs_json = {
        "content": generated_case_study,
        "main_topic": main_topic,
        "sub_topic": sub_topic,
        "mode": "api_call"
    }

    try:
        response = requests.post(mongo_upload_endpoint, json=cs_json)
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
@app.route('/api_get_qa', methods=['POST'])
def api_get_qa():

    input_data = request.get_json()
    sub_topic = input_data["sub_topic"]
    api_key = input_data["api_key"]

    sub_topics = ["Automation", "Software Design", "Versioning", "Software Process", "XP", "Support", "Testing", "Security"]

    # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
    if sub_topic in sub_topics:
        raw_data = {
            "sub_topic": sub_topic,
            "mode" : "automatic"
        }
    else:
        raw_data = {
            "sub_topic": sub_topic,
            "mode" : "manual"
        }

    # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
    try:
        response = requests.post(get_ind_questions_endpoint, json=raw_data)
        # GET DATA FROM MONGO MICROSERVICE RESPONSE
        # DATA RETRIEVED IS THE REFERENCE QUESTIONS AND ANSWERS
        json_data = response.json()
        data = json_data["data"]
    except Exception as e:
        print("Error")
        print(e)

    # FORMAT QUESTIONS AND ANSWERS INTO STRING TO BE PUT INTO THE CHAT COMPLETION MESSAGE 
    questions_string = ""
    answers_string = ""
        # FORMAT QUESTIONS AND ANSWERS 
    for i in range(len(data)-5):
        questions_string += f'{i+1}. ' + data[i]["question"] + "\n"
        answers_string += f'{i+1}. ' + data[i]["answer"] + "\n"

    if api_key == '':
        return jsonify({"error": "Unable to proceed. Please enter in API key!"})
    
    # GENERATE CHAT COMPLETION
    try:
        completion = openai.ChatCompletion.create(
            engine = "gpt35",
            messages = [
                {"role": "system", "content": "You are an instructor teaching an Agile and DevOps course, your job is to provide questions and answers for students for the purpose of assessing students purposes."},
                {"role": "user", "content": f"Provide sample questions and answers about {sub_topic} under Agile/DevOps. Follow this format for the response:\n\n 'Questions: \n1.\n2.\n3. \n\n Answers: \n1.\n2.\n3.' \n\n Skip the pleasantries of acknowledging the user and start generating the questions and answers immediately. (Meaning, do not start with 'Sure, here's a questions and answers for...')"},
                {"role": "assistant", "content": f"Questions:\n{questions_string}\nAnswers:\n{answers_string}"},
                {"role": "user", "content": "Provide 10 more questions and answers following the same format as what you have just generated. Skip the pleasantries of acknowledging the user and start generating the questions and answers immediately. (Meaning, do not start with 'Sure, here's a questions and answers for...')"},
            ],
            temperature = 0.7,
            max_tokens = 2048,
            top_p=1,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None
        )
        
    except Exception as e:
        print('---------------------------------------------------------------------------------------------------------')
        print(e)
        return jsonify({"error": e})
    
    answers_unformatted = completion.choices[0].message.content.split("Answers:")[1]
    questions_unformatted = completion.choices[0].message.content.split("Answers:")[0].split("Questions:")[1]

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

    modified_qn_arr = []
    modified_ans_arr = []
    scoring_array = []

    for i in range(len(questions_formatted_arr)):
        question = questions_formatted_arr[i][3:]
        modified_qn_arr.append(question)
        answer = answers_formatted_arr[i][3:]
        modified_ans_arr.append(answer)
        response = openai.ChatCompletion.create(
            engine="gpt35",
            messages = [
                {"role":"system","content":"You are an AI assistant that helps university students learn agile software development and DevSecOps concepts."},
                {"role":"user","content":"Given this question \"What exactly does continuous integration do?\". Please provide a score between 0 and 4 for the answer given by a student \"Conduct integration testing continuously\"."},
                {"role":"assistant","content":"1.5"},
                {"role":"user","content":"Given this question \"What is one advantage of canary deployment?\". Please provide a score between 0 and 4 for the answer given by a student \"Can minimize the impact of errors to a subset of users\"."},
                {"role":"assistant","content":"4"},
                {"role":"user","content":"Given this question \"What does it mean by A/B testing?\". Please provide a score between 0 and 4 for the answer given by a student \"Test to see which are the better features\"."},
                {"role":"assistant","content":"2.5"},
                {"role":"user","content":"Given this question \"How do we carry out rolling update in production?\". Please provide a score between 0 and 4 for the answer given by a student \"Test to see which are the better features\"."},
                {"role":"assistant","content":"0.5"},
                {"role":"user","content":"Given this question \"How do we carry out rolling update in production?\". Please provide a score between 0 and 4 for the answer given by a student \"update one server at a time while the others continue to handle requests\"."},
                {"role":"assistant","content":"3.5"},
                {"role":"user", "content": f"Given this question \"{question}\". Please provide a score between 0 and 4 for the answer given by a student \"{answer}\"."},
                ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        
        scoring_array.append(response.choices[0].message.content)
        
    
    mongo_upload_endpoint = upload_ind_qa_endpoint
    qa_json = {
        "mode": "api_call",
        "sub_topic": sub_topic,
        "questions": modified_qn_arr,
        "answers": modified_ans_arr,
        "scores": scoring_array
    }
    try:
        response = requests.post(mongo_upload_endpoint, json=qa_json)
        print(response)
    except Exception as e:
        print("Error")
        print(e)

    return jsonify(
        {
            "questions" : questions_formatted_arr,
            "answers" : answers_formatted_arr,
            "scores" : scoring_array,
            "message" : f"Questions and answers generated for {sub_topic}. Uploaded generated questions and answers to the database."
        }
    )


# API ENDPOINT TO GENERATE CASE STUDY, QUESTIONS AND ANSWERS
@app.route('/api_get_csqa', methods=['POST'])
def api_get_csqa():

    input_data = request.get_json()

    api_key = input_data["api_key"]
    main_topic = input_data["main_topic"]
    sub_topic = input_data["sub_topic"]

    # CHECK IF SUB_TOPIC IS IN THE LIST OF SUB_TOPICS
    sub_topics = ["Automation", "Software Design", "Version Control", "Software Lifecycle", "Agile Methodologies", "Software Security"]
    if sub_topic not in sub_topics:
        # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
        mongo_retrieve_endpoint = get_csqa_endpoint + "manual/" + main_topic + "/" + sub_topic
    else:
        # SET UP MONGO RETRIEVAL FROM MONGO MICROSERVICE
        mongo_retrieve_endpoint = get_csqa_endpoint + "automatic/" + main_topic + "/" + sub_topic
    
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
    
    modified_qn_arr = []
    modified_ans_arr = []
    scoring_array = []

    for i in range(len(questions_formatted_arr)):
        question = questions_formatted_arr[i][3:]
        modified_qn_arr.append(question)
        answer = answers_formatted_arr[i][3:]
        modified_ans_arr.append(answer)
        response = openai.ChatCompletion.create(
            engine="gpt35",
            messages = [
                {"role":"system","content":"You are an AI assistant that helps university students learn agile software development and DevSecOps concepts."},
                {"role":"user","content":"Given this question \"What exactly does continuous integration do?\". Please provide a score between 0 and 4 for the answer given by a student \"Conduct integration testing continuously\"."},
                {"role":"assistant","content":"1.5"},
                {"role":"user","content":"Given this question \"What is one advantage of canary deployment?\". Please provide a score between 0 and 4 for the answer given by a student \"Can minimize the impact of errors to a subset of users\"."},
                {"role":"assistant","content":"4"},
                {"role":"user","content":"Given this question \"What does it mean by A/B testing?\". Please provide a score between 0 and 4 for the answer given by a student \"Test to see which are the better features\"."},
                {"role":"assistant","content":"2.5"},
                {"role":"user","content":"Given this question \"How do we carry out rolling update in production?\". Please provide a score between 0 and 4 for the answer given by a student \"Test to see which are the better features\"."},
                {"role":"assistant","content":"0.5"},
                {"role":"user","content":"Given this question \"How do we carry out rolling update in production?\". Please provide a score between 0 and 4 for the answer given by a student \"update one server at a time while the others continue to handle requests\"."},
                {"role":"assistant","content":"3.5"},
                {"role":"user", "content": f"Given this question \"{question}\". Please provide a score between 0 and 4 for the answer given by a student \"{answer}\"."},
                ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        
        scoring_array.append(response.choices[0].message.content)

    # GET CASE STUDY
    generated_case_study = content.split("Answers:")[0].split("Questions:")[0].split("Case Study:")[1]

    # SET UP MONGO UPLOAD CS TO MONGO MICROSERVICE
    mongo_upload_cs_endpoint = upload_cs_endpoint
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
    mongo_upload_qa_endpoint = upload_qa_for_cs_endpoint
    new_qa_data = {
        "main_topic" : main_topic,
        "sub_topic" : sub_topic,
        "mode": "api_call",
        "content": generated_case_study,
        "questions": modified_qn_arr,
        "answers": modified_ans_arr,
        "scores" : scoring_array
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
            "scoring" : scoring_array,
            "message" : f"Case study, questions and answers generated for {main_topic} focusing on {sub_topic}. Uploaded all to the database.",
        }
    )


# SCORING FOR QUESTIONS AND ANSWERS
@app.route('/scoring_qa', methods=['POST'])
def scoring_qa():
    request_data = request.get_json()

    # GET DATA FROM REQUEST
    questions = request_data['questions']
    answers = request_data['answers']

    scoring_array = []

    for i in range(len(questions)):
        response = openai.ChatCompletion.create(
            engine="gpt35",
            messages = [
                {"role":"system","content":"You are an AI assistant that helps university students learn agile software development and DevSecOps concepts."},
                {"role":"user","content":"Given this question \"What exactly does continuous integration do?\". Please provide a score between 0 and 4 for the answer given by a student \"Conduct integration testing continuously\"."},
                {"role":"assistant","content":"1.5"},
                {"role":"user","content":"Given this question \"What is one advantage of canary deployment?\". Please provide a score between 0 and 4 for the answer given by a student \"Can minimize the impact of errors to a subset of users\"."},
                {"role":"assistant","content":"4"},
                {"role":"user","content":"Given this question \"What does it mean by A/B testing?\". Please provide a score between 0 and 4 for the answer given by a student \"Test to see which are the better features\"."},
                {"role":"assistant","content":"2.5"},
                {"role":"user","content":"Given this question \"How do we carry out rolling update in production?\". Please provide a score between 0 and 4 for the answer given by a student \"Test to see which are the better features\"."},
                {"role":"assistant","content":"0.5"},
                {"role":"user","content":"Given this question \"How do we carry out rolling update in production?\". Please provide a score between 0 and 4 for the answer given by a student \"update one server at a time while the others continue to handle requests\"."},
                {"role":"assistant","content":"3.5"},
                {"role":"user", "content": f"Given this question \"{questions[i]}\". Please provide a score between 0 and 4 for the answer given by a student \"{answers[i]}\"."},
                ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None)
        
        scoring_array.append(response.choices[0].message.content)
        print(scoring_array)

    return scoring_array


# FLASK APP ROUTE
if __name__ == '__main__':
    app.run(port=5002, debug=True)