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
import traceback

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
    "¨a": "a",
    ", ˘a": "a",
    ",˘a": "a",
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
    "´s": "s",
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
    "ê": "e",
    "ë": "e",
    "í": "i",
    "î": "i",
    "ï": "i",
    "ð": "d",
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
    "ė" : "e",
    "ę": "e",
    "ě": "e",
    "ğ": "g",
    "ı": "i",
    "ł": "l",
    "ń": "n",
    "ņ": "n",
    "ň": "n",
    "œ": "oe",
    "ř": "r",
    "ś": "s",
    "ś": "s",
    "ş": "s",
    "Š": "S",
    "š": "s",
    "ū": "u",
    "ů": "u",
    "ž": "z",
    "ˆe": "e",
    "ˆı": "i",
    "ˇS": "S",
    "ˇc": "c",
    "ˇe": "e",
    "ˇr": "r",
    "ˇs": "s",
    "ˇz": "z",
    "˙z": "z",
    "ż": "z",
    "˘g": "g",
    "˚a": "a",
    "˚u": "u",
    "˛e": "e",
    "˜a": "a",
    "˜n": "n",
    "’": "'",
    '"o': "o",
    "ˆo": "o",
    "¯a": "a",
    "ā": "a",
    "˘a": "a",

    # Some weird decoding
    "ﬁ": "fi",
    "ﬂ": "fl",
}

DICT_NAME_ISSUES = {
    "a padmasundary": "padmasundary",
    "a. apoorv reddy": "arrabothu apoorv reddy",
    "a.apoorv reddy": "apoorv reddy arrabothu",
    "achyut mani tripathi": "achyut tripathi",
    "adaeze adigwe": "adaeze o. adigwe",
    "ahmed adel attia": "ahmed attia",
    "alan w.black": "alan w black",
    "alvaro iturralde zurita": "alvaro martin iturralde zurita",
    "andreas soeeborg kirkedal": "andreas kirkedal",
    "ankita ankita": "ankita",
    "anusha prakash": "anusha p",
    "binu abeysinghe": "binu nisal abeysinghe",
    "bronya r. chernyak": "bronya roni chernyak",
    "c. d. rios-urrego": "cristian david rios-urrego",
    "chandan k.a. reddy": "chandan reddy",
    "cheng-hung hu": "chenghung hu",
    "chia-hsuan li": "chia-hsuan lee",
    "chunhui wang": "wang chunhui",
    "claus m. larsen": "claus larsen",
    "daniel r. van niekerk": "daniel van niekerk",
    "daniel yue zhang": "daniel zhang",
    "dashanka de silva": "dashanka da silva",
    "david m. chan": "david chan",
    "david nolden": "david noldena",
    "david noldenaa": "david noldena",
    "david r. feinberg": "david feinberg",
    "debasish ray mohapatra": "debasish mohapatra",
    "digvijay anil ingle": "digvijay ingle",
    "dinh-truong do": "truong do",
    "dino ratcliffe": "dino rattcliffe",
    "dirk eike hoffner": "dirk hoffner",
    "dominika c. woszczyk": "dominika woszczyk",
    "douglas sturim": "douglas e.sturim",
    "duan richeng": "richeng duan",
    "e.godoy": "elizabeth godoy",
    "emma cathrine liisborg leschly": "emma c. l. leschly",
    "enes yavuz ugan": "enes ugan",
    "evdokia kazimirova'": "e azimirova",
    "fougeron c.": "cecile fougeron",
    "franklin alvarez cardinale": "franklin alvarez",
    "g anushiya rachel": "g.anushiya rachel",
    "g. r. kasthuri": "g kasthuri",
    "g.laperriere": "gaelle laperriere",
    "g.nisha meenakshi": "g.nisha meenakshi",
    "geoffrey t. frost": "geoffrey frost",
    "griffin dietz smith": "griffin smith",
    "guan-tin liou": "guan-ting liou",
    "hardik b. sailor": "hardik sailor",
    "hawau olamide toyin": "hawau toyin",
    "hector a. cordourier maruri": "hector a.cordourier",
    "huu tuong tu": "tuong tu huu",
    "iroro fred o. no. me. orife": "Iroro Orife",
    "j-a. gomez-garcia": "j-a.gomez-garcia",
    "j. c. vasquez-correa": "juan camilo vasquez-correa",
    "j.-a.gomez-garcia": "j-a.gomez-garcia",
    "j.c. vasquez-correa": "juan camilo vasquez-correa",
    "j.linke": "julian linke",
    "j.martinezsevilla": "j.martinez-sevilla",
    "jacob j. webber": "jacob webber",
    "james m scobbie": "james m.scobbie",
    "jennifer drexler fox": "jennifer fox",
    "jenny yeonjin cho": "yeonjin cho",
    "jeremy h. m. wong": "jeremy heng meng wong",
    "jeremy h.m.wong": "jeremy h.m.wong",
    "jeremy heng meng won": "jeremy h.m. wong",
    "jiaxin chen": "jia-xin chen",
    "jin jin": "jing zheng",
    "joao dinis freitas": "joao freitas",
    "joao p. cabral": "joao cabral",
    "john h.l.hansen": "john h.l.hansen",
    "john s. novak iii": "john s. novak",
    "john w. kim": "john kim",
    "jose vicente egas-lopez": "jose egas-lopez",
    "jovan dalhouse": "jovan m. dalhouse",
    "juan carlos": "juan c.",
    "juan f. montesinos": "juan felipe montesinos",
    "juncheng b. li": "juncheng li",
    "k v vijay girish": "k.v.vijay girish",
    "k.m.knill": "kate knill",
    "k.ramesh": "ramesh k.",
    "keinichi fujita": "kenichi fujita",
    "kun zhou a.": "kun zhou",
    "kyu j. han": "kyu han",
    "l. ten bosch": "loui ten bosh",
    "l.l chamara kasun": "chamara kasun",
    "l.ten bosch": "louis ten bosch",
    "lani rachel mathew": "lani mathew",
    "laurianne georgeton": "georgeton laurianne",
    "levin k.": "k.levin",
    "lu mingxi": "mingxi lu",
    "m raza": "mohsin raza",
    "m. a. tugtekin turan": "mehmet ali tugtekin turan",
    "m. iftekhar tanveer": "md iftekhar tanveer",
    "m.a. tugtekin turan": "mehmet ali tugtekin turan",
    "m.rohmatillah": "mahdin rohmatillah",
    "madhavaraj ayyavu": "madhavaraj a",
    "madhu r. kamble": "madhu kamble",
    "manson c-m.fong": "manson c.-m.fong",
    "manuel sam ribeiro": "sam ribeiro",
    "marc a. hullebus": "marc antony hullebus",
    "maria k wolters": "maria k.wolters",
    "md.": "md",
    "megan m. willi": "megan willi",
    "michel meneses": "michel cardoso meneses",
    "mohammed salah al-radhi": "mohammed al-radhi",
    "mortaza (morrie) doulaty": "mortaza doulaty",
    "mudit batra": "mudit d. batra",
    "murali karthick b": "murali karthick b.",
    "nagarathna r": "nagarathna ravi",
    "nagarathna raviavi": "nagarathna ravi",
    "nathan young": "nathan joel young",
    "nathaniel robinson": "nathaniel romney robinson",
    "neha k. reddy": "neha reddy",
    "ngoc-quan pham": "quan pham",
    "nguyen thi thu trang": "thi thu trang nguyen",
    "nicolae-catalin ristea": "nicolaea-catalin ristea",
    "nicolas m. muller": "nicolas muller",
    "nirmesh j. shah": "nirmesh shah",
    "p. a. perez-toro": "paula andrea perez-toro",
    "p.a.pereztoro": "paula a.pereztoro",
    "pappagari raghavendra reddy": "raghavendra reddy pappagari",
    "paul k. krug": "paul konstantin krug",
    "pettorino massimo": "massimo pettorino",
    "phani nidadavolu": "phani sankar nidadavolu",
    "prasad a. tapkir": "prasad tapkir",
    "prudnikov a.": "a.prudnikov",
    "quoc-huy nguyen": "huy nguyen",
    "ram c.m.c shekar": "ram c.m.c.shekar",
    "ram charan m. c": "ram charan chandra shekar",
    "ramani b": "b.ramani",
    "ranzo c. f. huang": "ranzo huang",
    "ranzo c.f.huang": "ranzo huang",
    "raymond w.m.ng": "raymond w.m.ng",
    "rini sharon a": "rini a sharon",
    "rob j. j. h. van son": "rob van son",
    "rob j.j.h. van son": "rob van son",
    "rodrigo schoburg carrillo de mira": "rodrigo mira",
    "ryan m. corey": "ryan corey",
    "ryandhimas e. zezario": "ryandhimas edo zezario",
    "s aswin shanmugam": "s.aswin shanmugam",
    "s.shahnawazuddin": "s shahnawazuddin",
    "sachin n.kalkur": "sachin n kalkur",
    "sai akarsh c": "sai akarsh",
    "samuel d. bellows": "samuel bellows",
    "samuel j. yang": "samuel yang",
    "sarah si chen": "si chen",
    "sarenne carrol wallbridge": "sarenne wallbridge",
    "sebastian p. bayerl": "sebastian peter bayerl",
    "soha a. nossier": "soha nossier",
    "sujith p.": "sujith.p",
    "t pavan kalyan": "tankala pavan kalyan",
    "t.arias-vergara": "tomas arias-vergara",
    "t.j.tsai": "tj tsai",
    "t.villa-canas": "t.villa-canas",
    "teun f. krikke": "teun krikke",
    "thi anh xuan tran": "tran thi anh xuan",
    "tho tran": "tho nguyen duc tran",
    "thuy n tran": "thuy n.tran",
    "tom o'malley": "thomas r. omalley",
    "tomek rutowski": "tomasz rutowski",
    "tunde szalay": "tuende szalay",
    "tzeviya sylvia fuchs": "tzeviya fuchs",
    "valter a. miasato filho": "valter akira miasato filho",
    "venkatesh s. kadandale": "venkatesh shenoy kadandale",
    "vikram c.m": "vikram c.m.",
    "vikram c.m": "vikram c.m.",
    "w.q. zheng": "weiqiao zheng",
    "wiebke (toussaint) hutiri": "wiebke toussaint",
    "william f. katz": "william katz",
    "xiaowang liu": "liu xiaowang",
    "yiteng (arden) huang": "yiteng huang",
    "zhao shuyang": "shuyang zhao",
    "zheng-xin yong": "zheng xin yong",
    "zoltan tuskea": "zoltan tuske",
    # "c.-t.do": "c.-t.do",
    # "michael i mandel": "michael i.mandel",
    # "michael i mandel": "michael i.mandel",
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
    parser.add_argument("country_file", help="The country file")
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
    dirty = re.sub(r'^([a-z]) ', r'\g<1>. ', dirty)

    for k, v in DICT_KNOWN_ISSUES.items():
        dirty = dirty.replace(k, v)

    for k, v in DICT_NAME_ISSUES.items():
        dirty = dirty.replace(k, v)

    # dirty = re.sub(r'([^,]) [a-z][.] [a-z][.] ', r'\g<1> ', dirty)
    # dirty = re.sub(r'([^,]) [a-z][.] ', r'\g<1> ', dirty)
    return dirty


def extract_affiliations(
        paper_id: str, pdf_file: pathlib.Path, authors: list[str], countries: list[str]
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
    countries: list[str]
        The list of countries to be considered to avoid delete an affiliation by mistake

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

    # Generate a regexp to test the countries
    re_countries = re.compile(f'({"|".join(countries)})$')

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
    cleaned_header = clean("\n".join([l.strip() for l in filtered_header]).lower()).split("\n")

    # Clean the authors
    cleaned_authors = [clean(" ".join(a)) for a in authors]
    def _initial(a: list[str]) -> list[str]:
        if len(a[0]) == 0:
            return[a[1]]
        else:
            return [a[0][0] + "."] + [a[1]]

            raise Exception(authors)
    cleaned_authors += [clean(" ".join(_initial(a))) for a in authors]
    cleaned_authors += [clean(" ".join(a[::-1])) for a in authors]
    cleaned_authors = [re.sub(r"[^a-z]", "", a).strip() for a in cleaned_authors]

    # Search the line containing the authors
    index = -1

    for l_index, l in enumerate(cleaned_header):

        l = l.strip()
        if (index > -1) and (re.search(r'[^ 0-9]\d$', l) is not None):
            l_tmp = re.sub(r'[0-9,]+$', '', l).strip()
            if (re_countries.search(l_tmp) is None) and (l_index < len(cleaned_header) - 1):
                logger.debug(f" - Found a potential incomplete author line")
                index = l_index
                continue

        # Prepare the line to checked if it contains an author
        maybe_first_author = re.sub(r"[*†‡]", "", l)
        maybe_first_author = re.sub(r'[0-9],([^0-9])', r', \g<1>', maybe_first_author)
        maybe_first_author = re.sub(r'([^0-9]),([^0-9])', r'\g<1>, \g<2>', maybe_first_author)
        maybe_first_author = re.sub(r'([0-9]) ([^0-9])', r'\g<1>, \g<2>', maybe_first_author)
        maybe_first_author = re.sub(r"[0-9]", "", maybe_first_author)
        maybe_first_author = (
            maybe_first_author.split(" and ")[0].split(" & ")[0].split(", ")[0].split("; ")[0].strip()
        )
        maybe_first_author = re.sub(r"[^a-z]", "", maybe_first_author ).strip()
        maybe_first_author = maybe_first_author.lower()

        # Try to find all lines starting with an author
        logger.debug(f" - {maybe_first_author}", extra={"paper_id": paper_id})
        if maybe_first_author in cleaned_authors:
            index = l_index
        else:
            if index > -1:
                break

    # No author found...that is not expected!
    if index == -1:
        raise Exception(
            f"no author alignment:\n\t- authors: {authors}\n\t- cleaned_authors: {cleaned_authors}\n\t- filtered_header: {filtered_header}\n\t- cleaned_header: {cleaned_header}"
        )

    # Deal with some numerical edge cases
    affiliations = cleaned_header[index+1:]
    affiliations = [re.sub(r"^[0-9]*", "", a) for a in affiliations]
    affiliations = [re.sub(r" ([a-z])[.] ", r" \g<1> ", a) for a in affiliations]
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

    country_df = pd.read_csv(args.country_file)
    countries = [clean(n) for n in country_df["name"]]
    countries.append(" ai") # NOTE: this is added because a lot of companies start to put AI as part of their name...

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
            affiliations = extract_affiliations(paper_id, pdf_file, paper_info["authors"], countries)
            list_affiliations.append(
                {"paper_id": paper_id, "affiliations": affiliations if affiliations else None}
            )
        except Exception as ex:
            logger.error(
                # f"{ex}:\n{traceback.format_exc()}",
                f"{ex}:\n",
                extra={"paper_id": paper_id, "error_step": "affiliations_extraction", "stacktrack": traceback.format_exc()},
            )

            list_affiliations.append(
                {"paper_id": paper_id, "affiliations": None}
            )

    # ...and generate the dataframe
    df = pd.DataFrame(list_affiliations)
    df.to_csv(args.output_dataframe_affiliations, sep="\t", index=False)


###############################################################################
# Wrapping for directly calling the scripts
###############################################################################
if __name__ == "__main__":
    main()
