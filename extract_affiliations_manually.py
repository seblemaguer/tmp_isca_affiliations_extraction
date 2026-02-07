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
    ", ˘a": "a",
    "\xa0": " ",
    "`a": "a",
    "`e": "e",
    "`o": "o",
    "c¸": "c",
    "s¸": "s",
    "¨O": "o",
    "¨u": "u",
    "´E": "E",
    "´a": "a",
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
    "î": "i",
    "ï": "i",
    "ñ": "n",
    "ò": "o",
    "ó": "o",
    "ö": "o",
    "ø": "oe",
    "ú": "u",
    "ü": "u",
    "ý": "y",
    "ă": "a",
    "ć": "c",
    "č": "c",
    "ę": "e",
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
    "ˆe": "e",
    "ˆı": "i",
    "ˇS": "S",
    "ˇc": "c",
    "ˇr": "r",
    "ˇs": "s",
    "˘g": "g",
    "˚a": "a",
    "˚u": "u",
    "˛e": "e",
    "˜a": "a",
    "˜n": "n",
    "’": "'",
    '"o': "o",

    # Some weird decoding
    "ﬁ": "fi",
    "Schaufﬂer": "Schauffler",

    # Author inconsistencies or bad recognition
    "md.": "md",
    "pappagari raghavendra reddy": "raghavendra reddy pappagari",
    "g anushiya rachel": "g. anushiya rachel",
    "alan w. black": "alan w black",
    "sachin n. kalkur": "sachin n kalkur",
    "s. shahnawazuddin": "s shahnawazuddin",
    "t. j. tsai": "tj tsai",
    "sujith p.": "sujith. p",
    "j. -a. gomez-garcia": "j-a. gomez-garcia",
    "t. villa-canas": "t.villa-canas",
    "g. nisha meenakshi": "g.nisha meenakshi",
    "k. ramesh": "ramesh k.",
    "e. godoy": "elizabeth godoy",
    "thi anh xuan tran": "tran thi anh xuan",
    "a. apoorv reddy": "apoorv reddy arrabothu",
    "james m scobbie": "james m. scobbie",
    "thuy n tran": "thuy n. tran",
    "nguyen thi thu trang": "thi thu trang nguyen",
    "jin jin": "jing zheng",
    "david nolden": "david noldena",
    "laurianne georgeton": "georgeton laurianne",
    "ramani b": "b. ramani",
    "c.-t. do": "c. -t. do",
    "pettorino massimo": "massimo pettorino",
    "levin k.": "k. levin",
    "prudnikov a.": "a. prudnikov",
    "duan richeng": "richeng duan",
    "s aswin shanmugam": "s. aswin shanmugam",
    "michael i mandel": "michael i. mandel",
    "manson c-m. fong": "manson c. -m. fong",
    "murali karthick b": "murali karthick b.",
    "vikram c. m": "vikram c. m.",
    "michael i mandel": "michael i. mandel",
    "vikram c. m": "vikram c. m.",
    "maria k wolters": "maria k. wolters",
    "douglas sturim": "douglas e. sturim",
    "l. ten bosch": "louis ten bosch",
    "john h. l. hansen": "john h.l. hansen",
    "jeremy h. m. wong": "jeremy h.m. wong",
    "raymond w. m. ng": "raymond w.m. ng",
    "k v vijay girish": "k.v. vijay girish",
    "emma c. l. leschly": "emma cathrine liisborg leschly",
    "dirk eike hoffner": "dirk hoffner",
    "dinh-truong do": "truong do",
    "lu mingxi": "mingxi lu",
    "dashanka de silva": "dashanka da silva",
    "mohammed salah al-radhi": "mohammed al-radhi",
    "keinichi fujita": "kenichi fujita",
    "griffin dietz smith": "griffin smith",
    "dominika c woszczyk": "dominika woszczyk",
    "ankita ankita": "ankita",
    "ahmed adel attia": "ahmed attia",
    "hawau olamide toyin": "hawau toyin",
    "enes yavuz ugan": "enes ugan",
    "zheng-xin yong": "zheng xin yong",
    "nagarathna r": "nagarathna ravi",
    "nagarathna raviavi": "nagarathna ravi",
    "jiaxin chen": "jia-xin chen",
    "sai akarsh c": "sai akarsh",
    "sarah si chen": "si chen",
    "cheng-hung hu": "chenghung hu",
    "xiaowang liu": "liu xiaowang",
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
    dirty = dirty.lower().strip()
    dirty = re.sub(r' ([a-z]) ', r' \g<1>. ', dirty)
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
    cleaned_header = clean("\n".join(filtered_header).lower()).split("\n")

    # Clean the authors
    cleaned_authors = [clean(" ".join(a)) for a in authors]

    # Search the line containing the authors
    index = -1

    for l_index, l in enumerate(cleaned_header):

        # Prepare the line to checked if it contains an author
        maybe_first_author = re.sub(r"[0-9*†‡]", "", l)
        maybe_first_author = (
            maybe_first_author.split(" and ")[0].split(" & ")[0].split(", ")[0].split("; ")[0].strip()
        )
        maybe_first_author = re.sub(r"[^a-zA-Z-. ']", "", maybe_first_author).strip()
        maybe_first_author = maybe_first_author.lower()
        if maybe_first_author.startswith("jinxin"):
            print(maybe_first_author)

        # Now check if we have an author
        logger.debug(f" - {maybe_first_author}", extra={"paper_id": paper_id})
        if (index == -1) and (maybe_first_author in cleaned_authors):
            if index == -1:
                index = l_index
        elif (index > -1) and (maybe_first_author not in cleaned_authors):
            index = l_index
            break

    # No author found...that is not expected!
    if index == -1:
        raise Exception(
            f"no author alignment:\n\t- authors: {authors}\n\t- cleaned_authors: {cleaned_authors}\n\t- filtered_header: {filtered_header}\n\t- cleaned_header: {cleaned_header}"
        )

    # Deal with some numerical edge cases
    affiliations = cleaned_header[index:]
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
        pdf_file = archive_conf_dir / f"{paper_id}.pdf"
        if not pdf_file.exists():
            logger.error(
                f"{paper_id} doesn't have a PDF",
                extra={"paper_id": paper_id, "error_step": "pdf_loading"},
            )
            continue
        try:
            affiliations = extract_affiliations(paper_id, pdf_file, paper_info["authors"])
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
