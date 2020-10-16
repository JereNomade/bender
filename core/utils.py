import os
import random
import requests
import simplejson

def message_api(msg):
    api_url = "http://localhost:5000/api/message_bender"
    headers = {'content-type': 'application/json', 'Accept': 'application/json'}
    data = {"msg": msg}
    r = requests.post(api_url, data=simplejson.dumps(data), headers=headers, timeout=5)
    return 

def get_user_agent_list():
    install_folder = os.path.abspath(os.path.split(__file__)[0])
    user_agents_file = os.path.join(install_folder, 'user_agents.txt')
    with open(user_agents_file) as fp:
        user_agents_list = [_.strip() for _ in fp.readlines()]
        return user_agents_list

def get_random_user_agent(user_agents_list):
    return random.choice(user_agents_list)

def get_random_sleep():
    return random.randint(50,100)