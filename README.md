This Python script is used for migrating data for the Sinai Manuscripts Data Portal from Airtable and/or CSV formats into Portal-ready JSON documents.

# Installation

The preferred installation method is to use [Poetry](https://python-poetry.org/). Please refer to Poetry documentation for guidance on setting up this tool on your system.

Once Poetry has been added, it can be used to set up a virtual environment and install the dependencies for the migration script.

Clone this repository, then navigate to it in your terminal and run:

 `poetry install`

# Use

Once installed, use poetry to run the script, e.g.:

`poetry run python src/main.py -m csv -c path/to/config all`

The script accepts several command line arguments, which can be viewed by running with the `--help` flag.

The most important/common ones are:

- record type, a required positional argument. Must be one of manuscript_objects, layers, text_units, or all. ('all' can be used to process all record types. Note that each type will be saved to a distinct subdirectory)
- mode (`-m`/`--mode`), required. Must be either 'csv' or 'airtable'. Sets whether data will be loaded from CSV files or downloaded from the Airtable API. See below, under Configuration, for more info
- config directory (`-c`/`--config`), required. The absolute file path to the directory containing the configuration files (table config and field configs). See below, under Configuration, for more info on the contents of this directory.
- output directory (`-o`/`--output`), optional. Specify the directory where JSON data records should be saved; if not included it will default to the current working directory. (Note that record types will be saved in sub-directories of the specified path named based on their record type, e.g. `/foo/bar/layers/`)


The full list of options is as follows:
```
usage: Sinai Portal Migration Script [-h] -m {airtable,csv} [-c CONFIG] [--interactive] [-o OUTPUT] [-t TABLECACHE] {manuscript_objects,layers,text_units,all}

A command line utility for migrating Sinai manuscripts metadata from Airtable or CSVs to Sinai Data Portal-compliant JSON records

positional arguments:
  {manuscript_objects,layers,text_units,all}
                        The record type, must be one of ['manuscript_objects', 'layers', 'text_units'], or use 'all' to transform all types at once

optional arguments:
  -h, --help            show this help message and exit
  -m {airtable,csv}, --mode {airtable,csv}
                        Required. Must be set to one of ['airtable', 'csv']
  -c CONFIG, --config CONFIG
                        Path to the configuration file. Required if not using interactive
  --interactive         Set most configurations interactively
  -o OUTPUT, --output OUTPUT
                        Set the directory where output JSON records should be stored; default is the current working directory
  -t TABLECACHE, --tablecache TABLECACHE
                        A path to a JSON file representing a cached version of the data tables used in the transform. Useful for re-running Airtable data without redownloading if nothing has changed
```

Note: `--interactive` is not yet supported

# Configuration

An example configuration directory is provided in this repository, but it is recommended that users create a copy of this directory elsewhere on their file system and use the `-c`/`--config` option to point to it.

The directory should contain the following:
- `table_configs.yml`, which contains information related to the tables to be transformed
- A `fields` sub-directory with the field configurations for each table

Most changes will occur at the Table Configuration level, such as updated file paths or Airtable URLs.

## Table Configuration

Please refer to the example `table_configs.yml` file for the structure and permitted key/value pairs in this file.

The primary purpose of the Table Configuration file is to indicate the location where data is stored. Only table types which are needed for a given execution of the script must be listed. For example, the `work_witnesses` table does not need to be included if running the script solely for manuscript object data. Likewise, if layer records do not have associated bibliography (i.e., not 'reference instances'), the `bibs` table does not need to be included.

The following keys are permitted for each table type:

- `csv`: the path to the CSV file, required if using csv mode
- `airtable`: the URL of the Airtable table, or of a specific view. Required if using airtable mode
- `fields`: the relative path to the sub-directory containing the field configurations for this table (see below, under Field Configurations)
- `index_col`: This field sets which column contains the unique identifier for the tables' rows. It is required, when using CSV mode, for any table that is referenced from another (e.g., a manuscript object referencing records in the parts table).


Most commonly, changes to configurations will only be to the `csv` or `airtable` parameters.

## Field Configurations

Within a configuration directory, a set of YAML files may be found in the `fields` sub-directory. Each of these files specifies how the individual fields in a given table should be parsed. Please refer to the example configuration files provided in this repository.

**Note: The keys used for individual fields, e.g. `ark` or `type_id` should not be changed as the migration script relies upon these key names to parse the input data.**

These files serve several purposes, including mapping the field name understood by the migration script to the column label used in the CSV or Airtable data. As well, these files set the cardinality and delimiters of certain fields, as well as indicate whether the parser should expect the field to contain the data themselves or references to other tables wherein the data may be found.

The following keys are permitted for each field:
- `name`: This is the column header/label for this field as it appears in the source data (CSV or Airtable table). This property is vital for correctly mapping and parsing data from the table to the corresponding JSON property
- `csv` and `airtable`: these fields control the parsing behavior for the CSV or Airtable modes, respectively. Must be either "text" or "record". If text, the data found in that cell will be exported to the JSON as-is. If record, the parser will use the `lookup` parameter to lookup 
  - Appending a "+" to text ("text+") or record ("record+") marks this field as an array, telling the parser to treat its contents as delimited
  - Note that due a quirk of the Airtable API, some fields may be 'text' for CSV but 'record' for Airtable (e.g., `support_label`). This is fine and expected, resulting in identical output JSON
- `delimiter`: required for "text+" or "record+". Must be an array of one or more items. The parser will convert the value of the data cell into a multi-dimensional array based on the number of specified delimiters. This permits the declaration of fields with multiple levels of delimiting, e.g. `["|~|", "#"]` will first parse data based on the `|~|` character, then any elements of the resulting array into sub-arrays based on the `#` character.
  - Note that for "record+" the parser will first convert the data into an array of record references, then use the `lookup` field for each to pull in the data from the external table
- `lookup`: required for "record" (or "record+"). Must reference another of the table names (e.g., `parts`) and, using a dot separator, specify the field(s) within that table where data may be found. There are three possibilities:
  - A single field lookup, e.g. `supports.label`. The parser will find the row in the corresponding table and use the specified field as its data. Note: must use the config file's name for that field, not the CSV or Airtable column header.
  - All fields, e.g. `paracontents.*`. The parser will find the row in the corresponding table and create a dictionary of all of that row's fields for that table
  - List of fields, e.g. `table.field1,field2,field3`. Note that this is supported by the parser, but no implemented for any fields at this time. Would return a dictionary from the matched row in the corresponding table, but only for the subset of fields specified in the comma-delimited list.

Typed notes are an exception to this rule, allowing extensible lists of note types. They are all grouped under the `typed_notes` (or `part_typed_notes`) key. Please refer to the example field configurations for manuscript objects, layers, or text units for examples of these. Each entry in this list has the following structure:
- The name of the entry, e.g. `fol` must be the value of the note's `type.id` JSON property
- Its `label` property must be the value of the note's `type.label` JSON property
- Otherwise, each has the `name`, `csv`, `airtable`, and `delimiter` properties as described above. It is unlikely for a typed note to have other than "text+" as its field behavior.


# Airtable Mode

Additional information is required to run the script in Airtable mode.

1. The `tables_config.yml` file _should_ have the `airtable_base` parameter set (e.g., "appiXmKhPFEVmVQrD"). If full Airtable URLs are provided for each table, however, this value will be parsed from that URL
2. The script will prompt the user for the path to a `user.json` file, which should have at minimum an `airtable_api_key` with a valid personal access token that includes at minimum read permissions for the Airtable base from which you are pulling data. (see [Personal Access Tokens](https://airtable.com/create/tokens) in the Builder Hub to create one if needed)

The JSON file can be simple, e.g.:
```
{
    "airtable_api_key": "KEY GOES HERE"
}
```