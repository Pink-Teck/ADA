import requests
import re
from dotenv import load_dotenv
import os

load_dotenv()
server_url = os.getenv('SERVER_URL')
admin_token = os.getenv('ADMIN_TOKEN')
if server_url is None:
    raise Exception("server url is None.")
if admin_token is None:
    raise Exception("admin token is None.")

#Generate Token to access API
def generate_token():
    #Make HTML request
    print("game-api: querying server...")

    try:
        response = requests.post(
            server_url,
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "function": "RunCommand",
                "data": {"Command": "server.GenerateAPIToken"}
            },
            verify=False,
            timeout=5,
        )
    except requests.RequestException as exc:
        return False, f"No response: {exc}"

    response_code = response.status_code

    #Report result
    if response_code == 200:
        print("game-api/generate_token: response code 200 - Success")
    else:
        return False, f"generate token failed: {response_code}"

    #Grab string + extract token
    try:
        token_string = response.json()["data"]["commandResult"]
    except (ValueError, KeyError) as exc:
        return False, f"failure to look up keys: {exc}"
    
    token = re.search(
        pattern=r"New Server API Authentication Token:\s*(.*)",
        string=token_string
    )

    #Check token, return if valid
    if token:
        print(f"game-api/generate_token: token found")
        return True, token.group(1)
    else:
        return False, f"invalid token: None"

def get_players(token):
    #Query the server state
    print("game-api/get_players: retrieving player count...")

    try:
        response = requests.post(
            server_url,
            headers={
                "Authorization": f"Bearer {token}"
            },
            json={
                "function": "QueryServerState",
                "data": {}
            },
            verify=False,
            timeout=5,
        )
    except requests.RequestException as exc:
        return False, f"No response: {exc}"

    #Check result
    response_code = response.status_code

    #Check and report result
    if response_code == 200:
        print("game-api/get_players: response code: 200 - Success")
    else:
        print(f"game-api/get_players: unsuccessful response code: {response_code}")
        return False, f"QueryServerState was unsuccessful. Response code: {response_code}"

    #Return player count
    if response:
        try:
            player_count = response.json()["data"]["serverGameState"]["numConnectedPlayers"]
        except (ValueError, KeyError) as exc:
            return False, f"Failed to lookup keys: {exc}"
        
        print(f"game-api/get_players: player count: {player_count}")
        return True, player_count
    
    else:
        return False, f"QueryServerState response was None"


#Health check
def test_connection():

    try:
        response = requests.post(
            server_url,
            json={
                "function": "HealthCheck",
                "data": ""
            },
            verify=False,
            timeout=5,
        )

    except requests.RequestException as exc:
        return False, f"health check failed: {exc}"

    response_code = response.status_code
    if response_code == 200:
        return True, f"success"
    else:
        return False, f"unsuccessful response code: {response_code}"


def main():
    success, token = generate_token()
    if not success:
        print(f"game-api/main: {token}")
        return False, token
    return get_players(token)

if __name__ == "__main__":
    main()