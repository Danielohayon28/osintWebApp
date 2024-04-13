from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import datetime
import pandas as pd
import uuid
import json
import os
import re

app = Flask(__name__)
CORS(app)  

# Dictionary to store scan results with ID as key .
# Actually should be stored in database
SCAN_RESULTS = {}


# docker commands 
def run_theHarvester(domain):
    command = f"python /theHarvester/theHarvester.py -d {domain} -b all"
    result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    return result.strip()

def run_Amass(domain):
    command = f"~/go/bin/amass enum -passive -d {domain}"
    
    # command = f"docker run -v OUTPUT_DIR_PATH:/.config/amass/ caffix/amass enum -passive -d develop.carteav.com"

    result = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
    print(result.strip())
    return result.strip()


# Amass parser fucntions - start
def parse_line(line):
    
    parts = line.split(" --> ")
    if len(parts) < 2:
        return None, None, None, None 

    first_part = parts[0]
    second_part = parts[-1]

    key_1, value_1 = parse_key_value(first_part)
    key_2, value_2 = parse_key_value(second_part)

    return key_1, value_1, key_2, value_2

def parse_key_value(part):
    
    key = part.split("(")[1].split(")")[0]
    value = part.split(" ")[0]
    return key, value

def parse_amass_results(response):
    
    map_data = {}
    lines = response.split('\n')
    
    for line in lines:
        key_1, value_1, key_2, value_2 = parse_line(line)

           # Check if any of the keys or values are None
        if None in (key_1, value_1, key_2, value_2):
            # Skip this line or handle it differently (e.g., print a warning)
            print(f"Warning: Line '{line}' does not match the expected format")
            continue

        if key_1 not in map_data:
            map_data[key_1] = []
        map_data[key_1].append(value_1)

        if key_2 not in map_data:
            map_data[key_2] = []
        map_data[key_2].append(value_2)

    return map_data
# Amass parser fucntions - end


# theHarvester parser fucntions - start
def remove_items_before_relevant_data_theHarvester(strings):
    
    found_index = next((i for i, s in enumerate(strings) if "found:" in s), None)
    if found_index is None:
        return strings

    return strings[found_index:]

def extract_key_from_line(line):
    
    if 'found' in line.lower():
        key = line.split('[*] ')[1].replace(' found:', '')
        #key contains also the number of rows (so we remove it)
        key = ''.join([i for i in key if not i.isdigit()]).strip()
        return key
    return None

def parse_theHarvester_response(response):

    relevant_data = {}
    lines = response.split('\n')

    current_data = remove_items_before_relevant_data_theHarvester(lines)

    current_key = ""
    for line in current_data:
        key = extract_key_from_line(line)
        if key:
            current_key = key
            relevant_data[current_key] = []
        elif current_key and re.search(r'\w', line):
            relevant_data[current_key].append(line)

    return relevant_data
# theHarvester parser fucntions - start


# merge response -start
def safe_pop(dictionary, key):
    if key in dictionary:
        return dictionary.pop(key)
    return None

def merge_maps(theTharvester_map, amass_map):
    merged_map = {}
    
    # Merge ASNS and ASN
    asns = list(set(theTharvester_map.get("ASNS", []) + amass_map.get("ASN", [])))
    if asns:
        merged_map["ASNs"] = asns
        safe_pop(theTharvester_map, "ASNS")
        safe_pop(amass_map, "ASN")

    # Merge IPs and IPAddress
    ips = list(set(theTharvester_map.get("IPs", []) + amass_map.get("IPAddress", [])))
    if ips:
        merged_map["IPAddress"] = ips
        safe_pop(theTharvester_map, "IPs")
        safe_pop(amass_map, "IPAddress")

    # Merge Hosts and FQDN
    hosts = list(set(theTharvester_map.get("Hosts", []) + amass_map.get("FQDN", [])))
    if hosts:
        merged_map["Hosts"] = hosts
        safe_pop(theTharvester_map, "Hosts")
        safe_pop(amass_map, "FQDN")

    # Merge the rest of the keys
    for key in theTharvester_map.keys():
        merged_map[key] = theTharvester_map[key]

    for key in amass_map.keys():
        merged_map[key] = amass_map[key]

    return merged_map
# merge response -end


def load_saved_scans_from_file():
    try:
        with open('saved_scans.json', 'r') as file:
            data = file.read()
            if data.strip():
                return json.loads(data)
            else:
                return {}
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Error decoding JSON file. The file may be empty or corrupted.")
        return {}
    

# when server is up we load all old saved scans so even if server shutdown fails user will still get his old scan results
# of course it also should be got from database
SCAN_RESULTS = load_saved_scans_from_file()



# Function to save scan results to the JSON file
def save_SCAN_RESULTS_to_file(scan):
    SCAN_RESULTS[scan['id']] = scan
    with open('saved_scans.json', 'w') as file:
        json.dump(SCAN_RESULTS, file)



@app.route('/scan', methods=['POST'])
def scan_domain():
    domain = request.json.get('domain')
    toolsArray = request.json.get('toolsArray')

    start_time = datetime.datetime.now()
    
    theHarvester_output = {}
    if 'theHarvester' in toolsArray:
        theHarvester_response = run_theHarvester(domain)
        theHarvester_output = parse_theHarvester_response(theHarvester_response)

    Amass_output = {}
    if 'Amass' in toolsArray:
        Amass_response = run_Amass(domain)
        Amass_output = parse_amass_results(Amass_response)


    combined_results = merge_maps(theHarvester_output, Amass_output)
    end_time = datetime.datetime.now()
    scan_id = str(uuid.uuid4())

    scan ={
        "id":scan_id,
        "domain":domain,
        "results": combined_results,
        "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S'),
        "toolsArray":toolsArray
    }

    SCAN_RESULTS[scan_id] = scan
    save_SCAN_RESULTS_to_file(scan)
    return jsonify(scan), 200


@app.route('/scan', methods=['GET'])
def get_scan():
    scan_ids = request.args.get('scan_ids')
    scan_ids_list = json.loads(scan_ids)
    relevant_scans = {}

    for scan_id in scan_ids_list:
        if scan_id in SCAN_RESULTS:
            relevant_scans[scan_id] = SCAN_RESULTS[scan_id]

    return jsonify(relevant_scans), 200


@app.route('/export/<scan_id>', methods=['GET'])
def export_to_excel(scan_id):

    if scan_id not in SCAN_RESULTS:
        return jsonify({"error": "Scan ID not found"}), 404

    scan_data = SCAN_RESULTS[scan_id]
    results = scan_data["results"]
    
    flattened_results = []
    for section, data in results.items():
        flattened_results.extend(data)
    
    df = pd.DataFrame({"Result": flattened_results})
    filename = f"{scan_id}_results.xlsx"
    df.to_excel(filename, index=False)
    
    try:
        return send_file(filename, as_attachment=True)
    finally:
        # Clean up the file after sending it to the user
        os.remove(filename)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000,debug=True)

