""""
This module deals with wrangling data inputs from airtable or csv files.
These data will be parsed and processed by other modules
"""
import migrate.config as config
import pyairtable
import pandas as pd
import json
import os, time, logging
import dryable
"""
generic get data from config document that calls the airtable or pandas ones
based on the config setting of 'mode', which is from user
maybe here is the for each part?
it should set or add to a variable from config with the data itself?
"""
"""
TODO: consider if should return and set rather than return null and set as side effect?
"""
def get_data():
    logging.info("Getting data")
    if config.MODE == "airtable":
        logging.info("Retrieving data from Airtable")
        airtable_client = pyairtable.Api(config.AIRTABLE_USER_KEY)
    for table in config.TABLES:
        if(config.MODE == "csv"):
            get_table_data_from_csv(config.TABLES[table])
        elif(config.MODE == "airtable"):
            get_table_data_from_airtable(config.TABLES[table], airtable_client)

def get_table_data_from_csv(table_info):
    if table_info.get("csv"):
        with open(table_info["csv"]) as fh:
            table_data = pd.read_csv(fh, index_col=table_info.get("index_col"), dtype=str)
            data = {}
            # Parse the DataFrame into a 2-dim dictionary to match how Airtable will be parsed
            for row_index, row in table_data.iterrows():
                row_data = {}
                for column_index, column in row.items():
                    # Replace nan with None
                    if(pd.isna(column)):
                        row_data[column_index] = None
                    # Otherwise, add the field as a key/value pair
                    else:
                        row_data[column_index] = column
                data[str(row_index)] = row_data
            table_info["data"] = data

def get_table_data_from_airtable(table_info, airtable_client):
    # get and parse the URL into the base, table, and view keys
    url = table_info["airtable"]
    logging.info(f"getting Airtable data for {url}")
    base_key, table_key, view_key = parse_airtable_url(url)
    # TODO: Check base_key against config.AIRTABLE_BASE
    
    # use the API parameters to get all records from the table (and view, if not None)
    table_data = airtable_client.table(base_key, table_key).all(view=view_key)

    # Parse this data into a dictionary where the keys represent the Airtable record ID
    table_info["data"] = {record["id"]:record["fields"] for record in table_data}

"""
Assumes that URL looks like https://airtable.com/appiXmKhPFEVmVQrD/tblKIvl8xqSkze5jF/viwn0c2SSDH6oXvyq
The view URL is optional
"""
def parse_airtable_url(url):
    # get the list of keys from the URL path portion
    keys_string = url.split("airtable.com/")[1]
    keys = keys_string.split("/")

    # make sure the last one doesn't have trailing whitespace or search parameters
    keys[-1] = keys[-1].rstrip().split("?")[0]

    # add None for the view key if not included
    if len(keys) < 3:
        keys.append(None)

    return keys


"""
Saves a data record in the configured output directory, with an optional sub directory declared
Note: defaulting the sub_dir to "/" means it will ensure the working directory will end with a slash
"""
@dryable.Dryable(logging_msg='Skipping {function} (--dryrun)')
def save_record(record, file_name, sub_dir="/"):
    save_dir = config.OUTPUT_DIR + sub_dir
    logging.info(f'\t- Saving record {record["ark"]} to disk. Filepath: {save_dir + file_name + ".json"}')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with open(save_dir+file_name+".json", mode="w") as fh:
            json.dump(record, fh, indent=2, ensure_ascii=False)

"""
Saves the config.TABLES data as a JSON file for easy reuse, mostly for avoiding multiple calls to Airtable's APIs
"""
@dryable.Dryable(logging_msg='Skipping {function} (--dryrun)')
def cache_wrangled_tables(sub_dir="/table_cache/"):
    save_dir = config.OUTPUT_DIR + sub_dir
    timestr = time.strftime("%Y%m%d-%H%M%S")
    filename = "table_cache_" + timestr + ".json"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with open(save_dir+filename, mode="w") as fh:
        json.dump(config.TABLES, fh, indent=2, ensure_ascii=False)

def use_cached_tables(path_to_table_cache):
    logging.info("Loading cached table data")
    with open(path_to_table_cache) as fh:
        tables = json.load(fh)
        config.TABLES = tables

@dryable.Dryable(logging_msg='Skipping {function} (--dryrun)')
def save_validation_errors(log, sub_dir, filename_prexif):
    save_dir = config.OUTPUT_DIR + sub_dir
    filename = filename_prexif + "_validation_errors.json"
    logging.info(f"Validation file saved to {save_dir+filename}")
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    with open(save_dir+filename, mode="w") as fh:
        json.dump(log, fh, indent=2, ensure_ascii=False)