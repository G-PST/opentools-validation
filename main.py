""" Entry python module for github action. """

# standard imports
import os
import http
import re
import subprocess

# third-party imports
import pytest
import requests


def download_data_file(issue_url: str, access_token: str):
    """Function to download issue file."""
    print("Starting to download the file.")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{issue_url}/comments", headers=headers)

    print(f"Response: {response} {response.status_code} {headers}")
    if response.status_code != http.HTTPStatus.OK:
        return

    comments = response.json()
    print(f"Comments: {comments}")
    if not comments:
        return

    json_files = [
        item
        for item in re.findall(r"(https?://[^\s)]+)", comments[-1]["body"])
        if item.endswith(".json")
    ]

    if not json_files:
        return
    
    print(f"Detected JSON files {json_files}")

    latest_json_file = json_files[-1]
    file_name = latest_json_file.split("/")[-1]
    file_response = requests.get(latest_json_file)

    if file_response.status_code != http.HTTPStatus.OK:
        return False

    with open(file_name, "wb") as f:
        f.write(file_response.content)

    print(f"File {file_name} downloaded successfully.")
    return file_name


def main():
    """Entry function for github action."""
    issue_number = os.environ["INPUT_ISSUE_NUMBER"]
    issue_title = os.environ["INPUT_ISSUE_TITLE"]
    issue_url = os.environ["INPUT_ISSUE_URL"]
    token = os.environ["INPUT_TOKEN"]

    print(issue_number, issue_title, issue_url, token)

    if issue_number or issue_title or issue_url or token:
        if not (issue_number and issue_title and issue_url and token):
            print("::set-output name=exitcode::1")
            return

        os.environ["GITHUB_TOKEN"] = token
        file_name = download_data_file(issue_url, token)
        if not file_name:
            print("::set-output name=exitcode::0")
            return

        branch_name = f"issue_{issue_number}_branch"
        subprocess.run(["git", "checkout", "-b", branch_name], check=True)
        subprocess.run(["git", "add", file_name], check=True)
        commit_message = f"Add issue file: {file_name}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(
            ["git", "push", "--set-upstream", "origin", branch_name], check=True
        )
        print("::set-output name=exitcode::0")
        return

    try:
        data_path = os.environ["INPUT_DATAPATH"]
    except KeyError as _:
        data_path = "data"
        os.environ["INPUT_DATAPATH"] = data_path

    print(f"Data for testing: {data_path}")

    retcode = pytest.main(["-x", "/app"])
    print(f"::set-output name=exitcode::{retcode}")


if __name__ == "__main__":
    main()
