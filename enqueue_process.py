#!/home/c3hod/python/process_queue/.queue/bin/python
import requests
import argparse
from dotenv import load_dotenv
import os

def make_request(url, filename):
    url = f"{url}/add_task/"
    data = {"filename": filename}
    response = requests.post(url, json = data)
    print(f'Status Code: {response.status_code}\n Response JSON: {response.json()}')
    
def main():
    parser = argparse.ArgumentParser(description = 'FiFo Task Script')
    parser.add_argument("--filename", type = str, required = True )
    args = parser.parse_args()
    
    load_dotenv()
    URL = os.getenv('URL')
    make_request(URL, args.filename)

if __name__ == "__main__":
    main()