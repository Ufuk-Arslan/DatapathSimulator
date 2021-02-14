# dumpformat
"""
[
[(address,count),"add",(5),(0,0),(2,350),(cyclecount,stallcount)],
#rtype [(address,count),OP,(destreg),(s1reg,s1value),(s2reg,s2value),(cyclecount,stallcount)]
[(address,count),"addi",(5),(0,0),(-1,345),(cyclecount,stallcount)],
#itype [(address,count),OP,(destreg),(s1reg,s1value),(-1,immvalue),(cyclecount,stallcount)] #like -1 stands for an immediate source
[(address,count),"ble",(-1,0x665),(3,5),(2,3),(cyclecount,stallcount)],
#btype [(address,count),OP,(-1,immoffset),(s1reg,s1value),(s2reg,s2value),(cyclecount,stallcount)]
[(address,count),"sw",(-1,0xbbb),(3,5),(2,3),(cyclecount,stallcount)],
#stype [(address,count),OP,(-1,immptr),(s1reg,s1value),(s2reg,s2value),(cyclecount,stallcount)]
[],#u type, same as i type
[],#j type, implement as special case
]
"""
btype = ["beq", "bne", "blt", "bge", "bltu", "bgeu"]
ltype = ["lb", "lh", "lw", "lbu", "lhu"]
wasLastInstBranch = True
PC = 0


def main():
    return 0

def addStall(instructions, numOfStalls):
    # Let clock cycles pass
    instructions[PC][5][0] += numOfStalls
    # Add number of stalls
    instructions[PC][5][1] += numOfStalls


def hazardDetection(instructions):
    # There are three types of hazards we may face when we are creating a pipelined structure.

    # 1- STRUCTURAL HAZARDS: They arise from resource conflicts when the hardware cannot support all possible
    # combinations of instructions in simultaneous overlapped execution. We do not take these cases into consideration
    # in our project.

    # 2- CONTROL HAZARDS: They arise from the pipelining of branches and other instructions that change the PC. Noting
    # that we did not implement any branch prediction techniques, we considered the best way we can use without them.
    # So, we need to know whether the branch is taken or not as early as possible. Inside ID step if we find out that
    # we have a branch type instruction, we use a simple adder at hardware level to compute the effective address of the
    # target instruction of the branch. We also include a simple comparator at ID step so that we find the result of
    # whether the branch is going to be taken before going through ALU in the EX step. These are the optimizations we
    # can do at hardware level, so in normal cases we need to add ONE STALL after each branch type instruction. However,
    # since we decide the result of branch instructions at ID step, when the registers we use have dependencies over
    # instructions coming before them, after forwarding, we are forced to do the comparisons at EX step, which means
    # that we need to add TWO STALLS after those types of branch instructions.

    # 3- DATA HAZARDS: They arise when an instruction depends on the result of a previous instruction in a way that is
    # exposed by the overlapping of instructions in the pipeline.
    # There are 3 cases which may cause problems and they are:
    # 3a- RAW (read after write): Consumer instruction reads the data before producer instruction writes that data.
    # These are the most common data hazards, but luckily we can overcome most of them by using forwarding.
    # So, we don't need to worry about all the cases of RAW when we are adding stalls. There is one specific case
    # we need to handle and that occurs when we load data from memory to a register, then use that register in the next
    # instruction, and for this case we need to add ONE STALL between those two instructions.
    # 3b- WAW (write after write): First instruction writes after second instruction writes to the same memory or
    # register. This case does not happen in the pipeline structure we use.
    # 3c- WAR (write after read): Latter instruction writes the data before former instruction reads that data. This
    # case also does not happen in the pipeline structure we use.

    # HANDLING CONTROL HAZARDS
    # If we have a branch type instruction we have two cases.
    # If this branch instruction is dependent to the destination register of previous instruction we add TWO STALLS,
    # otherwise we only add ONE STALL.
    if instructions[PC][1] in btype:
        if not wasLastInstBranch and (instructions[PC][3][0] == instructions[PC-1][2][0] or instructions[PC][4][0] == instructions[PC-1][2][0]):
            addStall(instructions, 2)
        else:
            addStall(instructions, 1)

    # HANDLING DATA HAZARDS
    # If we have a load type instruction, and also if next instruction needs to use the register that is supposed to
    # change in this load instruction we add ONE STALL.
    if instructions[PC][1] in ltype:
        if instructions[PC][2] == instructions[PC + 1][3][0] or instructions[PC][2] == instructions[PC + 1][4][0]:
            addStall(instructions, 1)


if __name__ == '__main__':
    main()
