#!/bin/env python3

import sys
import time
from argparse import ArgumentParser, FileType
import dns.name
import dns.resolver
import socket
import concurrent.futures

# Our List of Domains to train on is too large, we also have some requirements for our model to work:
#   - The Domain needs to host a website
#   - The Site needs to be withing the realm of what we can use, - HTML, Text

# Filter Steps

'''
1. Verify the Domain is still current
2. Verify the Domain has a webserver on it. (check if port 80 or 443 is open)
3. ???

'''

TIMEOUT = 2


def verify_DNS(domain, nameserver):
    r = dns.resolver.Resolver()
    r.nameservers = [nameserver]
    r.timeout = TIMEOUT

    try: 
        answer = r.resolve(domain)
        return answer[0]
    except (dns.resolver.NXDOMAIN, dns.resolver.LifetimeTimeout, dns.resolver.NoAnswer) as e:
        return None
    except (dns.resolver.YXDOMAIN) as e:
        print(e)
        return None
    
def verify_port(domain) -> bool:

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)

    result = s.connect_ex((domain, 80))

    if result == 0:
        s.close()
        return True
    else:
        s.close()
        return False

# Returns a tuple with (bool, str)
# the bool states if the verifications was valid, the str states why it failed or conatins an exception message
def full_Verify(domain, ns):
    try:
        DNS_result = verify_DNS(domain, ns)
        if DNS_result is None:
            return (False, 'DNS')

        Port_result = verify_port(str(DNS_result))
        if not Port_result:
            return (False, 'PORT')

        return (True, DNS_result)

    except (Exception) as e:
        e.add_note(domain)
        return (False, e)


if __name__ == '__main__':

    parser = ArgumentParser(prog='Filter.py')
    parser.add_argument('blocklist', type=FileType('r'), help='The Block List file')
    parser.add_argument('outfile', type=FileType('w'))
    parser.add_argument('logfile', type=FileType('a'), default=sys.stdout)
    parser.add_argument('-ns', '--nameserver', type=str, default='1.1.1.1')
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-s', '--status', action='store_true', default=False)
    parser.add_argument('-dbug', '--debugMode', action='store_true', default=False)
    parser.add_argument('-tMax', '--threadMax', default=1, type=int, help='The maaximum number of threads to run concurrently')
    args = parser.parse_args()

    # to be used for easy performance tuning
    MULTIPLIER = 4

    ns = args.nameserver
    batchSize = MULTIPLIER*args.threadMax
    to = 2  # int(args.threadMax/16 + 1)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=args.threadMax)
    
    if args.verbose or args.status:
        print(f'Will use up to {executor._max_workers} threads')
        print(f'Using a batch size of {batchSize}')
        print(f'Timeout is {to} seconds')

    future_list = {}
    domainCount = 0
    errorCount = 0
    validCount = 0
    completeCount = 0

    start = time.time()

    while args.blocklist.readable():
        
        # Submit tasks in batches, while keeping the ram usage down
        if domainCount - completeCount < batchSize * MULTIPLIER:
            for i in range(0, batchSize):
                # Verify we have not read the entire file
                if not args.blocklist.readable():
                    break

                domain = args.blocklist.readline().strip()
                future_list[executor.submit(full_Verify, domain, ns)] = domain
                domainCount += 1

                if args.status:
                    sys.stdout.write(f'\rTotal {domainCount}, Completed {completeCount}, Queued {domainCount-completeCount}, {int(completeCount / (time.time() - start))} tps, {time.time() - start:.3f} seconds elapsed')
                    sys.stdout.flush()
        
        try:
            for future in concurrent.futures.as_completed(future_list, to):
                domain = future_list[future]
                try:
                    data = future.result()
                    status, info = data

                    if True == status:
                        validCount += 1
                        args.outfile.write(domain + '\n')
                        args.logfile.write(f'{domain} was successful. IP: {info}\n')
                    else:
                        args.logfile.write(f'{domain} failed, Info: {info}\n')           
                except Exception as e:
                    print(e)
                    args.logfile.write(f'{domain} experienced an Error\n')
                    errorCount += 1
                
                del future_list[future]
                completeCount += 1
                if args.status:
                    sys.stdout.write(f'\rTotal {domainCount}, Completed {completeCount}, Queued {domainCount-completeCount}, {int(completeCount / (time.time() - start))} tps, {time.time() - start:.3f} seconds elapsed')
                    sys.stdout.flush()

        except TimeoutError as e:
            pass

    print(f'Attempted {domainCount} Domains')
    print(f'Encountered {errorCount} Errors\n')
    print(f'Found {validCount} valid Entries\n')
    print(f'In {time.time() - start} seconds\n')