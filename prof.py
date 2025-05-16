import pstats

p = pstats.Stats("smoke_test.prof")
p.sort_stats("cumulative").print_stats(20)  # Show top 20 cumulative time consumers
p.sort_stats("tottime").print_stats(
    20
)  # Show top 20 total time consumers (in function itself)
