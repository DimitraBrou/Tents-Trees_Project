
import os
import numpy as np
from Solver import solve


results = []
def main():
    treeMap, topHints, leftHints = getInput()
    results = solve(treeMap, topHints, leftHints)
    print(len(results))    #
    print(results[4].message)

def getInput():
    print("Reading file")
    with open("input18.txt", 'r', encoding="utf-8") as file:
        file_content = file.read()

    file_content_strip = file_content.strip()
    data = file_content_strip.split()  # Split the content into individual elements

    row = int(data[0])
    column = int(data[1])
    print("row, column: ", row, column)

    stringTreeMap = np.empty((row,), dtype=object)
    topHints = np.empty(column, dtype=int)
    leftHints = np.empty(row, dtype=int)

    k = 2
    for i in range(row):
        stringTreeMap[i] = str(data[k])
        print(stringTreeMap[i])
        k += 1
        leftHints[i] = int(data[k])
        k += 1

    for i in range(column):
        topHints[i] = int(data[k])
        k += 1
    print("topHints :", topHints)
    print("leftHints :", leftHints)

    treeMap = np.zeros((row, column), dtype=int)
    for i in range(row):
        for j in range(column):
            if stringTreeMap[i][j] == '.':
                treeMap[i][j] = 0
            else:
                treeMap[i][j] = 1
    return treeMap, topHints, leftHints


if __name__ == '__main__':
    main()

