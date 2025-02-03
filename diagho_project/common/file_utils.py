import json

# Pretty print json string
def pretty_print_json_string(string):
    """
    Pretty print a JSON string.

    Arguments:
        json_str (str): The JSON string to be pretty printed.
    """
    try:
        json_string = json.dumps(string)
        json_dict = json.loads(json_string)
        print(json.dumps(json_dict, indent = 1))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON string: {e}")
     