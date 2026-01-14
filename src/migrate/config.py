"""
This module contains configurations, constant variables, etc. used for the CSV to JSON transformations
"""
import json, yaml, os, sys
from migrate import user

# CONSTANTS

VALID_MODES = ["airtable", "csv"]
VALIED_RECORD_TYPES = ["manuscript_objects", "layers", "text_units", "all"] # Note: "all" will transform all record types at once

# Output directory defaults to the current working directory
OUTPUT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))

TABLES = {}

MODE = ""

AIRTABLE_BASE = ""
AIRTABLE_USER_KEY = ""

# Default metadata and image rights statements
METADATA_RIGHTS = "Unless otherwise indicated, all metadata is copyright the authors and is released under the Creative Commons Attribution 4.0 International License (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/."
IMAGE_RIGHTS = "All manuscript images are the property of St. Catherine’s Monastery of the Sinai. No part of these images may be reproduced, reused, or distributed without prior written permission. For permissions and reuse requests, please contact sinai@library.ucla.edu."

# Default key ordering for top-level objects
# Note: lower-level objects' key ordering are set by the functions which create them (see transform.py if needing to edit)
MS_OBJ_FIELD_ORDER = ["ark", "reconstruction", "type", "shelfmark", "summary", "extent", "weight", "dim", "state", "fol", "coll", "features", "part", "layer", "para", "location", "assoc_date", "assoc_name", "assoc_place", "note", "related_mss", "viscodex", "bib", "iiif", "internal", "desc_provenance", "image_provenance", "cataloguer", "reconstructed_from"]

LAYER_FIELD_ORDER = ["ark", "reconstruction", "state", "label", "locus", "summary", "extent", "writing", "ink", "layout", "text_unit", "para", "assoc_date", "assoc_name", "assoc_place", "features", "related_mss", "note", "bib", "desc_provenance", "cataloguer", "reconstructed_from", "parent", "internal"]

TEXT_UNIT_FIELD_ORDER = ["ark", "reconstruction", "label", "summary", "locus", "lang", "work_wit", "para", "features", "note", "bib", "desc_provenance", "cataloguer", "reconstructed_from", "parent", "internal"]


def set_configs(args):
    # set the global MODE config variable based on the arguments
    set_mode(args.mode)

    # set the Airtable User key from user input based on 
    if args.mode == "airtable":
        global AIRTABLE_USER_KEY
        AIRTABLE_USER_KEY = user.get_airtable_user_key()
    
    # Open the file passed by the args.config value
    # TODO: try/catch i/o issues
    set_table_configs(args.config)

    # add the configuration data for each table's fields to its object
    config_dir_path = os.path.dirname(args.config)
    set_field_configs(base_dir=config_dir_path)
    """
    TODO:
    - hold this space as a place to add more configurations should they prove necessary
    """
    # set the output directory, otherwise defaults to working directory
    if(args.output):
        global OUTPUT_DIR
        OUTPUT_DIR = args.output

def set_mode(mode):
    global MODE
    MODE = mode

def set_table_configs(file_path):
    with open(file_path) as fh:
        data = yaml.safe_load(fh)
        global AIRTABLE_BASE
        AIRTABLE_BASE = data["airtable_base"]
        global TABLES
        TABLES = data["tables"]
        # Resolve any relative paths against the 
        resolve_relative_csv_paths(TABLES, os.path.dirname(file_path), "csv")

# Given a base directory, resolves the relative paths against that base directory
def resolve_relative_csv_paths(tables, base_dir, field_name):
    for table_name in tables:
        if not(tables[table_name][field_name]) or tables[table_name][field_name].startswith("/"):
            continue
        tables[table_name][field_name] = base_dir + "/" + tables[table_name][field_name]

def set_field_configs(base_dir):
    global TABLES
    resolve_relative_csv_paths(TABLES, base_dir, "fields")
    for table_name in TABLES:
        with open(TABLES[table_name]["fields"]) as fh:
            field_data = yaml.safe_load(fh)
            TABLES[table_name]["fields"] = field_data