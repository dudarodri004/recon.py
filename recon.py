import subprocess
import os

# Utility function to run a shell command and print output in real-time
def run_command(command, description):
    print(f"[INFO] {description}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Print stdout and stderr line by line
    for stdout_line in iter(process.stdout.readline, ""):
        print(stdout_line, end="")  # Print stdout
    for stderr_line in iter(process.stderr.readline, ""):
        print(stderr_line, end="")  # Print stderr
    
    process.stdout.close()
    process.stderr.close()
    return_code = process.wait()
    
    if return_code != 0:
        print(f"[ERROR] Command '{command}' failed with return code {return_code}\n")
    else:
        print(f"[INFO] Command '{command}' executed successfully\n")
    
    return return_code

def main(domain):
    # Create a directory for storing results
    os.makedirs(domain, exist_ok=True)
    
    # Step 1: Subdomain Enumeration with amass (Free APIs)
    amass_output = f"{domain}/amass.txt"
    run_command(f"amass enum -passive -d {domain} -o {amass_output}", "Running amass for subdomain enumeration")
    
    # Step 2: Subdomain Enumeration using SecurityTrails
    securitytrails_output = f"{domain}/securitytrails.txt"
    run_command(f"curl --request GET 'https://api.securitytrails.com/v1/domain/{domain}/subdomains' --header 'apikey: 5TWkBXVdf-1JO9JbiiLB0kSaOJGi6-D9' | jq -r '.subdomains[]' > {securitytrails_output}", "Fetching subdomains from SecurityTrails")
    
    # Combine results from amass and SecurityTrails using anew
    combined_subdomains = f"{domain}/combined_subdomains.txt"
    run_command(f"cat {amass_output} {securitytrails_output} | anew {combined_subdomains}", "Combining subdomains from amass and SecurityTrails using anew")

    # Step 3: Subdomain Permutations with ripgen
    ripgen_output = f"{domain}/ripgen.txt"
    run_command(f"ripgen -d {combined_subdomains} > {ripgen_output}", "Running ripgen for subdomain permutations")
    
    # Combine all subdomain results using anew
    all_subdomains = f"{domain}/all_subdomains.txt"
    run_command(f"cat {ripgen_output} | anew {all_subdomains}", "Combining all subdomains using anew")

    # Step 4: Grab A records with dnsx
    dnsx_output = f"{domain}/dnsx_output.txt"
    run_command(f"cat {all_subdomains} | dnsx -a -resp-only -o {dnsx_output}", "Running dnsx to grab A records")
    
    # Step 5: Remove IPs pointing to CDNs
    non_cdn_ips = f"{domain}/non_cdn_ips.txt"
    cdn_ips = ["104.16.", "104.17.", "151.101."]  # Extend this list with more CDN ranges
    with open(dnsx_output, 'r') as f:
        with open(non_cdn_ips, 'w') as nf:
            for line in f:
                if not any(cdn_ip in line for cdn_ip in cdn_ips):
                    nf.write(line)
    
    # Step 6: Scan non-CDN IPs with Nmap
    nmap_output = f"{domain}/nmap_scan.txt"
    run_command(f"nmap -iL {non_cdn_ips} -oN {nmap_output}", "Running Nmap scan on non-CDN IPs")

    # Step 7: Use httpx to grab HTTP metadata and location data
    httpx_output = f"{domain}/httpx_output.txt"
    run_command(f"cat {all_subdomains} | httpx -title -tech-detect -status-code -location -o {httpx_output}", "Running httpx to grab HTTP metadata and location data")
    
    # Step 8: Run nuclei on all gathered data
    nuclei_output = f"{domain}/nuclei_output.txt"
    run_command(f"nuclei -l {all_subdomains} -o {nuclei_output}", "Running nuclei on all gathered data")

if __name__ == "__main__":
    target_domain = input("Enter the target domain: ")
    main(target_domain)