#!/bin/env python3

# I keep getting rate limited . . .


import dns.name
import dns.resolver
import concurrent.futures
import time

def resolve_worker(count:int, domain: str, ns: str):
    r = dns.resolver.Resolver()
    r.nameservers = ns

    for i in range(0, count):
        r.resolve(domain)
    
    return 'Done'

# Config Items
nameServer = ['10.200.24.4']
domain = "home.theRealDealPeel.com"
TotalRequestCount = 10000
NodeCount = 100
requestsPerNode = int(TotalRequestCount/NodeCount)



print(f'Total Requests: {TotalRequestCount}')
print(f'Total Nodes: {NodeCount}')
print(f'Requests/Node: {requestsPerNode}')

ex = concurrent.futures.ThreadPoolExecutor(max_workers=NodeCount)

workers = list()

start = time.time()

for i in range(0, NodeCount):
    workers.append(ex.submit(resolve_worker, requestsPerNode, domain, nameServer))

for future in concurrent.futures.as_completed(workers, timeout=30):
    data = future.result()


print(f'Time to Complete {TotalRequestCount} requests is {time.time() - start:.5f} Seconds')







