# main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import math

# Constants
c_p_h = 2
c_p_C = 1


# Define input model using Pydantic
class InputData(BaseModel):
    T_H_IN: float
    T_C_IN: float
    m_dot_H: float
    m_dot_C: float
    UA: float


app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.post("/calculate_unknowns")
def calculate_unknowns(input_data: InputData):
    # Initialize variables
    T_H_OUT = 0
    T_C_OUT = 0

    # Calculate temperature differences
    DeltaT_H = input_data.T_H_IN - T_H_OUT
    DeltaT_C = T_C_OUT - input_data.T_C_IN

    # Calculate heat transfer rates
    Q_H = input_data.m_dot_H * c_p_h * DeltaT_H
    Q_C = input_data.m_dot_C * c_p_C * DeltaT_C

    # Check if UA is sufficient for heat transfer
    if input_data.UA <= 0:
        raise HTTPException(status_code=400, detail="Error: UA must be a positive value for heat transfer.")
    if Q_H <= 0:
        raise HTTPException(status_code=400, detail="Error: Insufficient heat input from the hot fluid.")
    if Q_C >= 0:
        raise HTTPException(status_code=400, detail=f"Error: Insufficient heat removal by the cold fluid. Q_C = {Q_C}")

    # Calculate log mean temperature difference
    T_D_1 = input_data.T_H_IN - T_C_OUT
    T_D_2 = T_H_OUT - input_data.T_C_IN

    # Ensure positive logarithmic argument
    if abs(T_D_1) > 0 and abs(T_D_2) > 0:
        LMTD = abs((T_D_1 - T_D_2) / math.log(
            (abs(T_D_1) + 1e-10) / (abs(T_D_2) + 1e-10)))  # Add a small value to avoid division by zero
    else:
        raise HTTPException(status_code=400, detail="Error: Logarithmic argument is not positive.")

    # Calculate overall heat transfer
    Q_LMTD = input_data.UA * LMTD

    # Solve for the unknowns
    T_H_OUT = input_data.T_H_IN - Q_H / (input_data.m_dot_H * c_p_h)
    T_C_OUT = input_data.T_C_IN - Q_C / (input_data.m_dot_C * c_p_C)  # Corrected to subtract Q_C instead of adding

    return {"T_H_OUT": T_H_OUT, "T_C_OUT": T_C_OUT}


# To run this FastAPI app using Uvicorn, you can save the code in a file (e.g., main.py) and run the following command in your terminal:
# uvicorn main:app --reload
# The --reload option enables automatic code reloading during development.

# After running the above command, you can access the