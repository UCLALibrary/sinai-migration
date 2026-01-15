import jschon, json, requests, os, sys, dryable
import migrate.config as config

'''
CONSTANTS
'''
@dryable.Dryable()
def initialize_schema(record_type):
    schema_url = config.SCHEMA_URLS[record_type]
    schema_json = requests.get(schema_url).json()
    return jschon.JSONSchema(schema_json)

@dryable.Dryable()
def validate_record(record, schema):
    result = schema.evaluate(jschon.json.JSON(record))
    # only include invalid ones
    if(not(result.output('flag')['valid'])):
        validation_result = {"record_ark": record["ark"]}
        validation_result = validation_result | result.output('basic')
        return validation_result