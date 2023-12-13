import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import re
from airflow.models import Variable

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def check_for_response(receiver, subject):
    """Display unread thread emails sent by receiver under subject
    Return: True if the email is responded to, False if no response

    Load pre-authorized user credentials from the environment.
    """
    # # Code that generates token.json
    # creds = None
    # # The file token.json stores the user's access and refresh tokens, and is
    # # created automatically when the authorization flow completes for the first
    # # time.
    # if os.path.exists("token.json"):
    #     creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # # If there are no (valid) credentials available, let the user log in.
    # if not creds or not creds.valid:
    #     if creds and creds.expired and creds.refresh_token:
    #         creds.refresh(Request())
    #     else:
    #         flow = InstalledAppFlow.from_client_secrets_file(
    #             "credentials.json", SCOPES
    #         )
    #         creds = flow.run_local_server(port=0)
    #     # Save the credentials for the next run
    #     with open("token.json", "w") as token:
    #         token.write(creds.to_json())

    token = Variable.get("token-json", deserialize_json=True, default_var=None)
    creds = Credentials.from_authorized_user_info(token, SCOPES)

    try:
        # create gmail api client
        service = build("gmail", "v1", credentials=creds)

        # pylint: disable=maybe-no-member
        # pylint: disable:R1710
        threads = (
            service.users().threads().list(userId="me", q=f"from:{receiver} subject:{subject} is:unread").execute().get("threads", [])
        )
        for thread in threads:
            tdata = (
                service.users().threads().get(userId="me", id=thread["id"]).execute()
            )
            nmsgs = len(tdata["messages"])

            if nmsgs > 1:
                sent_msg = tdata["messages"][0]["payload"]
                rcvd_msg = tdata["messages"][-1]["payload"]
                subject = ""
                receiver = ""
                for header in sent_msg["headers"]:
                    if header["name"] == "Subject":
                        subject = header["value"]
                    if header["name"] == "To":
                        receiver = header["value"]
                        break
                body = base64.b64decode(rcvd_msg["parts"][0]["body"]["data"], '-_').decode()
                pattern = r"^[a-z].*(?:\r?\n(?!\r?\n).*)*"
                body = re.match(pattern, f'{body}').group(0)
                if subject:  # skip if no Subject line
                    print(f"- {nmsgs} unread messages, subject: {subject}, to: {receiver}, body: {body}")
                    return body
            return False

    except HttpError as error:
        print(f"An error occurred: {error}")


# if __name__ == "__main__":
#   check_for_response("seohyunlim98@gmail.com", "Test Mail")