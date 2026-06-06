# shared/services/grid_service.py
def build_coverage_cube(commits, files, buckets):
    cube = {}
    for commit in commits:
        per_file = {}
        for f in files:
            per_bucket = {}
            for b in buckets:
                hits = 0
                for line in f.lines_in_bucket(b):
                    if line.covered_at(commit):
                        hits += 1
                per_bucket[b] = hits
            per_file[f.path] = per_bucket
        cube[commit.sha] = per_file
    return cube
