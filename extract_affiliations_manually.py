#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <sebastien.lemaguer@helsinki.fi>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created: 27 January 2026
"""

# Core Python
import argparse
import pathlib
import json
import re

# Messaging/logging
import logging
from logging.config import dictConfig

try:
    import pythonjsonlogger

    JSON_LOGGER = True
except Exception:
    JSON_LOGGER = False

# Data
import pymupdf
import pandas as pd

###############################################################################
# global constants
###############################################################################
LEVEL = [logging.WARNING, logging.INFO, logging.DEBUG]

# NOTE: for now this is a bit dirty, but it works enough
DICT_KNOWN_ISSUES = {
    "\xa0": " ",
    "`a": "a",
    "`e": "e",
    "c¸": "c",
    "s¸": "s",
    "¨O": "o",
    "¨u": "u",
    "´E": "E",
    "´c": "c",
    "´e": "e",
    "´n": "n",
    "´o": "o",
    "´u": "u",
    "´y": "y",
    "´ı": "i",
    "É": "E",
    "Ö": "o",
    "ß": "ss",
    "à": "a",
    "á": "a",
    "ã": "a",
    "ä": "a",
    "å": "a",
    "ç": "c",
    "è": "e",
    "é": "e",
    "ë": "e",
    "í": "i",
    "ñ": "n",
    "ó": "o",
    "ö": "o",
    "ø": "oe",
    "ú": "u",
    "ü": "u",
    "ý": "y",
    "ă": "a",
    "ć": "c",
    "č": "c",
    "ğ": "g",
    "ı": "i",
    "ł": "l",
    "ń": "n",
    "ņ": "n",
    "ň": "n",
    "œ": "oe",
    "ř": "r",
    "ş": "s",
    "Š": "S",
    "š": "s",
    "ū": "u",
    "ů": "u",
    "˚a": "a",
    "ˆe": "e",
    "ˇS": "S",
    "ˇc": "c",
    "ˇr": "r",
    "ˇs": "s",
    "˘g": "g",
    "˚u": "u",
    "˜a": "a",
    "˜n": "n",
    "’": "'",
    '"o': "o",

    # Some weird decoding
    "ﬁ": "fi",
    "Schaufﬂer": "Schauffler",

    # Author inconsistencies or bad recognition
    "Md.": "Md",
    "Pappagari Raghavendra Reddy": "Raghavendra Reddy Pappagari",
    "G Anushiya Rachel": "G. Anushiya Rachel",
    "Alan W. Black": "Alan W Black",
    "Sachin N. Kalkur": "Sachin N Kalkur",
    "S. Shahnawazuddin": "S Shahnawazuddin",
    "T. J. Tsai": "TJ Tsai",
    "Sujith P.": "Sujith. P",
    "J. -A. Gomez-Garcia": "J-A. Gomez-Garcia",
    "T. Villa-Canas": "T.Villa-Canas",
    "G. Nisha Meenakshi": "G.Nisha Meenakshi",
    "k. ramesh": "Ramesh K.",
    "E. Godoy": "elizabeth godoy",
    "thi anh xuan tran": "Tran Thi Anh Xuan",
    "A. Apoorv Reddy": "apoorv reddy arrabothu",
    "James M Scobbie": "james m. scobbie",
    "Thuy N Tran": "Thuy N. Tran",
    "NGUYEN Thi Thu Trang": "thi thu trang nguyen",
    "jin jin": "Jing Zheng",
    "david nolden": "david noldena",
    "laurianne georgeton": "georgeton laurianne",
    "ramani b": "b. ramani",
    "C.-T. Do": "c. -t. do",
    "Pettorino Massimo": "massimo pettorino",
    "Levin K.": "k. levin",
    "Prudnikov A.": "a. prudnikov",
    "DUAN Richeng": "richeng duan",
    "S Aswin Shanmugam": "s. aswin shanmugam",
    "Michael I Mandel": "michael i. mandel",
    "Manson C-M. Fong": "manson c. -m. fong",
    "Murali Karthick B": "Murali Karthick B.",
    "Vikram C. M": "Vikram C. M.",
    "Michael I Mandel": "Michael I. Mandel",
    "Vikram C. M": "Vikram C. M.",
    "Maria K Wolters": "Maria K. Wolters",
    "Douglas Sturim": "Douglas E. Sturim",
    "L. ten Bosch": "Louis ten Bosch",
    "John H. L. Hansen": "John H.L. Hansen",
    "Jeremy H. M. Wong": "Jeremy H.M. Wong",
    "Raymond W. M. Ng": "Raymond W.M. Ng",
    "K V Vijay Girish": "K.V. Vijay Girish",
    "Emma C. L. Leschly": "emma cathrine liisborg leschly",
    "Dirk Eike Hoffner": "dirk hoffner",
    "Dinh-Truong Do": "truong do",
    "LU Mingxi": "mingxi lu",
    "Dashanka De Silva": "dashanka da silva",
    "Mohammed Salah Al-Radhi": "Mohammed Al-Radhi",
    "Keinichi Fujita": "Kenichi Fujita",
    "Griffin Dietz Smith": "Griffin Smith",
    "dominika c woszczyk": "dominika woszczyk",
    "Ankita Ankita": "Ankita",
}


###############################################################################
# Functions
###############################################################################
def configure_logger(args) -> logging.Logger:
    """Setup the global logging configurations and instanciate a specific logger for the current script

    Parameters
    ----------
    args : dict
        The arguments given to the script

    Returns
    --------
    the logger: logger.Logger
    """
    # create logger and formatter
    logger = logging.getLogger()

    # Verbose level => logging level
    log_level = args.verbosity
    if args.verbosity >= len(LEVEL):
        log_level = len(LEVEL) - 1
        # logging.warning("verbosity level is too high, I'm gonna assume you're taking the highest (%d)" % log_level)

    # Define the default logger configuration
    logging_config = dict(
        version=1,
        disable_existing_logger=True,
        formatters={
            "f": {
                "format": "[%(levelname)s] — [%(name)s — %(funcName)s:%(lineno)d] %(message)s",
                # "datefmt": "%d/%b/%Y: %H:%M:%S ",
            }
        },
        handlers={
            "h": {
                "class": "logging.StreamHandler",
                "formatter": "f",
                "level": LEVEL[log_level],
            }
        },
        root={"handlers": ["h"], "level": LEVEL[log_level]},
    )

    # Add file handler if file logging required
    if args.log_file is not None:
        cur_formatter_key = "f"
        if JSON_LOGGER:
            logging_config["formatters"]["j"] = {
                "()": "pythonjsonlogger.json.JsonFormatter",
                "fmt": "%(levelname)s %(filename)s %(lineno)d %(message)s",
                "rename_fields": {
                    # "asctime": "time",
                    "levelname": "level",
                    "lineno": "line_number",
                },
            }
            cur_formatter_key = "j"

        logging_config["handlers"]["f"] = {
            "class": "logging.FileHandler",
            "formatter": cur_formatter_key,
            "level": LEVEL[log_level],
            "filename": args.log_file,
        }
        logging_config["root"]["handlers"] = ["h", "f"]

    # Setup logging configuration
    dictConfig(logging_config)

    # Retrieve and return the logger dedicated to the script
    logger = logging.getLogger(__name__)
    return logger


def define_argument_parser() -> argparse.ArgumentParser:
    """Defines the argument parser

    Returns
    --------
    The argument parser: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="Helper to extract the affiliations from the ISCA archive data using the metadata")

    # Add logging options
    parser.add_argument("-l", "--log_file", default=None, help="Logger file")
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="increase output verbosity",
    )

    # Add arguments
    parser.add_argument("input_metadata_file", help="The input metadata file")
    parser.add_argument("archive_conf_dir", help="The ISCA archive conference directory which contains the PDF")
    parser.add_argument(
        "output_dataframe_affiliations", help="The output dataframe containing the "
    )

    # Return parser
    return parser


###############################################################################
# Helpers
###############################################################################


def clean(dirty: str) -> str:
    """Post-process a dirty string to obtain a clean version

    The process is based on hardcoded rules stored in the dictionary
    DICT_KNOWN_ISSUES

    Parameters
    ----------
    dirty : str
        the dirty string to clean

    Returns
    -------
    str
        the cleaned string
    """

    for k, v in DICT_KNOWN_ISSUES.items():
        dirty = dirty.replace(k, v)
    return dirty


def extract_affiliations(
    paper_id: str, pdf_file: pathlib.Path, authors: list[str]
) -> list[str]:
    """Extract the affiliations from a given PDF file

    The extraction relies on the given list of authors to narrow the search.

    The narrowing is based on 3 informations:
      - from the top, the name of the authors
      - from the bottom, the keyword Abstract (surrounded by only spaces) to detect the beginning of the abstract
      - from the bottom, the characters "{"; "@" and keyword "email" to determine if the authors have indicated an email

    Parameters
    ----------
    paper_id : str
        The ID of the paper to analyze
    pdf_file : pathlib.Path
        The PDF file which contains the affiliations
    authors : list[str]
        The authors of the paper

    Returns
    -------
    list[str]
        The list of lines containing the affiliations

    Raises
    ------
    Exception
        If the authors have not been found in the PDF

    """

    doc = pymupdf.open(pdf_file)
    first_page = doc.load_page(0).get_text()
    logger = logging.getLogger("extract_affiliations")

    # Strip the content to focus on the header
    header = re.sub(r"\n[ \t]*[A]bstract[ \t]*\n.*", "", first_page, flags=re.S)
    header = clean(header)
    header = header.split("\n")

    # Remove the emails and the empty lines
    filtered_header = list(
        filter(
            lambda x: ("@" not in x)
            and (not x.startswith("{"))
            and (not re.match("email", x, re.IGNORECASE))
            and x.strip(),
            header,
        )
    )

    # Search the line containing the authors
    index = -1
    for l_index, l in enumerate(filtered_header):

        # Prepare the line to checked if it contains an author
        maybe_first_author = re.sub(r"[0-9*†‡]", "", l)
        maybe_first_author = (
            maybe_first_author.split(" and ")[0].split(" & ")[0].split(", ")[0]
        )
        maybe_first_author = re.sub(r"[^a-zA-Z-. ']", "", maybe_first_author).strip()
        maybe_first_author = maybe_first_author.lower()

        # Now check if we have an author
        logger.debug(f" - {maybe_first_author}", extra={"paper_id": paper_id})
        if (index == -1) and (maybe_first_author in authors):
            if index == -1:
                index = l_index
        elif (index > -1) and (maybe_first_author not in authors):
            index = l_index
            break

    # No author found...that is not expected!
    if index == -1:
        raise Exception(
            f"no author alignment:\n\t- authors: {authors}\n\t- header: {filtered_header}"
        )

    # Deal with some numerical edge cases
    affiliations = filtered_header[index:]
    affiliations = [re.sub(r"^[0-9]*", "", a) for a in affiliations]
    affiliations = [re.sub(r"[,;] [0-9]+", "\n", a) for a in affiliations]

    # Finalise the list of potential affiliations
    tmp_affiliations = affiliations
    affiliations = []
    for a in tmp_affiliations:
        a = a.strip()
        if not a:
            continue

        if "\n" in a:
            affiliations += a.split("\n")
        else:
            affiliations.append(a)

    return affiliations


###############################################################################
# Entry point
###############################################################################
def main():
    # Initialization of the argument parser and the logger
    arg_parser = define_argument_parser()
    args = arg_parser.parse_args()
    logger = configure_logger(args)

    # Load metadata to access the authors
    with open(args.input_metadata_file) as f_md:
        md = json.load(f_md)

    # Go through each paper to extract the affiliations....
    archive_conf_dir = pathlib.Path(args.archive_conf_dir)
    list_affiliations = []
    for paper_id, paper_info in md["papers"].items():
        authors = [clean(" ".join(a)).lower() for a in paper_info["authors"]]
        pdf_file = archive_conf_dir / f"{paper_id}.pdf"
        if not pdf_file.exists():
            logger.error(
                f"{paper_id} doesn't have a PDF",
                extra={"paper_id": paper_id, "error_step": "pdf_loading"},
            )
            continue
        try:
            affiliations = extract_affiliations(paper_id, pdf_file, authors)
            list_affiliations.append(
                {"paper_id": paper_id, "affiliations": affiliations}
            )
        except Exception as ex:
            logger.error(
                f"{ex}",
                extra={"paper_id": paper_id, "error_step": "affiliations_extraction"},
            )

    # ...and generate the dataframe
    df = pd.DataFrame(list_affiliations)
    df.to_csv(args.output_dataframe_affiliations, sep="\t", index=False)


###############################################################################
# Wrapping for directly calling the scripts
###############################################################################
if __name__ == "__main__":
    main()
