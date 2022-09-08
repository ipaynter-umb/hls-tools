import t_stac_search
import t_lookups
import datetime
import logging
import json
from dotenv import load_dotenv
from os import environ, walk
from pathlib import Path


# Load environmental variables
load_dotenv()


# Class for HLS (v2.0) data
class HLSDataCatalog:

    def __init__(self):

        self.l30 = HLSDataset('L30')
        self.s30 = HLSDataset('S30')


# Class for HLS (v2.0) data. Either Sentinel (S30) or Landsat (L30)
class HLSDataset:

    def __init__(self, dataset):

        self.dataset = f'HLS{dataset}.v2.0'
        self.by_date = {}
        self.by_id = {}
        self.by_tile = {}

        # Get the latest date of a file for the dataset (if any)
        latest_date = self.get_latest_dataset_file()
        # If there is no file (indicated by the None response from the latest date)
        if latest_date is None:
            # Make a dataset file
            self.make_new_dataset_file()
            # Try again for the latest date
            latest_date = self.get_latest_dataset_file()
        # Ingest the support file
        self.ingest_support_file(latest_date)

    # Ingest a support file for this dataset
    def ingest_support_file(self, latest_date):
        # Assemble the path to the file
        latest_file_path = Path(
            environ["support_files_path"] + f'{self.dataset}_files_' + latest_date.strftime(
                "%m%d%Y") + ".json")
        # Open the file
        with open(latest_file_path, 'r') as f:
            # Load as dictionary and reference
            input_list = json.load(f)
        # For each file in the list
        for file in input_list:
            # Add the file to the various search dictionaries
            self.add_file_by_date(file)
            self.add_file_by_tile(file)

    # Add a file to the "by_date" dictionary
    def add_file_by_date(self, file):
        # Split the name of the file
        split_name = file.split('.')
        # Get the date designators
        year = split_name[3][0:4]
        doy = split_name[3][4:7]
        # Reference the file
        if year not in self.by_date.keys():
            self.by_date[year] = {}
        if doy not in self.by_date[year].keys():
            self.by_date[year][doy] = []
        self.by_date[year][doy].append(file)

    # Add a file to the "by_tile" dictionary
    def add_file_by_tile(self, file):
        # Split the name of the file
        split_name = file.split('.')
        # Get the tile designators
        tile_col_major = split_name[2][1:3]
        tile_row_major = split_name[2][3]
        tile_col_minor = split_name[2][4]
        tile_row_minor = split_name[2][5]
        if tile_row_major not in self.by_tile.keys():
            self.by_tile[tile_row_major] = {}
        if tile_col_major not in self.by_tile[tile_row_major].keys():
            self.by_tile[tile_row_major][tile_col_major] = {}
        if tile_row_minor not in self.by_tile[tile_row_major][tile_col_major].keys():
            self.by_tile[tile_row_major][tile_col_major][tile_row_minor] = {}
        if tile_col_minor not in self.by_tile[tile_row_major][tile_col_major][tile_row_minor].keys():
            self.by_tile[tile_row_major][tile_col_major][tile_row_minor][tile_col_minor] = []
        self.by_tile[tile_row_major][tile_col_major][tile_row_minor][tile_col_minor].append(file)

    # Add a file to the "by_id" dictionary
    def add_file_by_id(self, file):
        # Split the name of the file
        split_name = file.split('.')
        # Assemble the predictable part of the ID (losing acquisition time)
        base_name = split_name[0] + split_name[1] + split_name[2] + split_name[3][0:7]
        # Enter into dictionary
        self.by_id[base_name] = file

    # Make a new file for the dates
    def make_new_dataset_file(self):
        # Get the file details to make a file
        file_list = t_stac_search.get_items_from_STAC(self.dataset)
        # Assemble the path to the file
        output_path = Path(
            environ["support_files_path"] + f'{self.dataset}_files_' + datetime.datetime.now().strftime(
                "%m%d%Y") + ".json")
        # Write the file
        with open(output_path, 'w') as f:
            json.dump(file_list, f)

    # Get the latest date of a support file for the dataset
    def get_latest_dataset_file(self):
        # Latest date variable
        latest_date = None
        # Walk the support file directory
        for root, dirs, files in walk(environ["support_files_path"]):
            # For each file name
            for name in files:
                # If the file is one of the URL files
                if f"{self.dataset}_files_" in name:
                    # Split the name
                    split_name = name.split('_')
                    # Make a datetime date object from the name
                    file_date = datetime.date(year=int(split_name[-1][4:8]),
                                              month=int(split_name[-1][0:2]),
                                              day=int(split_name[-1][2:4]))
                    # If there is no latest date yet
                    if latest_date is None:
                        # Set the file's date
                        latest_date = file_date
                    # Otherwise, if the file's date is later
                    elif file_date > latest_date:
                        # Set the file's date as latest
                        latest_date = file_date
        # Return latest date
        return latest_date

    # Takes a MGSR tile major row and column, and a datetime date object.
    def get_relevant_tiles(self, mgrs_row, mgrs_col, date):
        # Tile files
        tile_files = []
        # Set the current row and column
        curr_row = mgrs_row
        curr_col = mgrs_col
        # Stacks for the ongoing searches
        to_search_northward = [f'{curr_col}{curr_row}']
        to_search_westward = [f'{curr_col}{curr_row}']
        to_search_eastward = [f'{curr_col}{curr_row}']
        to_search_southward = [f'{curr_col}{curr_row}']

        print(to_search_northward,
              to_search_southward,
              to_search_westward,
              to_search_eastward)

        # Check for other tiles in the same major tile as the target
        files_list = self.check_for_files(f'{curr_col}{curr_row}', date)
        # For each file
        for file in files_list:
            # Add to the tile files (note this process will add the original tile file)
            tile_files.append(file)

        # While we are still looking northward
        while len(to_search_northward) > 0:
            # Pop a tile from the northward search stack
            curr_tile = to_search_northward.pop()
            # Update the current search row and col
            curr_row = curr_tile[-1]
            curr_col = curr_tile[0:2]
            # For each northward tile
            for tile in move_northwards(curr_row, curr_col):
                # Get any files
                files_list = self.check_for_files(tile, date)
                # If there was at least one file
                if len(files_list) > 0:
                    # Add the tile to the relevant stacks for further searching
                    if tile not in to_search_northward:
                        to_search_northward.append(tile)
                    if tile not in to_search_westward:
                        to_search_westward.append(tile)
                    if tile not in to_search_eastward:
                        to_search_eastward.append(tile)
                # For each file in the list
                for file in files_list:
                    # If it is not already in the tile files list
                    if file not in tile_files:
                        # Add it
                        tile_files.append(file)

        print(to_search_northward,
              to_search_southward,
              to_search_westward,
              to_search_eastward)
        print(tile_files)

        # While we are still looking southward
        while len(to_search_southward) > 0:
            # Pop a tile from the southward search stack
            curr_tile = to_search_southward.pop()
            # Update the current search row and col
            curr_row = curr_tile[-1]
            curr_col = curr_tile[0:2]
            # For each southward tile
            for tile in move_southwards(curr_row, curr_col):
                # Get any files
                files_list = self.check_for_files(tile, date)
                # If there was at least one file
                if len(files_list) > 0:
                    # Add the tile to the relevant stacks for further searching
                    if tile not in to_search_southward:
                        to_search_southward.append(tile)
                    if tile not in to_search_westward:
                        to_search_westward.append(tile)
                    if tile not in to_search_eastward:
                        to_search_eastward.append(tile)
                # For each file in the list
                for file in files_list:
                    # If it is not already in the tile files list
                    if file not in tile_files:
                        # Add it
                        tile_files.append(file)

        print(to_search_northward,
              to_search_southward,
              to_search_westward,
              to_search_eastward)
        print(tile_files)

        # While we are still looking westward
        while len(to_search_westward) > 0:
            # Pop a tile from the westward search stack
            curr_tile = to_search_westward.pop()
            # Update the current search row and col
            curr_row = curr_tile[-1]
            curr_col = curr_tile[0:2]
            # For each westward tile
            for tile in move_westwards(curr_row, curr_col):
                # Get any files
                files_list = self.check_for_files(tile, date)
                # If there was at least one file
                if len(files_list) > 0:
                    # Add the tile to the relevant stacks for further searching
                    if tile not in to_search_westward:
                        to_search_westward.append(tile)
                # For each file in the list
                for file in files_list:
                    # If it is not already in the tile files list
                    if file not in tile_files:
                        # Add it
                        tile_files.append(file)

        print(to_search_northward,
              to_search_southward,
              to_search_westward,
              to_search_eastward)
        print(tile_files)

        # While we are still looking eastward
        while len(to_search_eastward) > 0:
            # Pop a tile from the eastward search stack
            curr_tile = to_search_eastward.pop()
            # Update the current search row and col
            curr_row = curr_tile[-1]
            curr_col = curr_tile[0:2]
            # For each eastward tile
            for tile in move_eastwards(curr_row, curr_col):
                # Get any files
                files_list = self.check_for_files(tile, date)
                # If there was at least one file
                if len(files_list) > 0:
                    # Add the tile to the relevant stacks for further searching
                    if tile not in to_search_eastward:
                        to_search_eastward.append(tile)
                # For each file in the list
                for file in files_list:
                    # If it is not already in the tile files list
                    if file not in tile_files:
                        # Add it
                        tile_files.append(file)

        print(to_search_northward,
              to_search_southward,
              to_search_westward,
              to_search_eastward)
        print(tile_files)

        return tile_files

    # Check for files for a particular tile
    def check_for_files(self, tile, date):
        # Get the year and DOY to search
        year = str(date.year)
        doy = zero_pad_number((date - datetime.date(year=date.year, month=1, day=1)).days + 1, digits=3)
        # List for files
        files_list = []
        # Search for the year
        if year in self.by_date.keys():
            # Search for the DOY
            if doy in self.by_date[year].keys():
                # For each file
                for file in self.by_date[year][doy]:
                    print(f'Checking {file} against {tile}')
                    # Get the file's tile
                    file_tile = file.split('.')[2][1:4]
                    # If the (major) tile matches
                    if file_tile == tile:
                        # Add the file to the list
                        files_list.append(file)
        # Return the list
        return files_list


# Takes N, S, E, or W as direction
def check_for_dragons(row, col, direction):
    if direction == 'E':
        if f'{col}{row}' in t_lookups.to_check_eastwards.keys():
            return t_lookups.to_check_eastwards.get(f'{col}{row}')
    elif direction == 'W':
        if f'{col}{row}' in t_lookups.to_check_westwards.keys():
            return t_lookups.to_check_westwards.get(f'{col}{row}')
    elif direction == 'S':
        if f'{col}{row}' in t_lookups.to_check_southwards.keys():
            return t_lookups.to_check_southwards.get(f'{col}{row}')
    elif direction == 'N':
        if f'{col}{row}' in t_lookups.to_check_northwards.keys():
            return t_lookups.to_check_northwards.get(f'{col}{row}')
    else:
        logging.error(f'Checking for exceptions only accepts strings N, S, E, or W as direction, not {direction}.')


def move_northwards(row, col):
    # Check for exceptions
    exceptions = check_for_dragons(row, col, 'N')
    # If there were exceptions
    if exceptions:
        # Search for those instead
        return exceptions
    # Otherwise, return the incremented tile col (+1, eastwards)
    return [f'{col}{chr(ord(row) + 1)}']


def move_southwards(row, col):
    # Check for exceptions
    exceptions = check_for_dragons(row, col, 'S')
    # If there were exceptions
    if exceptions:
        # Search for those instead
        return exceptions
    # Otherwise, return the incremented tile col (+1, eastwards)
    return [f'{col}{chr(ord(row) - 1)}']


def move_eastwards(row, col):
    # Check for exceptions
    exceptions = check_for_dragons(row, col, 'E')
    # If there were exceptions
    if exceptions:
        # Search for those instead
        return exceptions
    # Otherwise, return the incremented tile col (+1, eastwards)
    return [f'{zero_pad_number(int(col) + 1, digits=2)}{row}']


def move_westwards(row, col):
    # Check for exceptions
    exceptions = check_for_dragons(row, col, 'W')
    # If there were exceptions
    if exceptions:
        # Search for those instead
        return exceptions
    # Otherwise, return the incremented tile col (+1, eastwards)
    return [f'{zero_pad_number(int(col) - 1, digits=2)}{row}']


def zero_pad_number(input_number, digits=3):
    # Make sure the number has been converted to a string
    input_number = str(input_number)
    # While the length of the string is less than the required digits
    while len(input_number) < digits:
        # Prepend a 0 to the string
        input_number = '0' + input_number
    # Return the string
    return input_number


def main():

    # Set the logging config
    logging.basicConfig(filename=environ['log_files_path'] + f'{datetime.datetime.now():%Y%m%d%H%M%S}.log',
                        filemode='w',
                        format=' %(levelname)s - %(asctime)s - %(message)s',
                        level=logging.INFO)

    #catalog = HLSDataCatalog()
    catalog = HLSDataset('S30')
    print(catalog.by_tile['U']['31']['Q']['D'][0])
    target_file = catalog.by_tile['U']['31']['Q']['D'][0]


    #exit()
    #catalog = HLSDataset('S30')

    #print(catalog.by_tile['U']['31']['Q']['D'][0])
    #target_file = catalog.by_tile['U']['31']['Q']['D'][0]

    #target_file = catalog.by_date['2017']['168'][3]
    #print(target_file)
    target_tile = target_file.split('.')[2][1:4]
    print(target_tile)

    split_date = target_file.split('.')[3]
    target_date = datetime.date(year=int(split_date[0:4]), month=1, day=1) + datetime.timedelta(days=int(split_date[4:7]) - 1)

    for file in catalog.by_date[split_date[0:4]][split_date[4:7]]:
        print(file)

    #print(catalog.get_relevant_tiles(target_tile[-1], target_tile[0:2], target_date))


if __name__ == '__main__':

    main()
