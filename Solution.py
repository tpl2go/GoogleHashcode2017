import csv
import numpy as np
import cProfile

# IMPORT DATA FILE
kittenfile =  open('videos_worth_spreading.in')
kittenreader = csv.reader(kittenfile, delimiter=' ')

# VARIABLE DEFINITION
N_VIDEOS, N_ENDPOINTS, N_REQUESTS, N_CACHE, CACHE_CAP = map(int, kittenreader.next())

VID_SIZES = np.array(map(int,kittenreader.next()))

latency = np.zeros([N_ENDPOINTS,N_CACHE + 1],dtype=np.dtype(int))

for endpoint_id in xrange(N_ENDPOINTS):
    latency_to_main, num_cache = map(int,kittenreader.next())
    latency[endpoint_id,N_CACHE] = latency_to_main
    for cache_i in xrange(num_cache):
        cache_id, latency_to_cache = map (int, kittenreader.next())
        latency[endpoint_id,cache_id] = latency_to_cache

requests = np.zeros([N_VIDEOS,N_ENDPOINTS],dtype=np.dtype(int))

for req in kittenreader:
    vid_id, endpoint_id, num_req = map(int,req)
    requests[vid_id,endpoint_id] = num_req

route_status = (np.ones([N_VIDEOS,N_ENDPOINTS], dtype=int))*N_CACHE
storage_status = np.zeros([N_VIDEOS,N_CACHE+1],dtype=bool)
storage_status[:,-1] = 1
traffic_status = np.ones([N_VIDEOS,N_ENDPOINTS],dtype=int) * latency[:,-1]



def timesaved(endpoint_id,cache_id, num_vid = 1):
    maintime = latency[endpoint_id, N_CACHE].reshape([N_ENDPOINTS, N_CACHE + 1])
    time_taken = latency[endpoint_id, cache_id]
    if time_taken == 0:
        return 0
    return num_vid*(maintime - time_taken)

def contruct_endpoint_demand_saving(endpoint_id, cache_id):
    """ Returns a vector of time saved for every video
     should endpoint (E) fetch video from cache (C) instead of
     the endpoint's current best known source of a video """
    numberofvideorequested = (requests[:,endpoint_id])
    original = traffic_status[:,endpoint_id] * numberofvideorequested
    new = numberofvideorequested * latency[endpoint_id,cache_id]
    ts = original - new
    return ts

def construct_cache_value_2(cache_id):
    endpointsthatiwant = find_cache_children(cache_id)
    cache_vector = np.zeros(N_VIDEOS, dtype=int)
    for endpoint_id in endpointsthatiwant:
        cache_vector = cache_vector + contruct_endpoint_demand_saving(endpoint_id,cache_id)
    return cache_vector


def find_num_childendpts():
    raisehands = (latency!=0)
    return np.sum(raisehands, axis=0)[0:-1]

def find_cache_children(cache_id):
    (endpoint_ids, ) = np.nonzero(latency[:,cache_id])
    return endpoint_ids

def sort_cache_id():
    count = find_num_childendpts()
    return np.argsort(count)

def solve():
    sorted_cache_id = sort_cache_id()
    for i in xrange(N_CACHE):
	print str(i) + "/" + str(N_CACHE)
        cache_value = construct_cache_value_2(sorted_cache_id[i])
        #vid_ids = greedy(cache_value)
        vid_ids = knapsack2(cache_value) # knapsack may not be better than greedy in the long run
        storage_status[vid_ids, i] = True
        endpoint_idss = find_cache_children(i)
        updateRouteStatusandTrafficStatus(endpoint_idss,vid_ids)

def greedy(cache_value):

    videos_indices_increasing = np.argsort(cache_value)
    weight = 0
    index = -1
    vid_ids = []
    while True:
        vid_id= videos_indices_increasing[index]
        weight += VID_SIZES[vid_id]
        index -= 1
        if weight>CACHE_CAP:
            break
        vid_ids.append(vid_id)
    return vid_ids

def knapsack(cache_value):
    # main algo
    m = np.zeros([N_VIDEOS, CACHE_CAP + 1], dtype=int)
    trace = np.zeros([N_VIDEOS, CACHE_CAP + 1], dtype=bool)
    for i in xrange(0,N_VIDEOS):  # i : item id
        #print "knapsack item: " + str(i)
        for W in xrange(CACHE_CAP + 1):  # W : current weight capacity
            wi = VID_SIZES[i]  # wi : weight of ith item
            if wi > W:
                m[i, W] = m[i - 1, W] # devious trick here : when i = 0, m[0,w] is defined as 0. fortunately numpy's m[-1,w] fetches the last row which is all 0
            else:
                vi = cache_value[i]  # vi = value of ith item
                if m[i - 1, W] < vi + m[i - 1, W - wi]:
                    m[i, W] = vi + m[i - 1, W - wi]
                    trace[i, W] = True
                else:
                    m[i, W] = m[i - 1, W]
    output = getknapsackitems(trace)

    return output

def getknapsackitems(trace):
    output = []
    W = CACHE_CAP
    for i in xrange(N_VIDEOS-1, -1, -1):
        if trace[i, W]:
            output.append(i)
            W -= VID_SIZES[i]
    return output


def knapsack2(cache_value):
    # main algo
    m = np.zeros([N_VIDEOS, CACHE_CAP + 1], dtype=int)
    trace = np.zeros([N_VIDEOS, CACHE_CAP + 1], dtype=bool)
    for i in xrange(N_VIDEOS):  # i : item id
        #print "knapsack item: " + str(i)
        wi = VID_SIZES[i]
        vi = cache_value[i]
        W = np.arange(CACHE_CAP+1) >= wi
        Wshifted = np.pad(W,(0,wi),mode = 'constant')[wi:]
        a = vi + m[i - 1, Wshifted]
        b = m[i - 1, W]
        c = a>b
        right = CACHE_CAP + 1 - len(c) - wi
        Wselected = np.pad(c,(wi,0), mode = 'constant')
        m[i,Wselected] = a[c]
        trace[i, Wselected] = True
        Wunselected = np.logical_not(Wselected)    
        m[i, Wunselected] = m[i - 1, Wunselected]

    output = getknapsackitems(trace)
    return output


def updateRouteStatusandTrafficStatus(endpoint_ids,vid_ids):
    # given storage table and latency table, produce routing table
    # use during cache loading algorithm
    for endpoint_id in endpoint_ids:
        multiplier = (latency[endpoint_id,:])
        (indices, ) = np.nonzero(multiplier)
        vid_ids = np.array(vid_ids)
        A = storage_status[vid_ids[:,None],indices] * multiplier[indices]
        route = np.nanargmin(A,axis=1)
        route_status[vid_ids,endpoint_id] = indices[route]
        lats = latency[endpoint_id,indices[route]]
        traffic_status[vid_ids,endpoint_id] = lats



def outputanswer():
    # a = input("PRESS ANYBUTTON TO CONTINUE")
    NUM_SERVERS_USED = np.count_nonzero(np.sum(storage_status[:,:-1], axis=0))
    print NUM_SERVERS_USED
    for i in xrange(N_CACHE):
        A = storage_status[:,i]
        # print np.shape(A)
        (vid_id, ) = np.nonzero(A)
        #generate an array with strings
        x_arrstr = np.char.mod('%d', vid_id)
        #combine to a string
        x_str = str(i) + " " +  " ".join(x_arrstr)
        print x_str

def score_nocache():
    return np.sum(latency[:,-1] * np.sum(requests,axis=0))

def totalnumberofrequests():
    return np.sum(requests)

def calculate_score():
    total = 0
    for endpoint_id in xrange(N_ENDPOINTS):
        route_instructions = route_status[:,endpoint_id]
        latencies = latency[endpoint_id,route_instructions]
        total += np.sum(requests[:,endpoint_id]*latencies)
    return (score_nocache() - total) * 1000 / totalnumberofrequests()

cProfile.run('solve()')
#solve()
#print calculate_score()
#outputanswer()

