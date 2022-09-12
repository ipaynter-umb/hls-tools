import json
from pathlib import Path
from os import walk, environ
from os.path import exists
from dotenv import load_dotenv
import t_lookups

# Load environmental variables
load_dotenv()


class MGRS:

    def __init__(self):

        self.major_cells = []
        self.by_row = {}
        self.by_col = {}
        self.by_col_row = {}

        # Get the input dictionary from a support file
        input_dict = get_mgrs_support_file()
        # Ingest the input dictionary
        self.ingest_support_dict(input_dict)

    def ingest_support_dict(self, input_dict):
        # For each major cell in the support file
        for major_cell_name in input_dict.keys():
            # Create a major cell object
            major_cell = MGRSMajorCell(major_cell_name)
            # Add the major cell
            self.add_major_cell(major_cell)
            # For each minor cell in the support file
            for minor_cell_name in input_dict[major_cell_name]:
                # Create a minor cell object
                minor_cell = MGRSMinorCell(major_cell, minor_cell_name)
                # Add minor cell to major cell
                major_cell.add_minor_cell(minor_cell)

    def add_major_cell(self, major_cell):
        # Append to list
        self.major_cells.append(major_cell)
        # Split out the major row and column
        major_row = major_cell.name[2]
        major_col = major_cell.name[0:2]
        # If the row is not in the dictionary
        if major_row not in self.by_row.keys():
            # Create a MGRSRow object
            self.by_row[major_row] = MGRSRowOfMajorCells(major_row)
        # Add the major cell to the row
        self.by_row[major_row].major_cells.append(major_cell)
        # Reference the row in the major cell
        major_cell.row = self.by_row[major_row]
        # If the col is not in the dictionary
        if major_col not in self.by_col.keys():
            # Create a MGRSCol object
            self.by_col[major_col] = MGRSColOfMajorCells(major_col)
        # Add the major cell to the col
        self.by_col[major_col].major_cells.append(major_cell)
        # Reference the col in the major cell
        major_cell.col = self.by_col[major_col]
        # If the col is not in the col_row dictionary
        if major_cell.col.name not in self.by_col_row.keys():
            # Add subdict
            self.by_col_row[major_cell.col.name] = {}
        # Add the reference
        self.by_col_row[major_cell.col.name][major_cell.row.name] = major_cell

    def find_all_minor_cell_nbhs(self):
        # For each major cell
        for major_cell in self.major_cells:
            # For each minor cell
            for minor_cell in major_cell.minor_cells:
                # Get its neighbors
                minor_cell.find_minor_cell_nbhs(minor_cell)


                # If the cell is known to be at the westward limit of its row
                if minor_cell.row.west_cell == minor_cell:
                    # Get the neighbor from the next major cell


                    # Get the row equivalent from the next major cell.
                    minor_cell.get_nbh_from_westward_major()

                    # Get the eastmost cell of the relevant row.
                    pass
                # Otherwise (not the westmost cell in its row)
                else:
                    # Get the westward column name
                    westward_column = minor_cell.get_westward_col()
                    # For each minor cell in that cell's row
                    for row_cell in minor_cell.row.minor_cells:
                        # If the column is a match
                        if row_cell.col.name == westward_column:
                            # Set the neighbor
                            minor_cell.westward_nbh = row_cell
                            # Break the loop
                            break
                # If the cell is known to be at the eastward limit of its row
                if minor_cell.row.east_cell == minor_cell:
                    # Get the next major cell.
                    # Get the westmost cell of the relevant row.
                    pass
                # Otherwise (not the eastmost cell in its row)
                else:
                    # Get the eastward column name
                    eastward_column = minor_cell.get_eastward_col()
                    # For each minor cell in that cell's row
                    for row_cell in minor_cell.row.minor_cells:
                        # If the column is a match
                        if row_cell.col.name == eastward_column:
                            # Set the neighbor
                            minor_cell.eastward_nbh = row_cell
                            # Break the loop
                            break
                # If the cell is known to be at the northward limit of its col
                if minor_cell.col.north_cell == minor_cell:
                    # Get the next major cell.
                    # Get the southmost cell of the relevant col.
                    pass
                # Otherwise (not the northmost cell in its col)
                else:
                    # Get the northward row name
                    northward_row = minor_cell.get_northward_row()
                    # For each minor cell in that cell's col
                    for col_cell in minor_cell.col.minor_cells:
                        # If the row is a match
                        if col_cell.row.name == northward_row:
                            # Set the neighbor
                            minor_cell.northward_nbh = col_cell
                            # Break the loop
                            break
                # If the cell is known to be at the southward limit of its col
                if minor_cell.col.south_cell == minor_cell:
                    # Get the next major cell.
                    # Get the northmost cell of the relevant col.
                    pass
                # Otherwise (not the northmost cell in its col)
                else:
                    # Get the southward row name
                    southward_row = minor_cell.get_southward_row()
                    # For each minor cell in that cell's col
                    for col_cell in minor_cell.col.minor_cells:
                        # If the row is a match
                        if col_cell.row.name == southward_row:
                            # Set the neighbor
                            minor_cell.southward_nbh = col_cell
                            # Break the loop
                            break

    #
    def find_minor_cell_nbhs(self, minor_cell):
        # Find each of the cardinal neighbors
        self.find_minor_cell_north_nbh(minor_cell)

    def find_minor_cell_north_nbh(self, minor_cell):
        # Get the North neighbor 1) Exception 2) Intra Major 3) Inter Major Sliver 4) Inter Major
        while True:

            # <> 1) Look for exceptions

            # 2) Try for a minor cell neighbor in the current major cell
            # Get the northward row name
            target_row = minor_cell.get_northward_row()
            # Reference the major cell
            major_cell = minor_cell.major_cell
            # If there is a cell in col/row dict
            if minor_cell.col in major_cell.by_col_row.keys():
                if target_row in major_cell.by_col_row[minor_cell.col].keys():
                    # Reference the northward cell
                    minor_cell.northward_nbh = major_cell.by_col_row[minor_cell.col][target_row]
                    # Break the while
                    break
            # 3) Try for a "sliver" of the same minor cell in the next major cell
            # Get the next major row and col
            next_major_row = major_cell.get_northward_row()
            next_major_col = major_cell.col.name
            # If there is a major cell in the col/row dict
            if next_major_col in self.by_col_row.keys():
                if next_major_row in self.by_col_row[next_major_col].keys():
                    # Reference the next major cell
                    next_major_cell = self.by_col_row[next_major_col][next_major_row]
                    # If there is a cell in col/row dict
                    if minor_cell.col in next_major_cell.by_col_row.keys():
                        if minor_cell.row in next_major_cell.by_col_row[minor_cell.col].keys():
                            # Reference the northward cell
                            minor_cell.northward_nbh = next_major_cell.by_col_row[minor_cell.col][minor_cell.row]
                            # Break the while
                            break
            # 4) Try for a neighbor minor cell in the next major cell
                    if minor_cell.col in next_major_cell.by_col_row.keys():
                        if target_row in next_major_cell.by_col_row[minor_cell.col].keys():
                            # Reference the northward cell
                            minor_cell.northward_nbh = next_major_cell.by_col_row[minor_cell.col][target_row]
            # Break the loop
            break


class MGRSRowOfMajorCells:

    def __init__(self, row_name):

        self.name = row_name
        self.major_cells = []


class MGRSColOfMajorCells:

    def __init__(self, col_name):

        self.name = col_name
        self.major_cells = []


class MGRSMajorCell:

    def __init__(self, major_cell):

        self.name = major_cell
        self.row = None
        self.col = None
        self.minor_cells = []
        self.by_row = {}
        self.by_col = {}
        self.by_col_row = {}

    def add_minor_cell(self, minor_cell):
        # Add minor cell to list
        self.minor_cells.append(minor_cell)
        # Split out the minor row and column
        minor_row = minor_cell.name[1]
        minor_col = minor_cell.name[0]
        # If the row is not in the dictionary
        if minor_row not in self.by_row.keys():
            # Create a MGRSRow object
            self.by_row[minor_row] = MGRSRowOfMinorCells(minor_row)
        # Add the minor cell to the row
        self.by_row[minor_row].add_minor_cell(minor_cell)
        # Reference the row in the minor cell
        minor_cell.row = self.by_row[minor_row]
        # If the col is not in the dictionary
        if minor_col not in self.by_col.keys():
            # Create an object
            self.by_col[minor_col] = MGRSColOfMinorCells(minor_col)
        # Add the minor cell to the col
        self.by_col[minor_col].add_minor_cell(minor_cell)
        # Reference the col in the minor cell
        minor_cell.col = self.by_col[minor_col]
        # If the col is not in the col_row dictionary
        if minor_cell.col.name not in self.by_col_row.keys():
            # Add subdict
            self.by_col_row[minor_cell.col.name] = {}
        # Add the reference
        self.by_col_row[minor_cell.col.name][minor_cell.row.name] = minor_cell

    def get_northward_row(self):
        # Increment the row
        new_row = increment_letter_row_or_col(self.row.name)
        # If this resulted in an I or O (unused letters)
        if new_row == 'I' or new_row == 'O':
            # Increment it again
            new_row = increment_letter_row_or_col(new_row)
        # Return the row
        return new_row

    def get_southward_row(self):
        # Decrement the row
        new_row = decrement_letter_row_or_col(self.row.name)
        # If this resulted in an I or O (unused letters)
        if new_row == 'I' or new_row == 'O':
            # Decrement it again
            new_row = decrement_letter_row_or_col(new_row)
        # Return the row
        return new_row

    def get_eastward_col(self):
        # Increment the col
        new_col = increment_number_row_or_col(self.col.name)
        # If the new col will be '61' (leaving the east edge of the grid)
        if new_col == '61':
            # Change it to the west-most col ('01')
            new_col = '01'
        # Return the col
        return new_col

    def get_westward_col(self):
        # Decrement the col
        new_col = decrement_number_row_or_col(self.col.name)
        # If the new col will be '00' (leaving the west edge of the grid)
        if new_col == '00':
            # Change it to the east-most col ('60')
            new_col = '60'
        # Return the col
        return new_col


class MGRSMinorCell:

    def __init__(self, major_cell, minor_cell):

        self.major_cell = major_cell
        self.name = minor_cell
        self.row = None
        self.col = None
        self.northward_nbh = None
        self.southward_nbh = None
        self.westward_nbh = None
        self.eastward_nbh = None

    def get_northward_row(self):
        # Increment the row
        new_row = increment_letter_row_or_col(self.row.name)
        # If this resulted in an I or O (unused letters)
        if new_row == 'I' or new_row == 'O':
            # Increment it again
            new_row = increment_letter_row_or_col(new_row)
        # Return the row
        return new_row

    def get_southward_row(self):
        # Decrement the row
        new_row = decrement_letter_row_or_col(self.row.name)
        # If this resulted in an I or O (unused letters)
        if new_row == 'I' or new_row == 'O':
            # Decrement it again
            new_row = decrement_letter_row_or_col(new_row)
        # Return the row
        return new_row

    def get_eastward_col(self):
        # Increment the col
        new_col = increment_letter_row_or_col(self.col.name)
        # If this resulted in an I or O (unused letters)
        if new_col == 'I' or new_col == 'O':
            # Increment it again
            new_col = increment_letter_row_or_col(new_col)
        # Return the col
        return new_col

    def get_westward_col(self):
        # Decrement the col
        new_col = decrement_letter_row_or_col(self.col.name)
        # If this resulted in an I or O (unused letters)
        if new_col == 'I' or new_col == 'O':
            # Decrement it again
            new_col = decrement_letter_row_or_col(new_col)
        # Return the col
        return new_col


class MGRSRowOfMinorCells:

    def __init__(self, row_name):

        self.name = row_name
        self.minor_cells = []
        self.west_cell = None
        self.east_cell = None

    def add_minor_cell(self, minor_cell):
        # Add minor cell to list
        self.minor_cells.append(minor_cell)
        # If there is no westmost cell
        if not self.west_cell:
            # Reference the minor cell
            self.west_cell = minor_cell
        # Otherwise (existing westmost cell)
        else:
            # If the minor cell is more westerly
            if ord(minor_cell.col.name) < ord(self.west_cell.col.name):
                # Replace the reference
                self.west_cell = minor_cell
        # If there is no eastmost cell
        if not self.east_cell:
            # Reference the minor cell
            self.east_cell = minor_cell
        # Otherwise (existing eastmost cell)
        else:
            # If the minor cell is more easterly
            if ord(minor_cell.col.name) > ord(self.east_cell.col.name):
                # Replace the reference
                self.east_cell = minor_cell


class MGRSColOfMinorCells:

    def __init__(self, col_name):

        self.name = col_name
        self.minor_cells = []
        self.north_cell = None
        self.south_cell = None

    def add_minor_cell(self, minor_cell):
        # Add minor cell to list
        self.minor_cells.append(minor_cell)
        # If there is no northmost cell
        if not self.north_cell:
            # Reference the minor cell
            self.north_cell = minor_cell
        # Otherwise (existing northmost cell)
        else:
            # If the minor cell is more northerly
            if ord(minor_cell.row.name) > ord(self.north_cell.row.name):
                # Replace the reference
                self.north_cell = minor_cell
        # If there is no southmost cell
        if not self.south_cell:
            # Reference the minor cell
            self.south_cell = minor_cell
        # Otherwise (existing southmost cell)
        else:
            # If the minor cell is more easterly
            if ord(minor_cell.row.name) < ord(self.south_cell.row.name):
                # Replace the reference
                self.south_cell = minor_cell


def get_mgrs_support_file():
    # Support file path
    support_path = Path(environ['support_files_path'], 'MGRS_cells.json')
    # If there is not an MGRS support file
    if not exists(support_path):
        # Generate a support file
        generate_mgrs_support_file()
    # Open the support file
    with open(support_path, 'r') as f:
        input_dict = json.load(f)
    # Return the input dictionary
    return input_dict


def check_for_monsters(target_dict, keys):
    # Current target
    curr_target = target_dict
    # For each key
    for key in keys:
        curr_target = curr_target.get(key)
        # If None (no entry for the key)
        if not curr_target:
            # Return None
            return curr_target
    # Return the target
    return curr_target


def increment_letter_row_or_col(row_or_col):
    # Get ordinal of the new letter
    new_letter = ord(row_or_col) + 1
    # If the ordinal is 91 (after 'Z')
    if new_letter == 91:
        # Wrap it round to Z
        new_letter = 65
    # Return the decremented character
    return chr(new_letter)


def decrement_letter_row_or_col(row_or_col):
    # Get ordinal of the new letter
    new_letter = ord(row_or_col) - 1
    # If the ordinal is 64 (before 'A')
    if new_letter == 64:
        # Wrap it round to Z
        new_letter = 90
    # Return the decremented character
    return chr(new_letter)


def increment_number_row_or_col(row_or_col):
    # Return the incremented string
    return zero_pad_number(int(row_or_col) + 1, digits=2)


def decrement_number_row_or_col(row_or_col):
    # Return the decremented string
    return zero_pad_number(int(row_or_col) - 1, digits=2)


def zero_pad_number(input_number, digits=3):
    # Make sure the number has been converted to a string
    input_number = str(input_number)
    # While the length of the string is less than the required digits
    while len(input_number) < digits:
        # Prepend a 0 to the string
        input_number = '0' + input_number
    # Return the string
    return input_number


def generate_mgrs_support_file():

    # Dictionary for results
    results_dict = {}

    for root, dirs, files in walk(Path(environ['input_files_path'], 'MGRS')):
        for file in files:
            if '.dbf' in file:
                # Split out major cell name
                major_name = file.split('_')[-1].split('.')[0]
                # Add list to hold minor cells for the major cell
                results_dict[major_name] = []
                # Open the file
                with open(Path(root, file), 'r') as f:
                    # For each line (starting from fourth line)
                    for line in f.readlines()[3:]:
                        # Split the line on spaces
                        for component in line.split(' '):
                            # If the component is a minor cell designator
                            if len(component) == 2:
                                # File is under the major cell
                                results_dict[major_name].append(component)

    # Write the dict to a support file
    with open(Path(environ['support_files_path'], 'MGRS_cells.json'), 'w') as of:
        json.dump(results_dict, of, indent=4)


def main():

    # MGRS object
    mgrs = MGRS()

    for root, dirs, files in walk(Path(environ['input_files_path'], 'MGRS')):
        for file in files:
            if '.dbf' in file:
                # Split out major cell name
                major_name = file.split('_')[-1].split('.')[0]
                # Make a new Major Cell object
                major_cell = MGRSMajorCell(major_name)
                # Add to the MGRS object
                mgrs.add_major_cell(major_cell)
                # Open the file
                with open(Path(root, file), 'r') as f:
                    # For each line (starting from fourth line)
                    for line in f.readlines()[3:]:
                        # Component count
                        component_count = 0
                        # Split the line on spaces
                        for component in line.split(' '):
                            # If the component is a minor cell designator
                            if len(component) == 2:
                                # Add to component count
                                component_count += 1
                                # Add minor cell object to major cell
                                major_cell.minor_cells.append(MGRSMinorCell(major_cell, component))
                # Organize the major cell (now we have all the minor cells)
                major_cell.organize_grid()
                print(f"{component_count} minor cells found in {major_name}.")
                print(f"{major_name} has {len(major_cell.by_rows.keys())} rows")
                print(f"{major_name} has {len(major_cell.by_cols.keys())} columns.")

                # Get minor cell neighbors
                mgrs.derive_minor_cell_nbhs()
                # Print one
                print(major_cell.by_cols['D'].minor_cells[2].__dict__)
                input()


if __name__ == '__main__':

    main()