import streamlit as st
import numpy as np

import Images

from Solver import  solve, Cell, CellType, MapSnapshot, _undef

global stepResults
global currentStep
global rowCount
global columnCount
global topHints
global leftHints
global puzzle
global cellHeight, results, heightInt, treeMap
global placeholder, step, stepContent

# Make the background white
st.markdown(
    f"""
    <style>
        [data-testid="stAppViewContainer"]{{
            background-color: white;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

def load_puzzle(uploaded_file): # Load the txt file and preprocessing
    global rowCount, columnCount, puzzle, leftHints, topHints, treeMap
    lines = uploaded_file.read().decode('utf-8').splitlines()
    rowCount, columnCount = map(int, lines[0].split())
    puzzle = [list(line.split()[0]) for line in lines[1:rowCount + 1]]
    leftHints = list(int(line.split()[1:][0]) for line in lines[1:rowCount + 1])
    topHints = list(map(int, lines[rowCount + 1].split()))

    print(rowCount, columnCount)
    for i in range(rowCount):
        print(puzzle[i])
    treeMap = np.zeros((rowCount, columnCount), dtype=int)
    for i in range(rowCount):
        for j in range(columnCount):
            if puzzle[i][j] == '.':
                treeMap[i][j] = 0
            else:
                treeMap[i][j] = 1
                 
def create_grid_layout(): 
    global cellHeight, heightInt, rowCount, columnCount, puzzle
    with st.container():
        rows = [st.columns(columnCount + 1, gap="small") for _ in range(rowCount + 1)]
        heightInt = 704 / (columnCount + 1)

        # Iterate over rows and columns to create containers with specified height

        for i in range(rowCount):
            for j in range(columnCount):
                if puzzle[i][j] == '.':
                    rows[i][j].write(f"""
                            <div style="padding: 0px; margin: 0px; height:{heightInt}px; 
                                width:{heightInt + 1}px; display: flex; align-items: center; 
                                justify-content: center; border:1px solid black;">
                            </div>
                            """,
                                     unsafe_allow_html=True
                                     )
                elif puzzle[i][j] == 'T':
                    rows[i][j].write(f"""
                                <div style="padding: 0px; margin: 0px; height:{heightInt}px; 
                                    width:{heightInt + 1}px; display: flex; align-items: center; 
                                    justify-content: center; border:1px solid black; ">
                                <img src={Images.input_treeUrl} style="width: 100%; height: 100%;"/>
                                </div>
                                """,
                                     unsafe_allow_html=True)

        for i in range(rowCount):
            rows[i][columnCount].write(f"""
                            <div style="padding: 0px; margin: 0px; height:{heightInt}px; 
                                width:{heightInt}px; display: flex; align-items: center; 
                                justify-content: center;">
                                <div style="padding: 0px; margin: 0px; height:{heightInt / 2.5}px; 
                                width:{heightInt}px; display: flex; align-items: center; 
                                justify-content: center; border-bottom: 0.5px solid black; 
                                border-right: 0.5px solid black; border-top: 0.5px solid black; font-size:25px">{leftHints[i]}</div>
                            </div>
                            """,
                                       unsafe_allow_html=True
                                       )
        for i in range(columnCount):
            rows[rowCount][i].write(f"""
                            <div style="padding: 0px; margin: 0px; height:{heightInt - 10}px; 
                                width:{heightInt}px; display: flex; align-items: center; 
                                justify-content: center;">
                                <div style="padding: 0px; margin: 0px; height:{heightInt - 10}px; 
                                width:{heightInt / 2.5}px; display: flex; align-items: center; 
                                justify-content: center; border-bottom: 0.5px solid black; 
                                border-right: 0.5px solid black; border-left: 0.5px solid black; font-size:25px">{topHints[i]}</div>
                            </div>
                            """, unsafe_allow_html=True)


def create_solution_map():
    global cellHeight, heightInt, rowCount, columnCount
    global placeholder, currentStep, stepResults, step

    result = stepResults[currentStep - 1]
    if result.map is None and currentStep > 1:
        result = stepResults[currentStep - 2]
    # st.write(result.map.shape)
    # for i in range(rowCount):
    #     s = ""
    #     for j in range(columnCount):
    #         if result.map[i][j].type == CellType.grass:
    #             s += "□"
    #         elif result.map[i][j].type == CellType.tent:
    #             s += "▲"
    #         elif result.map[i][j].type == CellType.tree:
    #             s += "T"
    #         else:  # uncertain or notTested
    #             s += "_"
        # st.write(s)
    # cellHeight = (704 )/(columnCount + 1)
    with placeholder.container():
        st.markdown(
            f"""
                <style>
                    [data-testid="block-container"]>[data-testid="stVerticalBlockBorderWrapper"]>
                    [class="st-emotion-cache-1wmy9hl e1f1d6gn1"]>[data-testid="stVerticalBlock"]>div:nth-child(8){{
                        width:400px;
                    }}
                </style>
                """,
            unsafe_allow_html=True
        )
        Map = [st.columns(columnCount) for _ in range(rowCount)]

        cellHeight = 704 / columnCount
        for i in range(rowCount):
            for j in range(columnCount):
                if result.map[i][j].type == CellType.grass:
                    Map[i][j].write(f"""
                             <div style="padding: 0px; margin-left: 8px; margin-bottom: 8px; height:{cellHeight-8}px; 
                                width:{cellHeight-8}px; align-items: center; 
                                justify-content: center; border-radius:5px; overflow :hidden;">
                            <img src={Images.grass2_url} style="width: 100%; height: 100%;"/>
                            </div>
                            """, unsafe_allow_html=True)
                elif result.map[i][j].type == CellType.tent:
                    Map[i][j].write(f"""
                            <div style="padding: 0px; margin-left: 8px; margin-bottom: 8px; height:{cellHeight-8}px; 
                                width:{cellHeight-8}px; align-items: center; 
                                justify-content: center; border-radius:5px; ; overflow :hidden;">
                            <img src={Images.tent_5_url} style="width: 100%; height: 100%; background-color:#ECD279 "/>
                            </div>
                            """, unsafe_allow_html=True)
                elif result.map[i][j].type == CellType.tree:
                    Map[i][j].write(f"""
                            <div style="padding: 0px; margin-left: 8px; margin-bottom: 8px; height:{cellHeight-8}px; 
                                width:{cellHeight-8}px; align-items: center; 
                                justify-content: center; border-radius:10px; overflow :hidden;">
                            <img src={Images.output_treeUrl3} style="width: 100%; height: 100%;"/>
                            </div>
                            """, unsafe_allow_html=True)
                else: # uncertain or notTested
                    Map[i][j].write(f"""
                            <div style="padding: 0px; margin-left: 8px; margin-bottom: 8px; height:{cellHeight-8}px; 
                                width:{cellHeight-8}px; align-items: center; 
                                justify-content: center; border-radius:5px; background-color:#5D6159 ; overflow :hidden;">
                            </div>
                            """, unsafe_allow_html=True)


def setState(i):
    st.session_state.stage = i
def setStepContent():
    global step, stepResults, stepContent
    stepContent = "Step " + str(currentStep) + " :  ->  " + stepResults[currentStep-1].message

if 'stage' not in st.session_state:
    st.session_state.stage = 0

def main():
    global currentStep, stepResults, rowCount, columnCount, puzzle
    global placeholder, step, stepContent
    st.title('Tent and Tree Puzzle Solver')
    uploaded_file = st.file_uploader("Upload a text file", type="txt")

    if uploaded_file is not None:
        load_puzzle(uploaded_file)

    # This is a button which create the input grid map.    
    st.button('Create', key="create", on_click=setState, args=[1])
    if st.session_state.stage >= 1:
        create_grid_layout()

    # This is a button which create the solution grid map.
    st.write("")
    st.button('Solve', key="solve", on_click=setState, args=[2])
    if st.session_state.stage == 2:

        stepResults = solve(treeMap, topHints, leftHints)

        # step = 1

        # step heading:
        currentStep = st.slider(
            "My Slider",
            1, len(stepResults), 1, step=1, key="myslider")
        setStepContent()
        st.write(stepContent)
        placeholder = st.empty()
        create_solution_map()





if __name__ == '__main__':
    main()