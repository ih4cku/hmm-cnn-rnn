def read_table(pth):
    with open(pth) as f:
        lines = f.readlines()
        lines = [l.strip().split() for l in lines]
    return lines

def print_list(lst):
    for l in lst:
        print l

