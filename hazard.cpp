#include "datapath.h"

void Datapath::hazard(void){

    if(MEMWB.destReg_o != 0 
    && !(EXMEM.destReg_o != 0
        && (EXMEM.destReg_o = IDEX.src1Reg_o))
    && (MEMWB.destReg_o = IDEX.src1Reg_o) IDEX.src1Reg_o = EXMEM.result_o; //Enabling mux to get register value directly form WB to EX for the first register

    if(MEMWB.destReg_o != 0 
    && !(EXMEM.destReg_o != 0
        && (EXMEM.destReg_o = IDEX.src2Reg_o))
    && (MEMWB.destReg_o = IDEX.src2Reg_o) IDEX.src2Reg_o = EXMEM.result_o; //Enabling mux to get register value directly form WB to EX for the second register

}
