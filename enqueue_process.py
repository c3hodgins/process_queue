#!/home/c3hod/python/process_queue/.queue/bin/python
# example file for making requests to the backend
import requests
import argparse
from dotenv import load_dotenv
import os

def make_request(url, filename):
    url = f"{url}/add_task/"
    if not os.path.exists(filename):
        print(f'File Does Not Exist')
        return
    try: 
        print(f'Attempting file transfer {filename} to {url}')
        with open(filename, 'rb') as f:
            response = requests.post(url, files={"file":f})
        print(f'Status Code: {response.status_code}\n Response JSON: {response.json()}')
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

    
def main():
    parser = argparse.ArgumentParser(description = 'FiFo Task Script')
    parser.add_argument("--filename", type = str, required = True )
    args = parser.parse_args()
    
    load_dotenv()
    URL = os.getenv('URL')
    make_request(URL, args.filename)

if __name__ == "__main__":
    main()