# GOOGLE HASHCODE 2017

## Idea
1. Sort caches in increasing order of the number child endpoints each have
2. Start with cache C_i. 
3. For each of its child endpoint, compute the "Time Saved Score" should the cache serve video V_i to the endpoint.
4. Sum all "Time Saved Score" for each video across child endpoints into a "value vector"
5. Together with the "video weight" vector, cache will decide which videos to store to maximise total "Time Saved Score"
6. After deciding on which videos to store, update the "routing table" and "traffic status" table 
7. Move on to next cache and repeat

Credits: Tinaesh

## Notes
*Two ways to for a cache to decide on videos based on the weight vector and value vector: A greedy algorithm and a dynamic programming algorithm
*While dynamic programming algorithm gives the most optimal solution for a single cache. When applied to all caches in the order we have specified, it may not produce the best solution

## Score
|Input| Score|
|----|----|
| Kittens|760783|
|Me at the Zoo|336681|
|Trending today|499565
|Videos worth spreading|315041|
