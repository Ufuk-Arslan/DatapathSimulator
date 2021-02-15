import ops
import mem
import sys

def hazardDetector(instructions):
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

	# Lists of types to be used to add stalls
	branchType = ["beq", "bne", "blt", "bge", "bltu", "bgeu", "jal", "jalr"]
	loadType = ["lb", "lh", "lw", "lbu", "lhu"]

	# Initializing counter variables
	clockCounter = 0
	instructionCounter = 0

	print("\n\n***HAZARD DETECTION***")

	#  Following executed iterations one by one
	for inst in instructions:
		# HANDLING CONTROL HAZARDS
		# If we have a branch type instruction we have two cases.
		# If this branch instruction is dependent to the destination register of previous instruction we add TWO STALLS,
		# otherwise we only add ONE STALL.
		if inst[1] in branchType:
			if not instructions[instructionCounter - 1][1] in branchType and (
					inst[3][0] == instructions[instructionCounter - 1][2][0] or
					inst[4][0] == instructions[instructionCounter - 1][2][0]):
				clockCounter += 3
				inst[5] = (clockCounter, 2)
			else:
				clockCounter += 2
				inst[5] = (clockCounter, 1)

		# HANDLING DATA HAZARDS
		# If we have a load type instruction, and also if next instruction needs to use the register that is supposed to
		# change in this load instruction we add ONE STALL.
		elif inst[1] in loadType:
			if inst[2][0] == instructions[instructionCounter + 1][3][0] or \
					inst[2][0] == instructions[instructionCounter + 1][4][0]:
				clockCounter += 2
				inst[5] = (clockCounter, 1)

		#  If there is no hazard we just add one cycle and continue with our instructions. The number of stalls will be 0.
		else:
			clockCounter += 1
			inst[5] = (clockCounter, 0)
		instructionCounter += 1
		res = ""
		for j in inst:
			res += "%10s" % (str(j))
		print(res)
	return 0


class machine:
    def __init__(self, filename):
        self.instmem = dict()
        self.datamem = mem.datamemory()
        self.reg = mem.regfile()
        self.dump = list()
        addr = int(0)
        inp = open(filename, "r")
        ##digest the input lines to instmem
        while (True):
            line = inp.readline()
            if not line:
                break
            text = str(line).replace(",", " ").replace("(", " ").replace(")", " ").rsplit()  # ["add","x5","x0","x1"]
            self.instmem[addr] = text
            addr += 4
        self.PC = 0
        self.counter = 0

    def instruction(self, inputLine):  # does not implement pseudoinstructions and labels
        text = self.instmem[self.PC]  # ["add","x5","x0","x1"]
        op = text[0]
        self.counter += 1
        if (any([op == i for i in ["add", "sub", "xor", "or", "and", "sll", "srl", "sra", "slt", "sltu"]])):
            # Rtype
            d = self.regIdx(text[1])
            s1 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            s2 = self.regIdx(text[3])
            arg2 = self.reg[s2]
            result = getattr(ops, "op" + op)(arg1, arg2)
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += 4
        elif (any([op == i for i in ["addi", "xori", "ori", "andi", "slli", "srli", "srai", "slti", "sltui"]])):
            # Itype
            d = self.regIdx(text[1])
            s1 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            s2 = -1
            arg2 = int(text[3])
            immop = op[:len(op) - 1]
            result = getattr(ops, "op" + immop)(arg1, arg2)
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += 4
        elif (any([op == i for i in ["lb", "lh", "lw", "lbu", "lhu"]])):  # I HAVE DOUBTS CHECK AGAIN
            # Like Itype
            d = self.regIdx(text[1])
            s1 = self.regIdx(text[3])
            arg1 = self.reg[s1]
            s2 = -1
            arg2 = int(text[2])
            location = arg1 + arg2
            result = getattr(ops, "op" + op)(self.datamem, location)
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += 4
        elif (any([op == i for i in ["sb", "sh", "sw"]])):
            # Stype
            s1 = self.regIdx(text[1])
            s2 = self.regIdx(text[3])
            arg1 = self.reg[s1]
            arg2 = self.reg[s2]
            immptr = int(text[2])
            location = immptr + arg2
            result = getattr(ops, "op" + op)(self.datamem, location,
                                             arg1)  # what will be read from memory later is returned here
            self.dump.append([(self.PC, self.counter), op, (-1, immptr), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += 4
        elif (any([op == i for i in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]])):
            # Btype
            s1 = self.regIdx(text[1])
            s2 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            arg2 = self.reg[s2]
            immptr = int(text[3])
            offset = getattr(ops, "op" + op)(arg1, arg2, immptr)
            self.dump.append([(self.PC, self.counter), op, (-1, offset), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += offset
        elif (op == "jal"):  # TRY THIS
            # Jtype
            d = self.regIdx(text[1])
            offset = int(text[2])
            self.reg[d] = self.PC + 4
            self.dump.append([(self.PC, self.counter), op, (d, self.PC + 4), (0, 0), (-1, offset), (-1, -1)])
            self.PC += offset
        elif (op == "jalr"):  # TRY THIS
            # Like Itype
            d = self.regIdx(text[1])
            s1 = self.regIdx(text[3])
            arg1 = self.reg[s1]
            s2 = -1
            arg2 = int(text[2])
            location = arg1 + arg2
            result = self.PC + 4
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += arg1 + arg2
        elif (op == "lui"):  # TRY THIS
            # Utype
            d = self.regIdx(text[1])
            arg1 = int(text[2])
            result = arg1 << 12
            self.reg[d] = result;
            self.dump.append([(self.PC, self.counter), op, (d, result), (0, 0), (-1, arg1), (-1, -1)])
            self.PC += 4
        elif (op == "auipc"):  # TRY THIS
            # Utype
            d = self.regIdx(text[1])
            arg1 = int(text[2])
            result = (arg1 << 12) + self.PC
            self.reg[d] = result;
            self.dump.append([(self.PC, self.counter), op, (d, result), (0, 0), (-1, arg1), (-1, -1)])
            self.PC += 4
        elif (op == "ecall" or op == "ebreak"):
            # Itype
            pass
        else:
            raise Exception("Invalid instruction name")

    def run(self):
        while (True):
            try:
                inst = self.instmem[self.PC]
            except:
                return
            if (len(inst) == 0):
                return
            self.instruction(inst)

    def regIdx(self, text):
        if (text == "zero"):
            return 0
        elif (text == "ra"):
            return 1
        elif (text == "sp"):
            return 2
        elif (text == "gp"):
            return 3
        elif (text == "tp"):
            return 4
        elif (text == "fp"):
            return 8
        elif (text[0] == "x"):
            res = int(text[1:])
            if (res > 31 or res < 0):
                raise Exception("invalid register index")
            return res
        elif (text[0] == "a"):
            res = int(text[1:])
            if (res > 7 or res < 0):
                raise Exception("invalid \"a\" register index")
            return res + 10
        elif (text[0] == "s"):
            res = int(text[1:])
            if (res > 11 or res < 0):
                raise Exception("invalid \"s\" register index")
            if (res < 3):
                return res + 8
            else:
                return res + 16
        elif (text[0] == "t"):
            res = int(text[1:])
            if (res > 6 or res < 0):
                raise Exception("invalid \"t\" register index")
            if (res < 3):
                return 5  # BUT WHY!!!
            else:
                return res + 25
        else:
            raise Exception("Invalid register syntax")

    def showdump(self):
        print("\n\n********DUMP********")
        for i in self.dump:
            res = ""
            for j in i:
                res += "%10s" % (str(j))
            print(res)

    def showprogram(self):
        print("\n\n****INSTRUCTIONS****")
        for i in sorted(self.instmem):
            res = ""
            for j in self.instmem[i]:
                res += "%6s" % (str(j))
            print(res)

    def showdata(self):
        print("\n\n********DATA********")
        for i in sorted(self.datamem.storage):
            print(str(i) + "\t:" + str(self.datamem.storage[i]))

    def showregs(self):
        print("\n\n******REGISTERS*****")
        for i in range(1, 32):
            print("x%2d:%10d    0x%x" % (i, self.reg[i], self.reg[i]))


mymac = machine(sys.argv[1])
try:
    mymac.run()
except Exception as e:
    print("!!!!!!!!!!BUG!!!!!!!!!!!")
    print(e)
    print("I will dump stuff up to here anyway:")

mymac.showprogram()
mymac.showdata()
mymac.showregs()
mymac.showdump()
hazardDetector(mymac.dump)
print("\n\n**CLOCKS AND STALLS**")
print("Number of instructions executed: ", len(mymac.dump))
print("Number of clock cycles: ", mymac.dump[-1][5][0])
print("Number of stalls added: ", mymac.dump[-1][5][0] - len(mymac.dump))

# UFUK: x0 registerinde ve immediatelarda(register -1) dependency olmaması lazım, senin kısımda onu kontrol eder misin?
