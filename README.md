# Datapath Simulator
Ufuk Arslan & Selman Berk Özkurt

## RV32I Emulation
We built a RV32I instruction emulator first, to trace the execution, using which we can infer the hazards. Data memory and instruction memory are implemented separately, the latter being immutable by the emulated processor itself. Other than that, we can fully emulate a RISC-V core with its registers and full data memory (taking into account alignment and endianness issues as well) without an operating system.

### Input File
We did not program a fully functional assembler becuse it is beyond the scope. What we did was a simple parser that takes RISC-V instructions in different lines and stores them in a virtual instruction memory in the emulator. We do not support pseudoinstructions, empty lines, labels and comments in our input code. Yet, it is possible to easily implement many algorithms. Notice that all forms of register naming is implemented to make programming easier. One example input file (`inp.a`) is provided.

### Usage
In a terminal type `python main.py inputfile` to run the code for `inputfile`. The results will be written to the `stdout`. Python 3 was used during development. 

### Output Dump Format
In order to make analysis of the execution more explicit, in accordance with the main aim of this study, All the instructions emulated are tallied with relevant information such as the instruction, source and destination registers and their values, other arguments, program counter for that instruction, the clock cycle and the number of stalls for that instruction.

## Hazard and Timing Considerations
There are three types of hazards we may face when we are creating a pipelined structure. Remember we assume *no branch prediction* and data *forwarding*.

### Structural Hazards
They occur when our hardware can not handle some combinations of instructions simultaneously, which means that we have resource conflicts. We do not take these cases into consideration in our project.

### Control Hazards
They occur when we have instructions that change the PC, the main reason of this hazard is the pipelining of branches. Noting that we did not implement any branch prediction techniques, we considered the best way we can use without them. So, we need to know whether the branch is taken or not as early as possible. Inside ID step if we find out that we have a branch type instruction, we use a simple adder at hardware level to compute the effective address of the target instruction of the branch. We also include a simple comparator at ID step so that we find the result of whether the branch is going to be taken before going through ALU in the EX step. These are the optimizations we can do at hardware level, so in normal cases we need to add ONE STALL after each branch type instruction. However, since we decide the result of branch instructions at ID step, when the registers we use have dependencies over instructions coming before them, after forwarding, we are forced to do the comparisons at EX step, which means that we need to add TWO STALLS after those types of branch instructions.

### Data Hazards
They occur when previous instruction has dependancy on the current instruction. This causes conflicts in the registers or memory where we read or write data at cycles that we are no supposed to do. There are 3 cases which may cause problems and they are: 

* **RAW (read after write):** Consumer instruction reads the data before producer instruction writes that data. These are the most common data hazards, but luckily we can overcome most of them by using forwarding. So, we don't need to worry about all the cases of RAW when we are adding stalls. There is one specific case we need to handle and that occurs when we load data from memory to a register, then use that register in the next instruction, and for this case we need to add ONE STALL between those two instructions.
* **WAW (write after write):** First instruction writes after second instruction writes to the same memory or register. This case does not happen in the pipeline structure we use.
* **WAR (write after read):** Latter instruction writes the data before former instruction reads that data. This case also does not happen in the pipeline structure we use.

### Tallies Calculated
After printing all the execution as decribed in the dump format section in addition to the memory and registers, the program calculates and prints number of instructions executed, number of clock cycles and number of stalls added.


## Modules

### The `main.py` Module
This module gets the command line arguments, creates an instance of an `emulator.machine` object and lets it run. Also, it makes use of the timing module (`hazard`) to analyze the timing considerations of its contents. Then it calculates the statistics and prints them. Most other printing is done using the modules' own printing implementations:

```python
import sys      #to get the input file name as the command line argument
import emulator #the RISC-V emulator
import hazard   #the module to calculate the timing of the instructions


if(len(sys.argv)!=2): #check for the correct use of the application and print usage instructions if incorrect
	print("usage:\"python[3] main.py <inputFileName>\"")
	print("input file shoud have RISC-V instructions (without pseudoinstructions, labels and empty lines)")
	sys.exit(-1)

#create an emulator object with instructions in the file given as a command line argument
mymac = emulator.machine(sys.argv[1])
try:
    mymac.run()
except Exception as e: #if the run returns by throwing, then print bug warning but do the rest of the tallying so the user can trace the bug 
    print("!!!!!!!!!!BUG!!!!!!!!!!!") 
    print(e)
    print("I will dump stuff up to here anyway:")

mymac.showprogram()		#first print the human-readable tokens fetched into the instruction memory of the machine
mymac.showdata()		#then print the data memory of the machine on a byte basis
mymac.showregs()		#then show the content of the 32 registers
#mymac.showdump()		#then maybe show the emulator trace or...
hazard.hazardDetector(mymac.dump)#call the timing simulator which writes timing data into the program trace dump and prints it beautifully

#finally, calculate and print the necessary statistics about the execution
print("\n\n**CLOCKS AND STALLS**")
print("Number of instructions executed: ", len(mymac.dump))
print("Number of clock cycles: ", mymac.dump[-1][5][0])
print("Number of stalls added: ", mymac.dump[-1][5][0] - len(mymac.dump) -4)
```

### `emulator` Module 
This is the module that actually implements the RV32I ISA and executes the instructions. Note that the timing analysis is done in another module (`hazard`) and the emulator module makes use of other modules for memory management and exact logical implementations of the operations with details like sign extension. This can be thought as the most central module in the project.

```python
import ops
import mem

class machine:
    def __init__(self, filename):
        self.instmem = dict()               #the instruction memory(holds instructions as tokenized input lines, indexed by the location in instruction memory)
        self.datamem = mem.datamemory()     #the data memory, see mem module for implementation
        self.reg = mem.regfile()            #the register file, see mem module for implementation
        self.dump = list()                  #the dump list, which traces all the execution and is printed later
        addr = int(0)                       #address to write the next instruction read from the input
        inp = open(filename, "r")           #the file with instructions written
        ##digest the input lines to instmem
        while (True):
            line = inp.readline()
            if not line:
                break
            text = str(line).replace(",", " ").replace("(", " ").replace(")", " ").rsplit()  # a simple tokenizer. example output: ["add","x5","x0","x1"]
            self.instmem[addr] = text
            addr += 4
        self.PC = 0                     #initialize PC for execution
        self.counter = 0                #initialize instruction counter (number of instructions executed)

    def instruction(self, inputLine):  # the main function to process an instruction
        text = self.instmem[self.PC]  # read from instruction memory
        op = text[0]
        self.counter += 1               
        if (any([op == i for i in ["add", "sub", "xor", "or", "and", "sll", "srl", "sra", "slt", "sltu"]])):
                                        #Process basic Rtype Instructions
            d = self.regIdx(text[1])    #destination register number from instruction
            s1 = self.regIdx(text[2])   #source register 1 number from instruction
            arg1 = self.reg[s1]         #argument read from register
            s2 = self.regIdx(text[3])
            arg2 = self.reg[s2]
            result = getattr(ops, "op" + op)(arg1, arg2)        #see ops file for logical implementation of most instructions
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])#this is the format used for dump NOTE: executor does not write timing, hazard module will do that
            self.PC += 4
        elif (any([op == i for i in ["addi", "xori", "ori", "andi", "slli", "srli", "srai", "slti", "sltui"]])):
                                            #Process arithmetic Itype Instructions
            d = self.regIdx(text[1])        #the same as Rtype section
            s1 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            s2 = -1                         #immediate arguments are traced as if from register -1
            arg2 = int(text[3])             #immediate argument directly read from the instruction
            immop = op[:len(op) - 1]        #get the logical operation name by removing i from op
            result = getattr(ops, "op" + immop)(arg1, arg2)
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += 4
        elif (any([op == i for i in ["lb", "lh", "lw", "lbu", "lhu"]])):
                                            #Process load instructions
            d = self.regIdx(text[1])        #source and destionation conventions are the same as before
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
                                                #Process Store instructions
            s1 = self.regIdx(text[1])           #same convention for sources but different for destination. See below.
            s2 = self.regIdx(text[3])
            arg1 = self.reg[s1]
            arg2 = self.reg[s2]
            immptr = int(text[2])
            location = immptr + arg2
            result = getattr(ops, "op" + op)(self.datamem, location,
                                             arg1)  # what will be read from memory later is returned here
            self.dump.append([(self.PC, self.counter), op, (-1, immptr), (s1, arg1), (s2, arg2), (-1, -1)]) #for S-Type instructions, we trace the immediate argument as an immediate destination
            self.PC += 4
        elif (any([op == i for i in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]])):
                                                #Process branch instructions
            s1 = self.regIdx(text[1])           #similar to Stype instructions
            s2 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            arg2 = self.reg[s2]
            immptr = int(text[3])
            offset = getattr(ops, "op" + op)(arg1, arg2, immptr)
            self.dump.append([(self.PC, self.counter), op, (-1, offset), (s1, arg1), (s2, arg2), (-1, -1)])#The result is traced as the ofset decided to branch as immediate
            self.PC += offset
        elif (op == "jal"): 
                                                #Jump and link is implemented here instead of in ops module
            d = self.regIdx(text[1])
            offset = int(text[2])
            self.reg[d] = self.PC + 4
            self.dump.append([(self.PC, self.counter), op, (d, self.PC + 4), (0, 0), (-1, offset), (-1, -1)])#there is a single source, so we trace (0,0) for one of the sources
            self.PC += offset                   #this is how jump happens
        elif (op == "jalr"):
                                                #This instruction is also implemented here but fits our Rtype and Itype convention for source and destination tracing 
            d = self.regIdx(text[1])
            s1 = self.regIdx(text[3])
            arg1 = self.reg[s1]
            s2 = -1                             #second argument is immediate
            arg2 = int(text[2])                 #immediate is read from the instruction
            location = arg1 + arg2              #calculate where to jump
            result = self.PC + 4
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += arg1 + arg2              #implement the jump itself
        elif (op == "lui"):
                                                #Load upper immediate is implemented here
            d = self.regIdx(text[1])
            arg1 = int(text[2])
            result = arg1 << 12                 #note that sign extension does not need special attention in this case
            self.reg[d] = result;
            self.dump.append([(self.PC, self.counter), op, (d, result), (0, 0), (-1, arg1), (-1, -1)])
            self.PC += 4
        elif (op == "auipc"):
                            #The sole Utype instruction
            d = self.regIdx(text[1])
            arg1 = int(text[2])
            result = (arg1 << 12) + self.PC
            self.reg[d] = result;
            self.dump.append([(self.PC, self.counter), op, (d, result), (0, 0), (-1, arg1), (-1, -1)])
            self.PC += 4
        elif (op == "ecall" or op == "ebreak"):
                            #We do not have an operating system or system call convention, so they are equivalent of NOP
            self.PC += 4
        else:               #if the op does not fit any in the RV32I instruction set
            raise Exception("Invalid instruction name")

    def run(self):  #this function can be used to repeatedly run the machine until an exception occurs or the instruction is empty
        while (True):
            try:
                inst = self.instmem[self.PC]    #this throws if there is no instruction in that PC and therefore the run returns
            except:
                return
            if (len(inst) == 0):                #this is implemented as a design choice, we wanted it to stop executing if the line there was empty.
                return
            self.instruction(inst)              #this may also throw, and also the run will throw

    def regIdx(self, text): #this function is to get the register index from possible aliases like sp that can be used in the source
        if (text == "zero"):#these if statements denote basic aliases
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
        elif (text[0] == "x"):#typical use case - register name starting with x
            res = int(text[1:])#either returns the number following x or throws if the number is invalid
            if (res > 31 or res < 0):
                raise Exception("invalid register index")
            return res
        elif (text[0] == "a"):
            res = int(text[1:])
            if (res > 7 or res < 0):
                raise Exception("invalid \"a\" register index")
            return res + 10 #registers "an" start with x10 and continue up to x17, therefore its index should be raised by 10
        elif (text[0] == "s"):#the same logic as a-type naming
            res = int(text[1:])
            if (res > 11 or res < 0):
                raise Exception("invalid \"s\" register index")
            if (res < 3):
                return res + 
            else:
                return res + 16
        elif (text[0] == "t"):#the same logic as s- and a-type naming
            res = int(text[1:])
            if (res > 6 or res < 0):
                raise Exception("invalid \"t\" register index")
            if (res < 3):
                return 5  #In RV32I, t-registers less than 3 are mapped to x5
            else:
                return res + 25
        else:   #if any of the formats above are not used where a register name was expected, throw an exception
            raise Exception("Invalid register syntax")
            
    #functions from here are related to printing status about the emulator 
    def showdump(self):
        print("\n\n********DUMP********")
        for i in self.dump:
            res = ""         #printing dump data which traces the whole execution with all ops,arguments and results
            for j in i:
                res += "%10s" % (str(j))
            print(res)

    def showprogram(self):
        print("\n\n****INSTRUCTIONS****")
        for i in sorted(self.instmem):
            res = "%6s:"%(str(i))
            for j in self.instmem[i]:       #prints the instruction memory tokens in human-readable format. Is a clean version of the input code
                res += "%6s" % (str(j))
            print(res)

    def showdata(self):
        print("\n\n********DATA********")   #prints the data memory byte-by-byte, only those locations that were written on. Both hex and decimal
        for i in sorted(self.datamem.storage):
            print("%6s:    %s"%(str(i),str(self.datamem.storage[i])))

    def showregs(self):
        print("\n\n******REGISTERS*****")   #shows the register file in decimal and also in hexadecimal
        for i in range(1, 32):
            print("x%2d:%10d    0x%x" % (i, self.reg[i], self.reg[i]))
            
```

### The `mem` Module
This module implements the byte-accessable data memory and and the register file as two distinct classes. It is to be used by the emulator module above. The operation of this module mainly has to do with the byte-alignment issues, handling little-endian memory management for data memory, and also to build an ergonomical interface for accessing registers including handling the special situation with register 0 in the register file.

```python
import ctypes	#to be used for getting last 8 bits of some data in an unsigned manner

class regfile: #the register file class to be used in the emulator
	def __init__(self):
		self.storage=[0 for i in range(32)]	#the data is stored as python integers in a list
	def __getitem__(self,key):			#python [] indexing is enabled for convenience 
		if(key==0):				#registers are indexed with numbers and index 0 always returns a 0
			return 0
		else:
			return self.storage[key]	#simply return data from the array
	def __setitem__(self,key,value):		#[] operator is again enabled
		if(key==0):
			return				#no action is done for register 0
		else:
			self.storage[key]=value		#otherwise write into the register wanted


class datamemory: #the class for data memory to be used in the emulator
	def __init__(self):
		self.storage=dict()	#all the data is held in a dictionary to avoid gigabytes-sized memory usage

	def get(self,index):		#all read-write is done in bytes in this module. see other functions for larger ones #DOES NOT SIGN EXTEND
		try:
			return self.storage[index]
		except:			#if nothing was written in that part of the memory, then return 0
			return 0
	def getword(self,index):	#read a 4-byte word
		if(index%4!=0):		#check for memory alignment and throw for errors
			raise Exception("Misaligned memory read address for word!")
			return
		else: #little endian
			return self.get(index)+(self.get(index+1)<<8)+(self.get(index+2)<<16)+(self.get(index+3)<<24) #combine the bytes in the memory
	def gethalf(self,index):	#the same as getword for 2-byte half words #DOES NOT SIGN EXTEND
		if(index%2!=0):
			raise Exception("Misaligned memory read address for half!")
			return
		else: #little endian
			return self.get(index)+(self.get(index+1)<<8)
	def write(self,index,data):				#writing a single byte into the memory. Again this is the only way to access the container
		self.storage[index]=ctypes.c_uint8(data).value	#this is done to get rid of the sign and get the least significant 8 bits
	def writehalf(self,index,data):
		if(index%2!=0):					#see getword for the explanation
			raise Exception("Misaligned memory write address for half!")
			return
		else: #little endian
			self.write(index,data)
			self.write(index+1,data>>8)
	def writeword(self,index,data):	#to write 32-bit words in the memory
		if(index%4!=0):		#again check for alignment
			raise Exception("Misaligned memory write address for word!")
			return
		else: #little endian
			self.write(index,data)		#write all the byte components in their corresponding addresses
			self.write(index+1,data>>8)
			self.write(index+2,data>>16)
			self.write(index+3,data>>24)
```

### The `ops` Module
This module provides a clean list of how the individual instructions are logically implemented. This is written here because they need special attention, especially while handling sign extension situations. For this, this module makes extensive use of the python `ctypes` module. The functions here are called by the emulator with their names, which also closely correspond to the names of the relevant instructions. This provides a very convenient way to possibly implement larger instruction sets

```pyhton
import ctypes as t #used to make sign-extensions correctly

#These operations are used for R-type instructions and arithmetic Itype instructions corresponding to them
#they are to be used in the emulator to implement logic, notably for correct sign-extension
#notice that all of these return unsigned 32-bit values to make further operations on these numbers bugless
def opadd(a,b): #for add and addi
	return t.c_uint32(a+b).value
def opsub(a,b): #for sub and subi
	return t.c_uint32(a-b).value
def opxor(a,b): #for xor and xori
	return t.c_uint32(a^b).value
def opor(a,b): #for or and ori
	return t.c_uint32(a|b).value
def opand(a,b): #for and and andi
	return t.c_uint32(a&b).value
def opsll(a,b): #for sll and slli
	return t.c_uint32(a<<b).value
def opsrl(a,b): #for srl and srli
	return t.c_uint32(t.c_uint32(a).value>>b).value
def opsra(a,b): #for sra and srai
	return t.c_uint32(a>>b).value
def opslt(a,b): #for slt and slti -- notice the sign difference between this and sltu logic 
	return t.c_uint32(t.c_int32(a).value<t.c_int32(b).value).value
def opsltu(a,b): #for sltu and sltui
	return t.c_uint32(t.c_uint32(a).value<t.c_uint32(b).value).value



#these operations only implement sign extension for data got from the memory
#the data memory object is also to be passed as an argument to implement sizing here, not in emulator module 
def oplb(mem,idx):#for lb
	return t.c_int8(mem.get(idx)).value
def oplbu(mem,idx):#for lbu
	return t.c_uint8(mem.get(idx)).value
def oplh(mem,idx):#for lh
	return t.c_int16(mem.gethalf(idx)).value
def oplhu(mem,idx):#for lhu
	return t.c_uint16(mem.gethalf(idx)).value
def oplw(mem,idx):#for lw
	return t.c_uint32(mem.getword(idx)).value

#the same for store instructions here
def opsb(mem,idx,data):#for sb
	mem.write(idx,data)
	return oplb(mem,idx) #this is returned to be able to maybe spot bugs, instead of returning nothing
def opsh(mem,idx,data):#for sh
	mem.writehalf(idx,data)
	return oplh(mem,idx)
def opsw(mem,idx,data):#for sw
	mem.writeword(idx,data)
	return oplw(mem,idx)


#implementations for branch operations, these calculate the offset to branch (what to add to PC)
#using the condition on the arguments  
def opbeq(a,b,immoffset):#for branch if equal
	if(a==b):
		return immoffset
	else:		#just go to the next instruction if the condition does not hold
		return 4
def opbne(a,b,immoffset):
	if(a!=b):#for branch if not equal
		return immoffset
	else:
		return 4
def opblt(a,b,immoffset):#for branch if less than
	if(t.c_int32(a).value < t.c_int32(b).value):#we care about meaning of the sign bit while comparing
		return immoffset
	else:
		return 4
def opbge(a,b,immoffset):#for branch if greater than or equal to
	if(t.c_int32(a).value >= t.c_int32(b).value):
		return immoffset
	else:
		return 4
def opbltu(a,b,immoffset):#for branch if less than (unsigned)
	if(t.c_uint32(a).value < t.c_uint32(b).value):#notice we make unsigned comparison from now on 
		return immoffset
	else:
		return 4
def opbgeu(a,b,immoffset):#for branch if greater than or equal to (unsigned)
	if(t.c_uint32(a).value >= t.c_uint32(b).value):
		return immoffset
	else:
		return 4

```

# The `hazard` Module
This is the module most relevant to the main aim of this project. This module is executed as the last module in `main.py`. After we finish executing all instructions, we have the list of instructions executed at each step in the dump list, and the function called `hazardDetector` of this module takes this dump list as a parameter. Inside `hazardDetector` function we traverse each instruction one by one and determine whether we need to add stalls or not. There, we also keep track of the cycles at the end of each instruction's execution. We explained the types of hazards we may encounter in such a datapath, and we took actions according to those possible hazards. Note that this hazard detection could have been done on an instruction-by-instruction basis, instead of after emulating all of the program. This would not make the code much more complex, but we chose it to keep it this way to separate the different logic as was done in other parts of the project as well.

```pyhton

def hazardDetector(instructions):
	# Lists of types to be used to add stalls
	branchType = ["beq", "bne", "blt", "bge", "bltu", "bgeu", "jal", "jalr"]
	loadType = ["lb", "lh", "lw", "lbu", "lhu"]

	# Initializing counter variables
	clockCounter = 4
	instructionCounter = 0
	
	print("\n\n*******EXECUTION******")
	print("arguments and results are as (register,value) with register being -1 for not a register")
	print("\n%10s%10s%10s%10s%10s%10s"%("PC&order","inst.","result","arg1","arg2","clk&stall"))
	print("-"*60)
	
	# After we get the dump, we can iterate through instructions one by one.
	for inst in instructions:
		# HANDLING CONTROL HAZARDS
		# If we have a branch type instruction we have two cases.
		# If this branch instruction is dependent to the destination register of previous instruction we add TWO STALLS,
		# otherwise we only add ONE STALL.
		if inst[1] in branchType:
			if not instructions[instructionCounter - 1][1] in branchType and (
                    	(inst[3][0] == instructions[instructionCounter - 1][2][0] and
                     	inst[3][0] != 0 and inst[3][0] != -1) or
                    	(inst[4][0] == instructions[instructionCounter - 1][2][0] and
                     	inst[4][0] != 0 and inst[4][0] != -1)):
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
			else:
				clockCounter += 1
				inst[5] = (clockCounter, 0)
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

```
