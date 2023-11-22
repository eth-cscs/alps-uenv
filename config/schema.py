import json
import pathlib

import jsonschema
import yaml

prefix = pathlib.Path(__file__).parent.resolve()

# create a validator that will insert optional fields with their default values
# if they have not been provided.


def extend_with_default(validator_class):
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator,
            properties,
            instance,
            schema,
        ):
            yield error

    return jsonschema.validators.extend(
        validator_class,
        {"properties": set_defaults},
    )


def py2yaml(data, indent):
    dump = yaml.dump(data)
    lines = [ln for ln in dump.split("\n") if ln != ""]
    res = ("\n" + " " * indent).join(lines)
    return res



# create validator for json schema
config_schema = json.load(open(prefix / "config-schema.json"))
validator = extend_with_default(jsonschema.Draft7Validator)
config_validator = validator(config_schema)

# load the configuration and validate
config = yaml.load(open(prefix / "config.yaml"), Loader=yaml.Loader)
config_validator.validate(config)

pipelines = config["pipelines"]
clusters = config["clusters"]

print("=-= clusters =-=")
for k in clusters.keys():
    print(k, clusters[k]["uarch"])

print()
print("=-= pipelines =-=")
for k in pipelines.keys():
    print(k)
    print(pipelines[k])
