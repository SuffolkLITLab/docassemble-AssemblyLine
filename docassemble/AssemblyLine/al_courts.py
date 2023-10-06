"""
Package for a very simple / MVP list of courts that is mostly signature compatible w/ MACourts for now
"""
import os
from typing import Any, Dict, List, Optional, Union, Set
import pandas as pd
import docassemble.base.functions
from docassemble.base.util import (
    path_and_mimetype,
    Address,
    LatitudeLongitude,
    DAObject,
    log,
    space_to_underscore,
)
from docassemble.base.legal import Court
from .al_general import ALAddress

__all__ = [
    "ALCourt",
    "ALCourtLoader",
]


class ALCourt(Court):
    """Object representing a court in Massachusetts.
    TODO: it could be interesting to store a jurisdiction on a court. But this is non-trivial. Should it be geo boundaries?
    A list of cities? A list of counties? Instead, we use a function on the CourtList object that filters courts by
    address and can use any of those three features of the court to do the filtering."""

    def init(self, *pargs, **kwargs):
        super().init(*pargs, **kwargs)
        if "address" not in kwargs:
            self.initializeAttribute("address", ALAddress)
        if (
            "jurisdiction" not in kwargs
        ):  # This attribute isn't used. Could be a better way to handle court locating
            self.jurisdiction = []
        if "location" not in kwargs:
            self.initializeAttribute("location", LatitudeLongitude)

    def __str__(self) -> str:
        return str(self.name)

    def _map_info(self) -> List[Dict[str, Any]]:
        """
        Create information that can be used to display court locations on a Docassemble map.

        See: https://docassemble.org/docs/functions.html#map_of

        Returns:
            List[Dict[str, Any]] - a list of dictionaries, each of which contains
                the following keys:
                    - latitude: float
                    - longitude: float
                    - info: str
                    - icon: str (optional)
        """
        the_info = str(self.name)
        the_info += "  [NEWLINE]  " + self.address.block()
        result = {
            "latitude": self.location.latitude,
            "longitude": self.location.longitude,
            "info": the_info,
        }
        if hasattr(self, "icon"):
            result["icon"] = self.icon
        return [result]

    def short_label(self) -> str:
        """
        Returns a string that represents a nice, disambiguated label for the court.
        This may not match the court's name. If the name omits city, we
        append city name to the court name. This is good for a drop-down selection
        list.

        Returns:
            str: string representing the court's name, with city if needed to disambiguate
        """
        # Avoid forcing the interview to define the court's address
        if hasattr(self, "address") and hasattr(self.address, "city"):
            if self.address.city in str(self.name):
                return str(self.name)
            else:
                return str(self.name) + " (" + self.address.city + ")"
        return str(self.name)

    def short_label_and_address(self) -> str:
        """
        Returns a markdown formatted string with the name and address of the court.
        More concise version without description; suitable for a responsive case.

        Returns:
            str: string representing the court's name and address
        """
        return f"**{ self.short_label() }**[BR]{ self.address.on_one_line() }"

    def short_description(self) -> str:
        """
        Returns a Markdown formatted string that includes the disambiguated name and
        the description of the court, for inclusion in the results page with radio
        buttons.

        Returns:
            str: string representing the court's name and description
        """
        all_info = f"**{ self.short_label() }**"
        if hasattr(self, "address"):
            all_info = f"{ all_info }[BR]{ self.address.on_one_line() }"
        return f"{ all_info }[BR]{ self.description }"

    def from_row(self, df_row: pd.Series, ensure_lat_long: bool = True) -> None:
        """
        Loads data from a single Pandas Dataframe into the current court object.
        Note: It will try to convert column names that don't make valid
        attributes. Best practice is to use good attribute names (no spaces) that don't interfere
        with existing attributes or methods of DAObject

        Args:
            df_row: Pandas Series object
            ensure_lat_long: bool, whether to use Google Maps to geocode the address if we don't have coordinates
        """
        # A few columns we expect to see:
        # name
        # address_address
        # address_city. Optionally: address_unit, address_zip, address_county, etc. Follow Address object
        # attribute conventions, but with address_ as prefix.
        # Optional:
        # location_latitude and location_latitude will fill the location.latitude/longitude attributes
        # Other columns will be turned into arbitrary attributes if possible, followed by transforming
        # underscores.
        df_row = df_row.dropna()  # Remove any Not a Number entries (null/empty cells)
        # Handle location specially since we made it on the top level and address object
        if "location_latitude" in df_row:
            self.location.latitude = df_row["location_latitude"]
            self.address.location.latitude = df_row["location_latitude"]
        if "location_longitude" in df_row:
            self.location.longitude = df_row["location_longitude"]
            self.address.location.longitude = df_row["location_longitude"]
        for attribute_candidate in set(df_row.keys()) - {
            "location_latitude",
            "location_longitude",
        }:
            if (
                attribute_candidate.startswith("address_")
                and attribute_candidate.isidentifier()
            ):
                setattr(
                    self.address, attribute_candidate[8:], df_row[attribute_candidate]
                )
            else:
                # Handle the rest. We hope to see `name` here at least.
                if attribute_candidate.isidentifier():
                    setattr(self, attribute_candidate, df_row[attribute_candidate])
                else:
                    try:
                        setattr(
                            self,
                            space_to_underscore(attribute_candidate),
                            df_row[attribute_candidate],
                        )
                    except:
                        log(
                            "Skipping invalid column name in court list: "
                            + attribute_candidate
                        )
                        pass  # People really need to use sensical column names that can be converted to attributes
                        # but we don't need to throw an exception about it.
            if ensure_lat_long and not (
                hasattr(self.location, "latitude")
                and hasattr(self.location, "longitude")
                and self.location.latitude
                and self.location.longitude
            ):
                # Use Google Maps to geocode if we don't have coordinates and that is desired
                # NOTE: this is causing a problem w/ intrinsic name in the _load_courts method below.
                pass
                # self.address.geolocate() # Note that Docassemble has misnamed geocoding to "geolocate"
                # self.location = self.address.location

    def geolocate(self) -> None:
        """
        Use Google Maps to geocode the court's address and store the result in the location attribute.

        Deprecated: use geocode() instead.
        """
        self.geocode()

    def geocode(self) -> None:
        """
        Use Google Maps to geocode the court's address and store the result in the location attribute.
        """
        self.address.geocode()
        self.location = self.address.location


class ALCourtLoader(DAObject):
    """
    Object to hold some methods surrounding loading/filtering courts.

    Built around Pandas dataframe.

    Attributes:
        filename (str): Path to the file containing court information.
    """

    def init(self, *pargs, **kwargs):
        super().init(*pargs, **kwargs)
        self.package = docassemble.base.functions.this_thread.current_question.package
        if not hasattr(self, "filename"):
            self.filename = (
                self.file_name
            )  # This spelling was a mistake but is everywhere

    # TODO: I think this design makes sense vs saving/storing ALL courts in the Docassemble session.
    # But we might want to at least cache data in Redis to reduce disk hits.
    # Also: think about how to handle court information changing if someone loads data far in the future
    # from a saved interview.
    # Only solution I can think of would require court database owners to assign each court a unique ID
    # and something that triggers recalculating the court address/etc info.

    def all_courts(self) -> List[Dict[int, str]]:
        """
        Return a list of all courts in the spreadsheet.

        Returns:
            List[Dict[int, str]]: List of all ALCourt instances without filtering.
        """
        return self.filter_courts(None)

    def unique_column_values(self, column_name: str) -> Set[str]:
        """
        Retrieve a set of unique values present in a specified dataframe column.

        Args:
            column_name (str): The name of the column in the dataframe.

        Returns:
            Set[str]: A set containing unique values from the specified column.
                      Returns an empty set if an error occurs.
        """
        df = self._load_courts()
        try:
            return set(df[column_name].unique())
        except:
            return set()

    def county_list(self, column_name: str = "address_county") -> Set[str]:
        """
        Get a set of all unique names for the specified column in the given spreadsheet.
        Typically used to get a list of all possible counties that have a court.

        Args:
            column_name (str): The name of the column in the dataframe.

        Returns:
            Set[str]: A list of all unique values in the specified row in the given spreadsheet
        """
        return self.unique_column_values(column_name)

    def county_has_one_court(
        self, county_name: str, county_column: str = "address_county"
    ) -> bool:
        """
        Returns True if there is only one court associated with the specified county
        in the spreadsheet. Returns False otherwise.

        Args:
            county_name (str): The name of the county to check.
            county_column (str): The name of the column in the dataframe that contains the county names.
                                    Defaults to "address_county".

        Returns:
            bool: True if there is only one court associated with the specified county in the spreadsheet.
        """
        return (
            len(self.filter_courts(court_types=county_name, column=county_column)) == 1
        )

    def county_court(
        self,
        intrinsicName: str,
        county_name: str,
        county_column: str = "address_county",
    ) -> ALCourt:
        """
        Return the first court matching the county name. Should only be used
        when you know there is exactly one match

        Args:
            intrinsicName (str): The intrinsic name you want the newly returned object to have (used for DA namespace searching).
            county_name (str): The name of the county to check.
            county_column (str): The name of the column in the dataframe that contains the county names.
                                    Defaults to "address_county".

        Returns:
            ALCourt: The first court matching the county name.

        """
        matches = self.filter_courts(court_types=county_name, column=county_column)
        if len(matches) > 0:
            return self.as_court(intrinsicName, next(iter(matches))[0])
        return ALCourt()

    def matching_courts_in_county(
        self,
        county_name: str,
        county_column: str = "address_county",
        display_column: str = "name",
        search_string: Optional[str] = None,
        search_columns: Optional[Union[List[str], str]] = None,
    ) -> List[Dict[int, str]]:
        """
        Retrieve a list of all courts in the specified county.

        This function fetches courts suitable for displaying as a drop-down or radio button list
        in Docassemble. The results are dictionaries where the key is the index in the dataframe,
        useful for retrieving the court's full details later using the as_court() method.

        Args:
            county_name (str): Name of the county.
            county_column (str, optional): Column heading which contains county name. Defaults to "address_county".
            display_column (str, optional): Column heading used for display in the drop-down. Defaults to "name".
            search_string (Optional[str], optional): A keyword to filter the list of results. Defaults to None.
            search_columns (Optional[Union[List[str], str]], optional): Columns to aggregate and search across with
                the search_string in a case-insensitive manner. Defaults to None.

        Returns:
            List[Dict[int, str]]: List of dictionaries representing matching courts.
        """
        return self.filter_courts(
            court_types=county_name,
            column=county_column,
            display_column=display_column,
            search_string=search_string,
            search_columns=search_columns,
        )

    def filter_courts(
        self,
        court_types: Optional[Union[List[str], str]],
        column: str = "department",
        display_column: str = "name",
        search_string: Optional[str] = None,
        search_columns: Optional[Union[List[str], str]] = None,
    ) -> List[Dict[int, str]]:
        """
        Return a filtered subset of courts represented as a list of dictionaries.

        Each dictionary has the format {index: name}, where "index" refers to the dataframe index and "name"
        is determined by the `display_column`.

        Args:
            court_types (Optional[Union[List[str], str]]): Exact string match or matches used to filter results
                (inclusive). Examples include "District" or ["Municipal","Superior"].
            column (str, optional): Column heading to search. Defaults to "department".
            display_column (str, optional): Column heading used for display in the drop-down. Defaults to "name".
            search_string (Optional[str], optional): A keyword to filter the list of results. Defaults to None.
            search_columns (Optional[Union[List[str], str]], optional): Columns to aggregate and search across with
                the search_string in a case-insensitive manner. Defaults to None.

        Returns:
            List[Dict[int, str]]: List of dictionaries representing filtered courts.
        """
        df = self._load_courts()
        if court_types:
            if isinstance(court_types, str):
                court_types = [court_types]
            # Return only the names for matching values in the specified column
            filtered = df[df[column].isin(court_types)]
        else:
            filtered = df
        if search_string and search_columns:
            if isinstance(search_columns, str):
                search_columns = [search_columns]
            filtered["__search_col"] = (
                filtered[search_columns].fillna("").agg(" ".join, axis=1)
            )
            filtered = filtered[
                filtered["__search_col"].str.contains(search_string, case=False)
            ]
        return list(filtered[display_column].items())  # type: ignore

    def as_court(
        self, intrinsicName: str, index: Union[int, str], ensure_lat_long: bool = True
    ) -> ALCourt:
        """
        Retrieve the court at the specified index as an ALCourt object.

        Args:
            intrinsicName (str): The intrinsic name you want to assign to the returned object (used for DA namespace searching).
            index (Union[int, str]): The index position of the court in the dataframe.
            ensure_lat_long (bool, optional): Whether to ensure the presence of latitude and longitude data. Defaults to True.

        Returns:
            ALCourt: An ALCourt object initialized with data from the specified index.
        """
        court = ALCourt(intrinsicName)
        df = self._load_courts()
        try:
            row = df.loc[int(index)]
        except:
            return court
        court.from_row(row, ensure_lat_long=ensure_lat_long)
        return court

    def _load_courts(self) -> pd.DataFrame:
        """
        Load and return the list of courts from the specified file.

        The method determines the file type (.csv, .xlsx, or .json) based on its extension and reads it accordingly.

        Returns:
            pd.DataFrame: A dataframe containing the list of courts.

        Raises:
            Exception: If the file type is neither CSV, XLSX, nor JSON.
        """
        if not hasattr(self, "filename") and hasattr(self, "file_name"):
            self.filename = self.file_name
        if ":" not in self.filename and hasattr(self, "package"):
            load_path = self.package + ":"
            if "/" not in str(self.filename):
                load_path += "data/sources/"
            load_path += str(self.filename)
        else:
            load_path = str(self.filename)

        to_load = path_and_mimetype(load_path)[0]
        if self.filename.lower().endswith(".xlsx"):
            df = pd.read_excel(to_load)
        elif self.filename.lower().endswith(".csv"):
            df = pd.read_csv(to_load)
        elif self.filename.lower().endswith(".json"):
            # TODO: we may need to normalize a JSON file
            df = pd.read_json(to_load)
        else:
            raise Exception(
                "The datafile must be a CSV, XLSX, or JSON file. Unknown file type: "
                + to_load
            )
        return df
