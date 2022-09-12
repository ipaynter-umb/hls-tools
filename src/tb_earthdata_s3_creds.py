import argparse
import base64
import boto3
import json
import requests
from os import environ
from dotenv import load_dotenv
from pathlib import Path

# Load environmental variables from .env file
load_dotenv()


def assemble_event():

    event = {'s3_endpoint': 'https://data.lpdaac.earthdatacloud.nasa.gov/s3credentials',
             'edl_username': environ['ed_username'],
             'edl_password': environ['ed_password']}

    return event


def retrieve_credentials(event):
    """Makes the Oauth calls to authenticate with EDS and return a set of s3
    same-region, read-only credentials.
    """
    login_resp = requests.get(
        event['s3_endpoint'], allow_redirects=False
    )

    login_resp.raise_for_status()

    auth = f"{event['edl_username']}:{event['edl_password']}"
    encoded_auth = base64.b64encode(auth.encode('ascii'))

    auth_redirect = requests.post(
        login_resp.headers['location'],
        data={"credentials": encoded_auth},
        headers={"Origin": event['s3_endpoint']},
        allow_redirects=False
    )
    auth_redirect.raise_for_status()

    final = requests.get(auth_redirect.headers['location'], allow_redirects=False)

    results = requests.get(event['s3_endpoint'], cookies={'accessToken': final.cookies['accessToken']})
    results.raise_for_status()

    return json.loads(results.content)


def lambda_handler(event, context):

    creds = retrieve_credentials(event)
    bucket = event['bucket_name']

    # create client with temporary credentials
    client = boto3.client(
        's3',
        aws_access_key_id=creds["accessKeyId"],
        aws_secret_access_key=creds["secretAccessKey"],
        aws_session_token=creds["sessionToken"]
    )
    # use the client for readonly access.
    response = client.list_objects_v2(Bucket=bucket, Prefix="")

    return {
        'statusCode': 200,
        'body': json.dumps([r["Key"] for r in response['Contents']])
    }


def main():

    download_path = Path('F:/UMB/s3_dl_test.tif')
    file_key = 'HLSS30.020/HLS.S30.T14TPL.2015334T173002.v2.0/HLS.S30.T14TPL.2015334T173002.v2.0.Fmask.tif'
    bucket = 'lp-prod-protected'

    creds = retrieve_credentials(assemble_event())

    client = boto3.client(
        's3',
        aws_access_key_id=creds['accessKeyId'],
        aws_secret_access_key=creds['secretAccessKey'],
        aws_session_token=creds['sessionToken']
    )

    #print(client.get_bucket_policy(Bucket=bucket))

    #obj_list = client.list_objects_v2(Bucket=bucket,
    #                                  Delimiter=',',
    #                                  EncodingType='url',
    #                                  MaxKeys=1,
    #                                  Prefix='HLSS30.020/HLS.S30.T14TPL.2015334T173002.v2.0/')

    #print(obj_list)

    client.download_file(Bucket='lp-prod-protected',
                         Key=file_key,
                         Filename=str(download_path))

    #print(object)

    #object.download_file(download_path)


if __name__ == '__main__':

    main()
