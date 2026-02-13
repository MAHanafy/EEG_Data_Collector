import numpy as np
import time
import fs
import pickle

_dir = fs.open_fs("./data")
files = []

for file in _dir.walk.files("./"):
    if file.endswith(".npz"):
        files.append(file)

if len(files) > 0:
    print("Files found in the current directory: ")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")
    print("Please select a file to simulate: ")
    file_index = int(input())
    file = files[file_index - 1]
    data = np.load(f"./data/{file}", allow_pickle=True)
    print(f"Data loaded from file: {file}")
    print(f"Data keys: {data.files}")
    key = input("Please select a key to simulate: ")
    if key in data:
        print(f"Simulating data for key: {key}")

        if key == "data":
            for a in data[key]:
                print(a)
                time.sleep(6/1000)
        else:
            print(pickle.loads(data[key]))
    else:
        print(f"Key {key} not found in data.")
