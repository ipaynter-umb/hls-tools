
class MGRSMinorCell:

    def __init__(self):

        # The Major cell to which this minor cell belongs
        self.major_cell = None
        # Other "parts" of this minor cell in other major cells
        self.sliver_buddies = []
        # Minor cells that are directly to the north
        self.northwards = []
        # Minor cells that are directly to the south
        self.southwards = []
        # Minor cells that are directly to the west
        self.westwards = []
        # Minor cells that are directly to the east
        self.eastwards = []


class MGRSMajorCell:

    def __init__(self):

        # Minor cells that belong to this major cell
        self.minor_cells = []
        self.by_minor_row = {}
        self.by_minor_col = {}

# A dictionary of exceptions
exceptions = {}
