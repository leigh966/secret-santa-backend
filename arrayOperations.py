import random
def randomise_order(arr):
    output=[]
    while len(arr) > 0:
        index = random.randrange(0,len(arr))
        elem = arr.pop(index)
        output.append(elem)
    return output