import migrate
import argparse
import logging

def main(args):
    # make sure a valid mode (csv or airtable) has been selected
    migrate.user.ensure_valid_mode(args, migrate.config.VALID_MODES)

    # set some configurations interactively if not supplied as comman   d line args
    # also used if no config file was provided
    if(args.interactive or not(args.config)):
        migrate.user.get_configs_interactive(args)
    
    migrate.config.set_configs(args)

    if(args.tablecache):
        migrate.wrangle.use_cached_tables(args.tablecache)
    else:
        migrate.wrangle.get_data()
        migrate.wrangle.cache_wrangled_tables()

    # Migrate all record types, or the one selected
    if(args.record_type == "all"):
        migrate.transform.transform_records("manuscript_objects")
        migrate.transform.transform_records("layers")
        migrate.transform.transform_records("text_units")
    else:
        migrate.transform.transform_records(args.record_type)


if __name__ == "__main__":
    # Set up an argparse parser and add CLI args
    parser = argparse.ArgumentParser(prog="Sinai Portal Migration Script",
                                     description="A command line utility for migrating Sinai manuscripts metadata from Airtable or CSVs to Sinai Data Portal-compliant JSON records")

    parser.add_argument('record_type',
                        choices=migrate.config.VALIED_RECORD_TYPES,
                        help=f"The record type, must be one of {migrate.config.VALIED_RECORD_TYPES[:-1]}, or use 'all' to transform all types at once")
    
    # Optional/flag arguments arguments
    parser.add_argument('-m', '--mode',
                        choices=migrate.config.VALID_MODES,
                        help=f"Required. Must be set to one of {migrate.config.VALID_MODES}",
                        required=True)
    parser.add_argument('-c', '--config',
                        help="Path to the configuration file. Required if not using interactive")
    parser.add_argument('--interactive',
                        help="Set most configurations interactively",
                        action='store_true')
    parser.add_argument('-o', '--output',
                        help="Set the directory where output JSON records should be stored; default is the current working directory")
    parser.add_argument('-t', '--tablecache',
                        help="A path to a JSON file representing a cached version of the data tables used in the transform. Useful for re-running Airtable data without redownloading if nothing has changed")
    parser.add_argument('-v', '--validate',
                        help="Validate all transformed records against the record types' schema. A record of invalid files and their errors will be saved to the output directory",
                        action='store_true')
    parser.add_argument('--dryrun',
                        help="Run the script without saving files to disk",
                        action='store_true')
    parser.add_argument('-d', '--debug',
                        help="Print all debug, warning, and info statements",
                        action="store_const", dest="loglevel", const=logging.DEBUG,
                        default=logging.WARNING,
    )
    parser.add_argument('--verbose',
                        help="Print additional information besides warnings and errors",
                        action="store_const", dest="loglevel", const=logging.INFO,
    )
    args = parser.parse_args()

    main(args)