import json

# Define the path to the JSON file
config_path = "/data/options.json"

# Read the JSON file
with open(config_path, "r") as file:
    config_data = json.load(file)

# Print the contents
print(json.dumps(config_data, indent=2))
