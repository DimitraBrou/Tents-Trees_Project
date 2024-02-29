import os
import numpy as np

_undef = object()
const_cellType_notTested = 0
const_cellType_tent = 1
const_cellType_uncertain = 2
const_cellType_grass = 3
const_cellType_tree = 4

class Cell:
    def __init__(self, row, column):
        self._type = CellType.notTested
        self._row = row
        self._column = column

    @property
    def row(self):
        return self._row

    @property
    def column(self):
        return self._column

    @property
    def type(self):
        return self._type

    @property
    def isTree(self):
        return self._type == CellType.tree

    @property
    def isSet(self):
        return self._type == CellType.tree or self._type == CellType.grass or self._type == CellType.tent

    @property
    def isNotSet(self):
        return self._type == CellType.uncertain or self._type == CellType.notTested

    @property
    def isTent(self):
        return self._type == CellType.tent

    @property
    def isDefinitelyNotTent(self):
        return self._type == CellType.tree or self._type == CellType.grass

    def setType(self, type):
        if self.isNotSet:
            self._type = type
        else:
            raise NameError(
                "Cannot change type from " + CellType.convertToString(self._type) + " to " + CellType.convertToString(
                    type))

    def forceSetType(self, type):
        self._type = type

    def trySetType(self, type):
        if self.isNotSet:
            self._type = type
            return True
        return False


class CellType:
    # using property decorator
    # a getter function
    @property
    def notTested(self):
        return const_cellType_notTested

    @property
    def tent(self):
        return const_cellType_tent

    @property
    def uncertain(self):
        return const_cellType_uncertain

    @property
    def grass(self):
        return const_cellType_grass

    @property
    def tree(self):
        return const_cellType_tree

    @staticmethod
    def convertToString(type: any) -> str:
        match type:
            case 0:
                return "not-tested"
            case 1:
                return "tent"
            case 2:
                return "uncertain"
            case 3:
                return "grass"
            case 4:
                return "tree"


class MapSnapshot:
    def __init__(self, changedCells, map, isValid, isSolved, message):
        self._changeCells = changedCells
        self._map = None if (map is None) or (map is _undef) else DeepCopyMap(map)
        # print("MapSnapshot -> ", self._map.shape)
        self._isValid = isValid
        self._isSolved = isSolved
        self._message = message

    @property
    def changeCells(self):
        return self._changeCells

    @property
    def map(self):
        return self._map

    @property
    def isValid(self):
        return self._isValid

    @property
    def isSolved(self):
        return self._isSolved

    @property
    def message(self):
        return self._message

def DeepCopyMap(tentMap):
    (rowCount, columnCount) = tentMap.shape
    newMap = np.empty((rowCount, columnCount), dtype=object)
    for row in range(rowCount):
        for column in range(columnCount):
            newMap[row][column] = Cell(row, column)
            newMap[row][column].setType(tentMap[row][column].type)
    return newMap

def checkIsValid(tentMap, topHints, leftHints):
    (rowCount, columnCount) = tentMap.shape
    # print("checkIsValid", rowCount, columnCount)
    rowTentCounts = np.zeros((columnCount, ), dtype=int)
    for row in range(rowCount):
        colTentCount = 0
        for column in range(columnCount):
            if tentMap[row][column].isTent:
                colTentCount += 1
                rowTentCounts[column] += 1
        if colTentCount + leftHints[row] > columnCount:
            return (False, "row" + row + " is invalid")
    for column in range(columnCount):
        if rowTentCounts[column] + topHints[column] > rowCount:
            return (False, "col" + column + " is invalid")
    totalTopHints = np.sum(topHints)
    totalLeftHints = np.sum(leftHints)

    if totalTopHints != totalLeftHints:
        return (False, "total tents hint (top) must be equal to total tents hint(left)")
    return (True, "")

def stringify(tentMap):
    result = ""
    (rowCount, columnCount) = tentMap.shape
    # print("Here stringify", tentMap.shape)
    for row in range(rowCount):
        for column in range(columnCount):
            text = ""
            match tentMap[row][column].type:
                case CellType.notTested:
                    text = "_"
                case CellType.tent:
                    text = "▲"
                case CellType.uncertain:
                    text = "?"
                case CellType.grass:
                    text = "□"
                case CellType.tree:
                    text = "T"
            result += text
        result += "\n"
    return result


def toHtml(tentMap):
    result = stringify(tentMap).replace("\n", "<br>")
    # print("toHtml-> ", result)
    return "<div class='text-map'>" + result + "</div>"

def RemoveZeroColumnRow(tentMap, topHints, leftHints): #well done
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        if not leftHints[row]:
            for column in range(columnCount):
                isChanged |= tentMap[row][column].trySetType(CellType.grass)

    for column in range(columnCount):
        if not topHints[column]:
            for row in range(rowCount):
                isChanged |= tentMap[row][column].trySetType(CellType.grass)
    return isChanged

def checkIsSolved(tentMap, topHoints, leftHints):
    (rowCount, columnCount) = tentMap.shape
    rowTentCounts = np.zeros((columnCount, ), dtype=int)
    rowNotSetCounts = np.zeros((columnCount, ), dtype=int)

    for row in range(rowCount):
        columnTentCount = 0
        columnNotSetCount = 0
        for column in range(columnCount):
            cell = tentMap[row][column]
            if cell.isTent:
                columnTentCount += 1
                rowTentCounts[column] += 1
            elif cell.isNotSet:
                columnNotSetCount += 1
                rowNotSetCounts[column] += 1
        if columnTentCount != leftHints[row]:
            return False
        if columnNotSetCount > 0:
            return False
    for column in range(columnCount):
        if rowTentCounts[column] != topHoints[column]:
            return False
        if rowNotSetCounts[column]:
            return False
    return True



def logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, description): # Record tentmap changes in the results
    # print("Here logStatus")
    (isValid, errorMessage) = checkIsValid(tentMap, topHints, leftHints)
    if not isValid:
        snapshot = MapSnapshot(None, None, False, False, "<br>error: " + errorMessage)
        result.append(snapshot)
        return (prevState, stepCount, False, True)
    isSolved = checkIsSolved(tentMap, topHints, leftHints)
    currentState = toHtml(tentMap)

    if prevState != currentState:
        snapshot = MapSnapshot(None, tentMap, False, isSolved, description)

        result.append(snapshot)
        if isSolved:
            return (prevState, stepCount, False, True)
        stepCount += 1
        prevState = currentState
        return (prevState, stepCount, True, False)
    return (prevState, stepCount, False, False)

def DeepCopyArray(arr): # function that copy arr array to newArr, not same address
    newArr = np.copy(arr)
    return newArr

def CopySetCells(map, copyFrom): # copy copyFrom to map so map address is not same copyFrom
    (rowCount, columnCount) = map.shape
    for row in range(rowCount):
        for column in range(columnCount):
            fromCell = copyFrom[row][column]
            cell = map[row][column]
            if cell.isNotSet and fromCell.isSet:
                cell.setType(fromCell.type)

def SetGrassAroundTent(tentMap): # Set notSet cells around tent to grass, in Up, down, left, right 
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        for column in range(columnCount):
            if tentMap[row][column].isTent:
                lastRow = row - 1
                if lastRow >= 0:
                    isChanged |= tentMap[lastRow][column].trySetType(CellType.grass)
                nextRow = row + 1
                if nextRow < rowCount:
                    isChanged |= tentMap[nextRow][column].trySetType(CellType.grass)

                lastColumn = column - 1
                if lastColumn >= 0:
                    isChanged |= tentMap[row][lastColumn].trySetType(CellType.grass)
                    if lastRow >= 0:
                        isChanged |= tentMap[lastRow][lastColumn].trySetType(CellType.grass)
                    if nextRow < rowCount:
                        isChanged |= tentMap[nextRow][lastColumn].trySetType(CellType.grass)
                nextColumn = column + 1
                if nextColumn < columnCount:
                    isChanged |= tentMap[row][nextColumn].trySetType(CellType.grass)
                    if lastRow >= 0:
                        isChanged |= tentMap[lastRow][nextColumn].trySetType(CellType.grass)
                    if nextRow < rowCount:
                        isChanged |= tentMap[nextRow][nextColumn].trySetType(CellType.grass)
    return isChanged
def GetCellsAround(map, row, lastRow, nextRow, column, rowCount, columnCount): # Get Cells Around present Cell
    lastColumn = column - 1
    nextColumn = column + 1
    topCell = _undef
    bottomCell = _undef
    leftCell = _undef
    rightCell = _undef

    if lastRow >= 0:
        topCell = map[lastRow][column]
    if nextRow < rowCount:
        bottomCell = map[nextRow][column]
    if lastColumn >= 0:
        leftCell = map[row][lastColumn]
    if nextColumn < columnCount:
        rightCell = map[row][nextColumn]
    return (topCell, leftCell, rightCell, bottomCell)

def TryIsTentOrNotSet(cell): #Identify if that cell is tent or notSet, returning True if it is, and False otherwise.
    if (cell != _undef) and (cell != None):
        return cell.isTent or cell.isNotSet
    return False
def TryIsTree(cell): #Identify if that cell is tree, returning True if it is, and False otherwise.
    if (cell != _undef) and (cell != None):
        return cell.isTree
    return False
def RemoveAssociatedTreesAndTents(map, topHints, leftHints): #Remove newly identified trees and tents from the test map to show which tents each tree is associated with.
    isRemoved = False
    (rowCount, columnCount) = map.shape
    
    for row in range(rowCount):
        lastRow = row - 1
        nextRow = row + 1
        for column in range(columnCount):
            cell = map[row][column]
            if cell.isTree:
                # print("remove Cell Tree-> ", cell.row, cell.column)
                (topCell, leftCell, rightCell, bottomCell) = GetCellsAround(map, row, lastRow, nextRow, column, rowCount, columnCount)
                tentCount = TryIsTentOrNotSet(topCell) + TryIsTentOrNotSet(leftCell) + TryIsTentOrNotSet(rightCell) + TryIsTentOrNotSet(bottomCell)
                # print("remove tentCount", tentCount)
                if tentCount == 1:

                    tentCell = next((cell for cell in [topCell, leftCell, rightCell, bottomCell] if TryIsTentOrNotSet(cell)), None)
                    if tentCell.isTent:
                        cell.forceSetType(CellType.grass)
                        tentCell.forceSetType(CellType.grass)
                        topHints[tentCell.column] -= 1
                        leftHints[tentCell.row] -= 1
                        isRemoved = True
            elif cell.isTent:
                # print("remove Cell Tent-> ", cell.row, cell.column)
                (topCell, leftCell, rightCell, bottomCell) = GetCellsAround(map, row, lastRow, nextRow, column, rowCount, columnCount)
                treeCount = TryIsTree(topCell) + TryIsTree(leftCell) + TryIsTree(rightCell) + TryIsTree(bottomCell)
                # print("remove treeCount", treeCount)
                if treeCount == 1:
                    treeCell = next((cell for cell in [topCell, leftCell, rightCell, bottomCell] if TryIsTree(cell)), None)
                    if treeCell.isTree:
                        cell.forceSetType(CellType.grass)
                        treeCell.forceSetType(CellType.grass)
                        topHints[cell.column] -= 1
                        leftHints[cell.row] -= 1
                        isRemoved = True

    return isRemoved

def seePresentState(tentMap): # This function aims to see the current state of the tentMap.
    (rowCount, columnCount) = tentMap.shape
    result = ""
    for row in range(rowCount):
        text=""
        for column in range(columnCount):
            cell = tentMap[row][column]
            match tentMap[row][column].type:
                case CellType.notTested:
                    text += "_"
                case CellType.tent:
                    text += "▲"
                case CellType.uncertain:
                    text += "?"
                case CellType.grass:
                    text += "□"
                case CellType.tree:
                    text += "T"
        result += text + "    " + str(row+1) + "\n"
    print(result)
def excludeLand(tentMap): # Remove any cells that don't have a tree around them.
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        for column in range(columnCount):
            if not tentMap[row][column].isNotSet: # only pass isNotSet
                continue
            lastRow = row - 1
            lastColumn = column - 1
            nextRow = row + 1
            nextColumn = column + 1
            noTopTree = True
            noLeftTree = True
            if lastRow >= 0:
                noTopTree = not tentMap[lastRow][column].isTree
            if lastColumn >= 0:
                noLeftTree = not tentMap[row][lastColumn].isTree
            noBottomTree = True
            noRightTree = True
            if nextRow < rowCount:
                noBottomTree = not tentMap[nextRow][column].isTree
            if nextColumn < columnCount:
                noRightTree = not tentMap[row][nextColumn].isTree

            #idendify if this cell can set to grass because there is not tree around
            if (noTopTree and noLeftTree and noBottomTree and noRightTree):
                # print("cell that can to grass -> ", row, column)
                tentMap[row][column].setType(CellType.grass)
                isChanged = True
    return isChanged

def GroupAdjacentNumbers(arr): # Combine adjacent indices into the same array

    len_arr = len(arr)
    if len_arr == 0:
        return ()
    last = arr[0]
    result = [
       [last]
    ]
    # result += ([last], )
    for i in range(1, len_arr):
        current = arr[i]
        if current == last + 1:
            result[len(result) - 1].append(current)
        else:
            result.append([current])
        last = current
    return result

def CountDiscontinousCells(arr): #[[1, 2, 3], [5, 6], [7]] => 4 this caculate how many tent can exist on this row
    count = 0
    for i in range(len(arr)):
        count += (len(arr[i]) + 1) >> 1
    return count

def PlaceOnesAndThreesTents(rowCount, rowEmptyCells, leftHints, isNotSet, setType):
    isChanged = False
    for row in range(rowCount):
        if leftHints[row] == 0:
            continue
        emptyCell = rowEmptyCells[row]
        discontinousCellsCount = CountDiscontinousCells(emptyCell)
        if discontinousCellsCount < leftHints[row]:
            diff = (leftHints[row] - discontinousCellsCount + 1) >> 1
            threes = 0
            largerThanThree = 0
            for i in range(len(emptyCell)):
                emptyCellLength = len(emptyCell[i])
                if emptyCellLength == 3:
                    threes += 1
                elif emptyCellLength > 3:
                    largerThanThree += 1
            if largerThanThree == 0 and threes == diff:
                for i in range(len(emptyCell)):
                    cells = emptyCell[0]
                    if len(cells) == 1 and isNotSet(row, cells[0]):
                        setType(row, cells[i])
                        isChanged = True
                    if len(cells) == 3 and isNotSet(row, cells[0]) and isNotSet(row, cells[1]) and isNotSet(row, cells[2]):
                        setType(row, cells[0])
                        setType(row, cells[2])

                        isChanged = True
        elif discontinousCellsCount == leftHints[row]:
            largerThanTwo = next((e for e in emptyCell if len(e) > 2), None)
            if (largerThanTwo == _undef or largerThanTwo == None):
                for i in range(len(emptyCell)):
                    cells = emptyCell[0]
                    if len(cells) == 1 and isNotSet(row, cells[0]):
                        setType(row, cells[0])
                        isChanged = True
    return isChanged
def GetEmptyCells(tentMap): #Get array of combined indexed arrays
    (rowCount, columnCount) = tentMap.shape
    rowEmptyCells = np.empty((rowCount, ), dtype=object)
    localColumnEmptyCells = np.empty((columnCount, ), dtype=object)
    columnEmptyCells = np.empty((columnCount, ), dtype=object)

    for column in range(columnCount):
        localColumnEmptyCells[column] = np.array([], dtype=int)
    for row in range(rowCount):
        localRowEmptyCells = np.array([], dtype=int)
        for column in range(columnCount):
            cell = tentMap[row][column]
            if cell.isNotSet or cell.isTent:
                localRowEmptyCells = np.append(localRowEmptyCells, column)
                localColumnEmptyCells[column] = np.append(localColumnEmptyCells[column], row)
        rowEmptyCells[row] = GroupAdjacentNumbers(localRowEmptyCells)

    for column in range(columnCount):
        # print("localColunEmptyCells[column] -> ", columnEmptyCells[column])
        columnEmptyCells[column] = GroupAdjacentNumbers(localColumnEmptyCells[column])
    return (rowEmptyCells, columnEmptyCells)
def PlaceExplicitTents(tentMap, topHints, leftHints):
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    topUnknownTents = np.zeros((columnCount, ), dtype=int)
    leftUnknownTents = np.zeros((columnCount, ), dtype=int)
    topKnownTents = np.zeros((columnCount,), dtype=int)
    leftKnownTents = np.zeros((columnCount,), dtype=int)

    for row in range(rowCount):
        for column in range(columnCount):
            cell = tentMap[row][column]
            if cell.isNotSet:
                topUnknownTents[column] += 1
                leftUnknownTents[row] += 1
            elif cell.isTent:
                topKnownTents[column] += 1
                leftKnownTents[row] += 1
    for row in range(rowCount):
        if leftUnknownTents[row] == 0:
            continue
        if (leftKnownTents[row] + leftUnknownTents[row] == leftHints[row]):
            for column in range(columnCount):
                cell = tentMap[row][column]
                if cell.isNotSet:
                    tentMap[row][column].setType(CellType.tent)
                    isChanged = True
                    topUnknownTents[column] -= 1
                    topKnownTents[column] += 1
    for column in range(columnCount):
        if topUnknownTents[column] == 0:
            continue
        if (topKnownTents[column] + topUnknownTents[column] == topHints[column]):
            for row in range(rowCount):
                cell = tentMap[row][column]
                isChanged |= cell.trySetType(CellType.tent)
    # print("placeExplicitTents->")
    # seePresentState(tentMap)
    (rowEmptyCells, columnEmptyCell) = GetEmptyCells(tentMap)
    # print("rowEmptyCells -> ")
    # print(rowEmptyCells)

    isChanged |= PlaceOnesAndThreesTents(rowCount, rowEmptyCells, leftHints,
                    lambda r, c: tentMap[r][c].isNotSet,
                    lambda r, c: tentMap[r][c].setType(CellType.tent))
    # print("-------row direct placeOneAndThreesTens ----->")
    # seePresentState(tentMap)
    isChanged |= PlaceOnesAndThreesTents(columnCount, columnEmptyCell, topHints,
                    lambda c, r: tentMap[r][c].isNotSet,
                    lambda c, r: tentMap[r][c].setType(CellType.tent))
    # print("-------column direct placeOneAndThreesTens ----->")
    # seePresentState(tentMap)
    return isChanged

def PlaceTentNextToIsolatedsTree(tentMap):
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        for column in range(columnCount):
            if tentMap[row][column].isTree:
                coordinate = hasOnlyOneUnKnownCell(tentMap, row, column)
                if coordinate is not _undef and coordinate is not None:
                    print([row, column], coordinate)
                    isChanged |= tentMap[coordinate[0]][coordinate[1]].trySetType(CellType.tent)
    return isChanged

def hasOnlyOneUnKnownCell(tentMap, row, column): # Make sure there is only one isNotSet space around this tree.
    (rowCount, columnCount) = tentMap.shape
    isTopNotTent = row <= 0 or ( row > 0 and tentMap[row - 1][column].isDefinitelyNotTent)
    isBottomNotTent = row >= rowCount - 1 or (row < rowCount - 1 and tentMap[row + 1][column].isDefinitelyNotTent)
    isLeftNotTent = column <= 0 or  (column > 0 and tentMap[row][column - 1].isDefinitelyNotTent)
    isRightNotTent = column >= columnCount - 1 or (column < columnCount - 1 and tentMap[row][column + 1].isDefinitelyNotTent)
    coordinate = None
    if not isTopNotTent:
        coordinate = [row - 1, column]
    if not isBottomNotTent:
        coordinate = [row + 1, column]
    if not isLeftNotTent:
        coordinate = [row, column - 1]
    if not isRightNotTent:
        coordinate = [row, column + 1]
    if (isTopNotTent + isRightNotTent + isLeftNotTent + isBottomNotTent == 3):
        return coordinate
    return None


def PlaceDeducedTents(tentMap, topHints, leftHints):
    # [0, 3, 0, 0] and hint is 2, then 1 st cell must be a tent
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    (rowEmptyCells, columnEmptyCells) = GetEmptyCells(tentMap)
    for row in range(rowCount):
        rowEmptyCell = rowEmptyCells[row]
        if CountDiscontinousCells(rowEmptyCell) == leftHints[row]:
            for i in range(len(rowEmptyCell)):
                cells = rowEmptyCell[i]
                if (len(cells) & 1) == 1:
                    for j in range(0, len(cells), 2):
                        if not tentMap[row][cells[j]].isTent:
                            tentMap[row][cells[j]].setType(CellType.tent)
                            isChanged = True
    for column in range(columnCount):
        columnEmptyCell = columnEmptyCells[column]
        if CountDiscontinousCells(columnEmptyCell) == topHints[column]:
            for i in range(len(columnEmptyCell)):
                cells = columnEmptyCell[i]
                if (len(cells) & 1) == 1:
                    for j in range(0, len(cells), 2):
                        if not tentMap[cells[j]][column].isTent:
                            tentMap[cells[j]][column].setType(CellType.tent)
                            isChanged = True
    return isChanged

def ExcludeFullyFilledLine(tentMap, topHints, leftHints):
    # (2) 1 T 1 0 <- the last cell must be grass
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        notSetCount = 0
        tentCount = 0
        for column in range(columnCount):
            cell = tentMap[row][column]
            if cell.isTent:
                tentCount += 1
            elif cell.isNotSet:
                notSetCount += 1
        if tentCount == leftHints[row] and notSetCount > 0:
            for column in range(columnCount):
                isChanged |= tentMap[row][column].trySetType(CellType.grass)
    for column in range(columnCount):
        notSetCount = 0
        tentCount = 0
        for row in range(rowCount):
            cell = tentMap[row][column]
            if cell.isTent:
                tentCount += 1
            elif cell.isNotSet:
                notSetCount += 1
        if tentCount == topHints[column] and notSetCount > 0:
            for row in range(rowCount):
                isChanged |= tentMap[row][column].trySetType(CellType.grass)
    return isChanged

def ExcludeDiagonallyJointCell(tentMap, topHints, leftHints):
    # (2) 0 T 0 0
    #     0 0 0 0 <- 2nd must be grass
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    (rowEmptyCells, columnEmptyCells) = GetEmptyCells(tentMap)
    # print(rowEmptyCells)
    # print(columnEmptyCells)
    print("row")
    for row in range(rowCount):
        if leftHints[row] == 0:
            continue
        isChanged |= ExcludeDiagonallyJointCellsInline(rowEmptyCells, leftHints, row, rowCount,
             lambda r, c: tentMap[r][c].isNotSet,
             lambda r, c: tentMap[r][c].trySetType(CellType.grass),
        )
    print("column")
    for column in range(columnCount):
        if leftHints[column] == 0:
            continue
        isChanged |= ExcludeDiagonallyJointCellsInline(columnEmptyCells, topHints, column, columnCount,
             lambda c, r: tentMap[r][c].isNotSet,
             lambda c, r: tentMap[r][c].trySetType(CellType.grass),
        )
    # print("diagonally result -> ", isChanged)
    return isChanged

def ExcludeAlignedCellsInline(emptyCell, row, rowCount, isNotSet, trySetType):
    isChanged = False
    lastRow = row - 1
    nextRow = row + 1
    if len(emptyCell) == 0:
        return isChanged
    lastCells = emptyCell[0]
    # print("ExcludeAlignedCellsInline -> ", emptyCell)
    for i in range(1, len(emptyCell)):
        cells = emptyCell[i]
        if len(cells) == 2 and isNotSet(row, cells[0]) and isNotSet(row, cells[1]):
            # * (1) 0 0
            # *     0 T <- 1st
            if lastRow >= 0:
                isChanged |= trySetType(lastRow, cells[0])
                isChanged |= trySetType(lastRow, cells[1])
            elif nextRow < rowCount:
                isChanged |= trySetType(nextRow, cells[0])
                isChanged |= trySetType(nextRow, cells[1])
        elif len(cells) == 3 and isNotSet(row, cells[0]) and isNotSet(row, cells[1]) and isNotSet(row, cells[2]):
            # * (1) 0 0 0
            #       T 0 T <- 2nd
            if lastRow >= 0:
                isChanged |= trySetType(lastRow, cells[1])
            elif nextRow < rowCount:
                trySetType(nextRow, cells[1])
        elif len(lastCells) == 1 and len(cells) == 3 and cells[0] == lastCells[0] + 2:
            #*(2) 0 T 0 0 0
            #     T 0 T T T <-2nd
            if isNotSet(row, cells[0]) and isNotSet(row, cells[1]) and isNotSet(row, cells[2]) and isNotSet(row, lastCells[0]):
                if lastRow >=0:
                    isChanged |= trySetType(lastRow, lastCells[0] + 1)
                if nextRow < rowCount:
                    isChanged |= trySetType(nextRow, lastCells[0] + 1)
        elif len(lastCells) == 3 and len(cells) == 1 and cells[0] == lastCells[2] + 2:
            #*(2) 0 0 0 T 0
            #     T T T 0 T
            if isNotSet(row,cells[0] and isNotSet(row, lastCells[1])) and isNotSet(row, lastCells[2]) and isNotSet(row, lastCells[0]):
                if lastRow >= 0:
                    isChanged |= trySetType(lastRow, lastCells[0] - 1)
                if nextRow < rowCount:
                    isChanged |= trySetType(lastRow, cells[0] - 1)
        if i >= 1:
            lastCells = cells
    return isChanged


def ExcludeDiagonallyJointCellsInline(emptyCells, hints, row, rowCount, isNotSet, trySetType):
    isChanged = False
    emptyCell = emptyCells[row]
    discontinuousCellsCount = CountDiscontinousCells(emptyCell)
    # print("i -> discount", row,  discontinuousCellsCount)
    if discontinuousCellsCount == hints[row]:
        isChanged |= ExcludeAlignedCellsInline(emptyCell, row, rowCount, isNotSet, trySetType)
    elif discontinuousCellsCount == hints[row] + 1:
        # print("i, disCount, hints[i]", row, discontinuousCellsCount, hints[row])
        isChanged |= ExcludeDiagonallyJointCells(emptyCell, row, rowCount, isNotSet, trySetType)
    return isChanged
def ExcludeDiagonallyJointCells(emptyCell, row, rowCount, isNotSet, trySetType):
    lastRow = row - 1
    nextRow = row + 1
    isChanged = False
    print(emptyCell)
    if len(emptyCell) == 0:
        return False
    lastCells = emptyCell[0]
    for i in range(1, len(emptyCell)):
        cells = emptyCell[i]
        if len(lastCells) == 1 and len(cells) == 1 and cells[0] == lastCells[0] + 2:
            # * (1) 0 T 0
            # *     0 0 0 <- 2nd
            if isNotSet(row, cells[0]) and isNotSet(row, lastCells[0]):
                if lastRow >= 0:
                    isChanged |= trySetType(lastRow, lastCells[0] + 1)
                if nextRow < rowCount:
                    isChanged |= trySetType(nextRow, lastCells[0] + 1)
        elif len(lastCells) == 1 and len(cells) == 3 and cells[0] == lastCells[0] + 2:
            # (2) 0 T 0 0 0
            #     T 0 T T T <- 2nd
            if isNotSet(row, cells[0]) and isNotSet(row, cells[1]) and isNotSet(row, cells[2]) and isNotSet(row, lastCells[0]):
                if lastRow >= 0:
                    isChanged |= trySetType(lastRow, lastCells[0] + 1)
                if nextRow < rowCount:
                    isChanged |= trySetType(nextRow, lastCells[0] + 1)
        elif len(lastCells) == 3 and len(cells) == 1 and cells[0] == lastCells[2] + 2:
            #(2) 0 0 0 T 0
            #    T T T 0 T <-4th
            if isNotSet(row, cells[0]) and isNotSet(row, lastCells[1]) and isNotSet(row, lastCells[2]) and isNotSet(row, lastCells[0]):
                if lastRow >= 0:
                    isChanged |= trySetType(lastRow, cells[0] - 1)
                if nextRow < rowCount:
                    isChanged |= trySetType(nextRow, cells[0] - 1)
        elif len(cells) == 3 and isNotSet(row, cells[0]) and isNotSet(row, cells[1]) and isNotSet(row, cells[2]):
            #(1) 0 0 0
            #    T 0 T <- 2nd
            if lastRow >= 0:
                isChanged |= trySetType(lastRow, cells[1])
            elif (nextRow < rowCount):
                isChanged |= trySetType(nextRow, cells[1])
        lastCells = cells
    return isChanged
def ExcludeCornerCell(tentMap):
    # T 0
    # 0 0 <- impossible
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        for column in range(columnCount):
            if tentMap[row][column].isTree:
                lastRow = row - 1
                lastColumn = column - 1
                nextRow = row + 1
                nextColumn = column + 1
                isTopNotSet = False
                isBottomNotSet = False
                isLeftNotSet = False
                isRightNotSet = False
                if lastRow >= 0:
                    isTopNotSet = tentMap[lastRow][column].isNotSet
                if nextRow < rowCount:
                    isBottomNotSet = tentMap[nextRow][column].isNotSet
                if lastColumn >= 0:
                    isLeftNotSet = tentMap[row][lastColumn].isNotSet
                if nextColumn < columnCount:
                    isRightNotSet = tentMap[row][nextColumn].isNotSet
                if isTopNotSet and isLeftNotSet and (not isBottomNotSet) and (not isRightNotSet):
                    isChanged |= tentMap[lastRow][lastColumn].trySetType(CellType.grass)
                elif isTopNotSet and (not isLeftNotSet) and (not isBottomNotSet) and isRightNotSet:
                    isChanged |= tentMap[lastRow][nextColumn].trySetType(CellType.grass)
                elif (not isTopNotSet) and (not isLeftNotSet) and isBottomNotSet and isRightNotSet:
                    isChanged |= tentMap[nextRow][nextColumn].trySetType(CellType.grass)
                elif (not isTopNotSet) and isLeftNotSet and isBottomNotSet and (not isRightNotSet):
                    isChanged |= tentMap[nextRow][lastColumn].trySetType(CellType.grass)
    return isChanged
def ExcludeImpossibleCell(tentMap):
    isChanged = False
    (rowCount, columnCount) = tentMap.shape
    for row in range(rowCount):
        for column in range(columnCount):
            if tentMap[row][column].isNotSet:
                newMap = DeepCopyMap(tentMap)
                newMap[row][column].setType(CellType.tent)
                SetGrassAroundTent(newMap)
                lastRow = row -1
                lastColumn = column - 1
                nextRow = row + 1
                nextColumn = column + 1
                treeWithOneTentCount = 0
                if lastRow >= 0:
                    treeWithOneTentCount += (HasNTentAroundTree(newMap, lastRow, column, 0, [[row, column]]) == True)
                if nextRow < rowCount:
                    treeWithOneTentCount += (HasNTentAroundTree(newMap, nextRow, column, 0, [[row, column]]) == True)
                if lastColumn >= 0:
                    treeWithOneTentCount += (HasNTentAroundTree(newMap, row, lastColumn, 0, [[row, column]]) == True)
                    if lastRow >= 0:
                        treeWithOneTentCount += (HasNTentAroundTree(newMap, lastRow, lastColumn, 0, [[row, column]]) == True)
                    if nextRow < rowCount:
                        treeWithOneTentCount += (HasNTentAroundTree(newMap, nextRow, lastColumn, 0, [[row, column]]) == True)
                if nextColumn < columnCount:
                    treeWithOneTentCount += (HasNTentAroundTree(newMap, row, nextColumn, 0, [[row, column]]) == True)
                    if lastRow >= 0:
                        treeWithOneTentCount += (HasNTentAroundTree(newMap, lastRow, nextColumn, 0, [[row, column]]) == True)
                    if nextRow < rowCount:
                        treeWithOneTentCount += (HasNTentAroundTree(newMap, nextRow, nextColumn, 0, [[row, column]]) == True)
                if treeWithOneTentCount > 1: # an impossible cell, must be grass
                    tentMap[row][column].setType(CellType.grass)
                    isChanged = True
    return isChanged
def HasNTentAroundTree(tentMap, row, column, n, excludedCoordates = []):
    (rowCount, columnCount) = tentMap.shape
    if tentMap[row][column].isTree:
        lastRow = row - 1
        lastColumn = column - 1
        nextRow = row + 1
        nextColumn = column + 1
        tentCount = 0
        if lastRow >= 0 and (not ContainCoordinate(excludedCoordates, lastRow, column)):
            tentCount += (tentMap[lastRow][column].isTent or tentMap[lastRow][column].isNotSet)
        if nextRow < rowCount and (not ContainCoordinate(excludedCoordates, nextRow, column)):
            tentCount += (tentMap[nextRow][column].isTent or tentMap[nextRow][column].isNotSet)
        if lastColumn >= 0 and (not ContainCoordinate(excludedCoordates, row, lastColumn)):
            tentCount += (tentMap[row][lastColumn].isTent or tentMap[row][lastColumn].isNotSet)
        if nextColumn < columnCount and (not ContainCoordinate(excludedCoordates, row, nextColumn)):
            tentCount += (tentMap[row][nextColumn].isTent or tentMap[row][nextColumn].isNotSet)
        return (tentCount == n)
    return None
def ContainCoordinate(coordinates, row, column):
    for i in range(len(coordinates)):
        if coordinates[i][0] == row and coordinates[i][1] == column:
            return True
    return False

def solve(treeMap, topHints, leftHints):

    print("Here Solve function")
    (rowCount, columnCount) = treeMap.shape
    # print(rowCount, columnCount)

    result = []
    tentMap = np.empty((rowCount, columnCount), dtype=object) 
    
    for row in range(rowCount):
        for column in range(columnCount):
            tentMap[row][column] = Cell(row, column)
    for row in range(rowCount):
        for column in range(columnCount):
            if treeMap[row][column] and tentMap[row][column].isNotSet:
                tentMap[row][column].setType(CellType.tree)
    (isValid, errorMessage) = checkIsValid(tentMap, topHints, leftHints)

    if not isValid:
        result.append("<br>: " + errorMessage)
        return result

    result.append(MapSnapshot([], tentMap, isValid, False, "input"))
    stepCount = 1
    prevState = toHtml(tentMap)

    RemoveZeroColumnRow(tentMap, topHints, leftHints) #well done
    (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "ignore zero columns and rows")

    print("----------ignore zero columns and rows------> ", stepCount)
    seePresentState(tentMap)

    if canReturn:
        return result

    simplifiedMap = DeepCopyMap(tentMap)
    simplifiedTopHints = DeepCopyArray(topHints)
    simplifiedLeftHints = DeepCopyArray(leftHints)


    # circulation process
    # step:
    # first RemoveAssociatedTrenAndTents
    k = 0
    while isValid:
        k += 1
        CopySetCells(simplifiedMap, tentMap)
        print("-----while start", k)
        seePresentState(tentMap)
        seePresentState(simplifiedMap)
        isRemoved = RemoveAssociatedTreesAndTents(simplifiedMap, simplifiedTopHints, simplifiedLeftHints)
        if isRemoved:

            print("--------RemoveAssociatedTreesAndTents -> ", isRemoved)
            # seePresentState(simplifiedMap)

            result.append(MapSnapshot(None, None, False, False, "Remove associated trees and tents"))

        isChanged = excludeLand(simplifiedMap)
        if isChanged:

            CopySetCells(tentMap, simplifiedMap)
            # SetGrassAroundTent(simplifiedMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "exclude open land (no adjacent tree)")

            print("-----exclude open land (no adjacent tree)---->")
            seePresentState(tentMap)

            if canReturn:
                break
            if canContinue:
                continue

        isChanged = PlaceExplicitTents(simplifiedMap, simplifiedTopHints, simplifiedLeftHints)
        if isChanged:
            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "fill in tents based on hints")

            print("--------fill in tents based on hints")
            seePresentState(tentMap)

            if canReturn:
                break
            if canContinue:
                continue

        isChanged = PlaceTentNextToIsolatedsTree(simplifiedMap)
        if isChanged:

            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            print("---------PlaceTentNextToIsolatedTree")
            seePresentState(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "fill in tents next to isolated trees")

            if canReturn:
                break
            if canContinue:
                continue

        isChanged = PlaceDeducedTents(simplifiedMap, simplifiedTopHints, simplifiedLeftHints)
        if isChanged:

            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            print("-----fill in tents based on hints and deduction---->")
            seePresentState(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "fill in tents based on hints and deduction")
            if canReturn:
                break
            if canContinue:
                continue

        isChanged = ExcludeFullyFilledLine(simplifiedMap, simplifiedTopHints, simplifiedLeftHints)
        if isChanged:

            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            print("-----exclude fully filled lines---->")
            seePresentState(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "exclude fully filled lines")
            if canReturn:
                break
            if canContinue:
                continue
        isChanged = ExcludeDiagonallyJointCell(simplifiedMap, simplifiedTopHints, simplifiedLeftHints)
        if isChanged:
            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            print("-----exclude diagonally joint cells---->")
            seePresentState(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "exclude diagonally joint cells")
            if canReturn:
                break
            if canContinue:
                continue
        isChanged = ExcludeCornerCell(simplifiedMap)
        if isChanged:
            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            print("-----exclude corner cell---->")
            seePresentState(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "exclude corner cell")
            if canReturn:
                break
            if canContinue:
                continue
        isChanged = ExcludeImpossibleCell(simplifiedMap)
        if isChanged:

            CopySetCells(tentMap, simplifiedMap)
            SetGrassAroundTent(tentMap)

            print("exclude impossible cells>")
            seePresentState(tentMap)

            (prevState, stepCount, canContinue, canReturn) = logStatus(tentMap, topHints, leftHints, prevState, result, stepCount, "exclude impossible cells")
            if canReturn:
                break
            if canContinue:
                continue
        break

    print("--------last------->")
    seePresentState(tentMap)

    return result
    # resultString = json.dumps(result)
    # resultString = resultString.replace("_", "")
    # resultString = resultString.replace("changedCells", "changed")
    # print(resultString)
    # return resultString



# return format:
# [
#     [
#         {
#             "changed": [Cell, Cell, Cell...]
#             "map":
#                 [
#                     [Cell, Cell, Cell...]
#                     ...
#                 ]
#         }
#     ],
#     [
#         {
#             "changed": [Cell, Cell, Cell...]
#             "map":
#                 [
#                     [Cell, Cell, Cell...]
#                     ...
#                 ]
#         }
#     ]
#     ...
# ]




