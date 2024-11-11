import argparse
from collections import defaultdict
import re

def generate_output_with_full_domain_name(input_file_path, output_file_path):
    # Initialize dictionaries for web groups and policies
    web_groups = defaultdict(lambda: {"domains": set(), "urls": set()})
    policies_dict = defaultdict(lambda: {"protocol": None, "environment": None, "port_ranges": set(), "web_group": None})
    sequential = 1

    # Read the input file
    with open(input_file_path, 'r') as file:
        lines = file.readlines()

    # Process each line for web groups and policies
    for line in lines:
        fields = line.strip().split(",")
        if len(fields) != 4:
            continue  # Skip lines that do not have exactly 4 fields

        domain = fields[0].strip()
        protocol = fields[1].strip().lower()
        port_range = fields[2].strip()
        environment = fields[3].strip()

        # Normalize the domain by removing "www." or "*." prefixes only
        if domain.startswith("www."):
            normalized_domain = domain[4:]
        elif domain.startswith("*."):
            normalized_domain = domain[2:]
        else:
            normalized_domain = domain

        # Construct the full sanitized group name using all parts of the domain
        sanitized_group_name = re.sub(r"[^a-zA-Z0-9]", "_", normalized_domain)

        # Categorize domains and URLs, creating separate web groups as needed
        if domain.startswith("*") and not domain.startswith("*."):
            web_groups[sanitized_group_name + "_u"]["urls"].add(domain)
            web_group_name = sanitized_group_name + "_u"
        else:
            web_groups[sanitized_group_name + "_d"]["domains"].add(domain)
            web_group_name = sanitized_group_name + "_d"

        # Consolidate policies by web group, protocol, and environment
        key = (web_group_name, protocol, environment)
        policies_dict[key]["protocol"] = protocol
        policies_dict[key]["environment"] = environment
        policies_dict[key]["web_group"] = web_group_name

        # Handle "All" or "Any" protocol cases
        if protocol in ["all", "any"]:
            policies_dict[key]["protocol"] = "Any"
        elif protocol != "icmp":
            # Add port range(s) if the protocol is not "icmp"
            if "-" in port_range:
                start, end = map(int, port_range.split("-"))
                for port in range(start, end + 1):
                    policies_dict[key]["port_ranges"].add(str(port))
            elif port_range.isdigit():
                policies_dict[key]["port_ranges"].add(port_range)

    # Write the output to the specified file
    with open(output_file_path, 'w') as file:
        # Write web groups
        file.write("web_groups = {\n")
        for group_name, values in web_groups.items():
            url_list = ", ".join(f'"{u}"' for u in sorted(values["urls"]))
            domain_list = ", ".join(f'"{d}"' for d in sorted(values["domains"]))
            file.write(f'  {group_name} = {{\n')
            file.write(f'    urls = [{url_list}]\n')
            file.write(f'    domains = [{domain_list}]\n')
            file.write("  }\n")
        file.write("}\n\n")

        # Write policies
        file.write("policies = {\n")
        for (web_group_name, protocol, environment), policy_data in policies_dict.items():
            is_url_based = len(web_groups[web_group_name]["urls"]) > 0
            decrypt_policy = "DECRYPT_ALLOWED" if is_url_based else ""
            port_ranges = ", ".join(sorted(policy_data["port_ranges"], key=int))

            policy_name = f"pol-{sequential}"
            file.write(f'  {policy_name} = {{\n')
            file.write('    action           = "PERMIT"\n')
            file.write(f'    priority         = "{sequential}"\n')
            file.write(f'    protocol         = "{policy_data["protocol"]}"\n')
            file.write('    logging          = "false"\n')
            file.write('    watch            = "false"\n')
            file.write(f'    src_smart_groups = ["{environment}"]\n')
            file.write('    dst_smart_groups = ["avtx_system_v4_wildcard_app_domain"]\n')
            if policy_data["protocol"] not in ["Any", "icmp"] and port_ranges:
                file.write(f'    port_ranges      = [{port_ranges}]\n')
            file.write(f'    web_groups       = ["{web_group_name}"]\n')
            file.write(f'    decrypt_policy   = "{decrypt_policy}"\n')
            file.write("  }\n")
            sequential += 1
        file.write("}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate web groups and policies output from an input file.")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("output_file", help="Path to the output file")
    args = parser.parse_args()

    # Call the function with the provided input and output file paths
    generate_output_with_full_domain_name(args.input_file, args.output_file)
