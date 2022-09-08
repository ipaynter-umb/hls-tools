import json
import requests
import logging
from time import sleep, time
from dotenv import load_dotenv
from os import environ


# Load environmental variables from .env
load_dotenv()


# Get a list of item titles from a STAC data product
def get_items_from_STAC(data_product):
    # Start time
    stime = time()
    # List to hold the items
    item_list = []
    # Start (unauthenticated) session
    s = requests.session()
    # Data product URL
    data_product_url = environ['stac_root'] + f'LPCLOUD/collections/{data_product}'
    # Logging info
    logging.info(f"Requesting {data_product_url} from STAC.")
    # Request the data product and retrieve the text
    dataset_dict = get_text_from_STAC_request(data_product_url, session=s)
    # If the text was retrieved
    if dataset_dict:
        # Get all the children from the dataset (years)
        dataset_children = filter_STAC_dataset_links(dataset_dict, 'child')
    # Otherwise (no text retrieved)
    else:
        # Log error
        logging.error(f'Text could not be retrieved from {data_product_url}.')
        # Return False
        return False
    # For each of the years
    for year_link in dataset_children:
        # Get the href as the link
        year_link = year_link['href']
        # Request the data from the year links and retrieve the text
        year_dict = get_text_from_STAC_request(year_link, session=s)
        # If the text was retrieved
        if year_dict:
            # Get all the children from the dataset (years)
            year_children = filter_STAC_dataset_links(year_dict, 'child')
        # Otherwise (no text retrieved)
        else:
            # Log warning
            logging.warning(f'No text was retrieved from {year_link}. Skipping.')
            # Skip the year
            continue
        # For each of the months
        for month_link in year_children:
            # Get the href as the link
            month_link = month_link['href']
            # Request the data from the month links and retrieve the text
            month_dict = get_text_from_STAC_request(month_link, session=s)
            # If the text was retrieved
            if month_dict:
                # Get all the children (days)
                month_children = filter_STAC_dataset_links(month_dict, 'child')
            # Otherwise (no text retrieved)
            else:
                # Log warning
                logging.warning(f'No text was retrieved from {month_link}. Skipping.')
                # Skip the month
                continue
            # For each of the days
            for day_link in month_children:
                # Get the href as the link
                day_link = day_link['href']
                # Request the data from the day links and retrieve the text
                day_dict = get_text_from_STAC_request(day_link, session=s)
                # If the text was retrieved
                if day_dict:
                    # Get all the items (scenes/base files)
                    day_items = filter_STAC_dataset_links(day_dict, 'item')
                # Otherwise (no text retrieved)
                else:
                    # Log warning
                    logging.warning(f'No text was retrieved from {day_link}. Skipping.')
                    # Skip the month
                    continue
                # For each item
                for item in day_items:
                    # Add the file name base ('title') to the list
                    item_list.append(item['title'])
    # Log the success
    logging.info(f'All items retrieved for {data_product} in {round(time() - stime)} seconds.')
    # Return the list of item titles
    return item_list


def get_text_from_STAC_request(target_url, session=requests.session(), attempt_limit=3):
    # Logging info
    logging.info(f"Requesting {target_url} from STAC.")
    # Attempt count
    attempt_count = 0
    # While loop to get through the validation steps
    while True:
        # Increment attempt count
        attempt_count += 1
        # If the attempt count exceeds the limit
        if attempt_count > attempt_limit:
            # Log and error
            logging.error(f'All {attempt_limit} attempts to retrieve text from {target_url} failed.')
            # Return False
            return False
        # Log the attempt
        logging.info(f'Attempting to retrieve text from {target_url}. Attempt {attempt_count} of {attempt_limit}.')
        # Make a request for the dataset from STAC
        r = attempt_request(session,
                            target_url)
        # If the request was unsuccessful
        if not r:
            # Log warning
            logging.warning(f'Request for {target_url} was unsuccessful.')
            # Skip the loop
            continue
        # Get the text from the request
        r_text = attempt_request_to_text(r)
        # If the text retrieval was unsuccessful
        if not r_text:
            # Log warning
            logging.warning(f'Text retrieval from request for {target_url} was unsuccessful.')
            # Skip the loop
            continue
        # If we get this far, log the info
        logging.info(f'Retrieval of text from {target_url} successful in {attempt_count} attempts.')
        # Return the text
        return r_text


def attempt_request_to_text(response):
    # Try and retrieve text from a requests response
    try:
        response_text = json.loads(response.text)
        return response_text
    # If it doesn't work
    except:
        # Return False
        return False


def filter_STAC_dataset_links(dataset, filter):
    links_list = []
    # For each link (dictionary in list in links)
    for link in dataset['links']:
        # If the relative field of the entry indicates it's a 'child"
        if link['rel'] == filter:
            # Get the dictionary
            links_list.append(link)
    # Return the list
    return links_list


# Attempt a request until it is successful or hard limit is reached
def attempt_request(session, target_url, attempt_limit=10):
    # Back-off timer
    back_off = 0
    # Attempt count
    attempt_count = 1
    # Log the attempt
    logging.info(f'Making request for {target_url}. Attempt {attempt_count}.')
    # Try the request
    r = session.get(target_url)
    # If we get a non-200 status request
    while r.status_code != 200:
        # Log the attempt
        logging.info(f'{r.status_code} for {target_url}.')
        # Increment attempt count
        attempt_count += 1
        # If we have exceeded the attempt limit
        if attempt_count > attempt_limit:
            # Log an error
            logging.error(f'Request for {target_url} failed after {attempt_count} of {attempt_limit} attempts.')
            # Return False (failed)
            return False
        # Log a warning
        logging.warning(f'Status code of {r.status_code} for {target_url}. Waiting {back_off} seconds.')
        # Wait a hot second_
        sleep(back_off)
        # Log the attempt
        logging.info(f'Making request for {target_url}. Attempt {attempt_count}.')
        # Try again
        r = session.get(target_url)
        # Add to back off timer
        back_off += 1
    # Log the attempt
    logging.info(f'Finished with request for {target_url}. Attempt {attempt_count}.')
    # Return the completed request
    return r


def main():

    get_items_from_STAC('HLSS30.v2.0')
    #get_items_from_STAC('HLSL30.v2.0')


if __name__ == '__main__':

    main()
