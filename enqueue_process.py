#!/home/c3hod/pyproj/process_queue/.process_queue/bin/python
import requests
import argparse

def make_request(filename):
    url = "http://localhost:8000/add_task/"
    data = {"filename": filename}
    response = requests.post(url, json = data)
    print(f'Status Code: {response.status_code}\n Response JSON: {response.json()}')
    

def main():
    parser = argparse.ArgumentParser(description = 'FiFo Task Script')
    parser.add_argument("--filename", type = str, required = True )
    args = parser.parse_args()

    make_request(args.filename)

if __name__ == "__main__":
    main()