
import os

path1 = "out_2/harmony/0.25"

path2 = "out_2/harmony/0.5"

path3 = "out_2/harmony/0.75"

path4 = "out_2/harmony/1"

path5 = "out_2/harmony/1.5"

path6 = "out_2/harmony/2"


D = {}

D[1]  = set(os.listdir(path1))

D[2] = set(os.listdir(path2))

D[3] = set(os.listdir(path3))

D[4] = set(os.listdir(path4))

D[5] = set(os.listdir(path5))

D[6] = set(os.listdir(path6))

for i in range(1,7):
    for j in range(1,7):
        
        set1 = D[i]
        set2 = D[j]
        print str(i) + "-" + str(j)

        print set1 - set2
	print
