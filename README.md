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


if(len(sys.argv)!=2): #check for the correct use of the application and print usage 
		      #instructions if incorrect
	print("usage:\"python[3] main.py <inputFileName>\"")
	print("input file shoud have RISC-V instructions (without pseudoinstructions, labels and empty lines)")
	sys.exit(-1)

#create an emulator object with instructions in the file given as a command 
#line argument
mymac = emulator.machine(sys.argv[1])
try:
    mymac.run()
except Exception as e: #if the run returns by throwing, then print bug warning but 
		       #do the rest of the tallying so the user can trace the bug 
    print("!!!!!!!!!!BUG!!!!!!!!!!!") 
    print(e)
    print("I will dump stuff up to here anyway:")

mymac.showprogram()		#first print the human-readable tokens fetched into
				#the instruction memory of the machine
mymac.showdata()		#then print the data memory of the machine on a 
				#byte basis
mymac.showregs()		#then show the content of the 32 registers
#mymac.showdump()		#then maybe show the emulator trace or...
hazard.hazardDetector(mymac.dump)#call the timing simulator which writes timing data 
				#into the program trace dump and prints it beautifully

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
        self.instmem = dict()               #the instruction memory(holds instructions 
					    #as tokenized input lines, indexed by the 
					    #location in instruction memory)
        self.datamem = mem.datamemory()     #the data memory, see mem module for 
					    #implementation
        self.reg = mem.regfile()            #the register file, see mem module for 
					    #implementation
        self.dump = list()                  #the dump list, which traces all the execution 
					    #and is printed later
        addr = int(0)                       #address to write the next instruction read 
					    #from the input
        inp = open(filename, "r")           #the file with instructions written
        ##digest the input lines to instmem
        while (True):
            line = inp.readline()
            if not line:
                break
            text = str(line).replace(",", " ").replace("(", " ").replace(")", " ").rsplit() 
	    # a simple tokenizer. example output: ["add","x5","x0","x1"]
            self.instmem[addr] = text
            addr += 4
        self.PC = 0                     #initialize PC for execution
        self.counter = 0                #initialize instruction counter 
					#(number of instructions executed)

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
            result = getattr(ops, "op" + op)(arg1, arg2)        #see ops file for logical implementation of 
	    							#most instructions
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
	    #this is the format used for dump NOTE: executor does not write timing, hazard module will do that
            self.PC += 4
        elif (any([op == i for i in ["addi", "xori", "ori", "andi", "slli", "srli", "srai", "slti", "sltui"]])):
                                            #Process arithmetic Itype Instructions
            d = self.regIdx(text[1])        #the same as Rtype section
            s1 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            s2 = -1                         #immediate arguments are traced as if 
	    				    #from register -1
            arg2 = int(text[3])             #immediate argument directly read from
	    				    #the instruction
            immop = op[:len(op) - 1]        #get the logical operation name by 
	    				    #removing i from op
            result = getattr(ops, "op" + immop)(arg1, arg2)
            self.reg[d] = result
            self.dump.append([(self.PC, self.counter), op, (d, result), (s1, arg1), (s2, arg2), (-1, -1)])
            self.PC += 4
        elif (any([op == i for i in ["lb", "lh", "lw", "lbu", "lhu"]])):
                                            #Process load instructions
            d = self.regIdx(text[1])        #source and destionation conventions are 
	    				    #the same as before
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
            s1 = self.regIdx(text[1])           #same convention for sources but different
	    					#for destination. See below.
            s2 = self.regIdx(text[3])
            arg1 = self.reg[s1]
            arg2 = self.reg[s2]
            immptr = int(text[2])
            location = immptr + arg2
            result = getattr(ops, "op" + op)(self.datamem, location,
                                             arg1)  # what will be read from 
					     	    #memory later is returned here
            self.dump.append([(self.PC, self.counter), op, (-1, immptr), (s1, arg1), (s2, arg2), (-1, -1)]) 
	    #for S-Type instructions, we trace the immediate argument as an immediate destination
            self.PC += 4
        elif (any([op == i for i in ["beq", "bne", "blt", "bge", "bltu", "bgeu"]])):
                                                #Process branch instructions
            s1 = self.regIdx(text[1])           #similar to Stype instructions
            s2 = self.regIdx(text[2])
            arg1 = self.reg[s1]
            arg2 = self.reg[s2]
            immptr = int(text[3])
            offset = getattr(ops, "op" + op)(arg1, arg2, immptr)
            self.dump.append([(self.PC, self.counter), op, (-1, offset), (s1, arg1), (s2, arg2), (-1, -1)])
	    #The result is traced as the ofset decided to branch as immediate
            self.PC += offset
        elif (op == "jal"): 
                                                #Jump and link is implemented here
						#instead of in ops module
            d = self.regIdx(text[1])
            offset = int(text[2])
            self.reg[d] = self.PC + 4
            self.dump.append([(self.PC, self.counter), op, (d, self.PC + 4), (0, 0), (-1, offset), (-1, -1)])
	    #there is a single source, so we trace (0,0) for one of the sources
            self.PC += offset                   #this is how jump happens
        elif (op == "jalr"):
                                                #This instruction is also implemented here but 
						#fits our Rtype and Itype convention for source
						#and destination tracing 
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
            result = arg1 << 12                 #note that sign extension does not need 
	    					#special attention in this case
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
                            #We do not have an operating system or system call convention,
			    #so they are equivalent of NOP
            self.PC += 4
        else:               #if the op does not fit any in the RV32I instruction set
            raise Exception("Invalid instruction name")

    def run(self):  #this function can be used to repeatedly run the machine until an 
    	            #exception occurs or the instruction is empty
        while (True):
            try:
                inst = self.instmem[self.PC]    #this throws if there is no instruction 
						#in that PC and therefore the run returns
            except:
                return
            if (len(inst) == 0):                #this is implemented as a design choice, 
	    					#we wanted it to stop executing if the line 
						#there was empty.
                return
            self.instruction(inst)              #this may also throw, and also the run will throw

    def regIdx(self, text): #this function is to get the register index from possible aliases 
    			    #like sp that can be used in the source
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
            res = int(text[1:])#either returns the number following x or throws if the 
	    		       #number is invalid
            if (res > 31 or res < 0):
                raise Exception("invalid register index")
            return res
        elif (text[0] == "a"):
            res = int(text[1:])
            if (res > 7 or res < 0):
                raise Exception("invalid \"a\" register index")
            return res + 10 #registers "an" start with x10 and continue up to x17, therefore 
	    		    #its index should be raised by 10
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
        else:   #if any of the formats above are not used where a register name 
		#was expected, throw an exception
            raise Exception("Invalid register syntax")
            
    #functions from here are related to printing status about the emulator 
    def showdump(self):
        print("\n\n********DUMP********")
        for i in self.dump:
            res = ""         #printing dump data which traces the whole 
	    		     #execution with all ops,arguments and results
            for j in i:
                res += "%10s" % (str(j))
            print(res)

    def showprogram(self):
        print("\n\n****INSTRUCTIONS****")
        for i in sorted(self.instmem):
            res = "%6s:"%(str(i))
            for j in self.instmem[i]:       #prints the instruction memory 
	    				    #tokens in human-readable format.
					    #Is a clean version of the input code
                res += "%6s" % (str(j))
            print(res)

    def showdata(self):
        print("\n\n********DATA********")   #prints the data memory byte-by-byte, only 
					    #those locations that were written on. Both hex 
					    #and decimal
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
		self.storage=[0 for i in range(32)]	#the data is stored as python 
							#integers in a list
	def __getitem__(self,key):			#python [] indexing is enabled for 
							#convenience 
		if(key==0):				#registers are indexed with numbers 
							#and index 0 always returns a 0
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
		self.storage=dict()	#all the data is held in a dictionary to avoid 
					#gigabytes-sized memory usage

	def get(self,index):		#all read-write is done in bytes in this module.
					#see other functions for larger ones #DOES NOT SIGN EXTEND
		try:
			return self.storage[index]
		except:			#if nothing was written in that part of the memory, then return 0
			return 0
	def getword(self,index):	#read a 4-byte word
		if(index%4!=0):		#check for memory alignment and throw for errors
			raise Exception("Misaligned memory read address for word!")
			return
		else: #little endian
			return self.get(index)+(self.get(index+1)<<8)+(self.get(index+2)<<16)+(self.get(index+3)<<24) 
			#combine the bytes in the memory
	def gethalf(self,index):	#the same as getword for 2-byte half words #DOES NOT SIGN EXTEND
		if(index%2!=0):
			raise Exception("Misaligned memory read address for half!")
			return
		else: #little endian
			return self.get(index)+(self.get(index+1)<<8)
	def write(self,index,data):				#writing a single byte into the memory.
								#Again this is the only way to access the container
		self.storage[index]=ctypes.c_uint8(data).value	#this is done to get rid of the sign and 
								#get the least significant 8 bits
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
			self.write(index,data)		#write all the byte components in their 
							#corresponding addresses
			self.write(index+1,data>>8)
			self.write(index+2,data>>16)
			self.write(index+3,data>>24)
```

### The `ops` Module
This module provides a clean list of how the individual instructions are logically implemented. This is written here because they need special attention, especially while handling sign extension situations. For this, this module makes extensive use of the python `ctypes` module. The functions here are called by the emulator with their names, which also closely correspond to the names of the relevant instructions. This provides a very convenient way to possibly implement larger instruction sets

```pyhton
import ctypes as t #used to make sign-extensions correctly

#These operations are used for R-type instructions and arithmetic Itype 
#instructions corresponding to them
#they are to be used in the emulator to implement logic, notably for 
#correct sign-extension
#notice that all of these return unsigned 32-bit values to make further 
#operations on these numbers bugless
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
def opslt(a,b): #for slt and slti -- notice the sign difference
#between this and sltu logic 
	return t.c_uint32(t.c_int32(a).value<t.c_int32(b).value).value
def opsltu(a,b): #for sltu and sltui
	return t.c_uint32(t.c_uint32(a).value<t.c_uint32(b).value).value



#these operations only implement sign extension for data got from the memory
#the data memory object is also to be passed as an argument to implement
#sizing here, not in emulator module 
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
	return oplb(mem,idx) #this is returned to be able to maybe
	#spot bugs, instead of returning nothing
def opsh(mem,idx,data):#for sh
	mem.writehalf(idx,data)
	return oplh(mem,idx)
def opsw(mem,idx,data):#for sw
	mem.writeword(idx,data)
	return oplw(mem,idx)


#implementations for branch operations, these calculate the offset 
#to branch (what to add to PC)
#using the condition on the arguments  
def opbeq(a,b,immoffset):#for branch if equal
	if(a==b):
		return immoffset
	else:		#just go to the next instruction if the
			#condition does not hold
		return 4
def opbne(a,b,immoffset):
	if(a!=b):#for branch if not equal
		return immoffset
	else:
		return 4
def opblt(a,b,immoffset):#for branch if less than
	if(t.c_int32(a).value < t.c_int32(b).value):#we care about meaning
						    #of the sign bit while comparing
		return immoffset
	else:
		return 4
def opbge(a,b,immoffset):#for branch if greater than or equal to
	if(t.c_int32(a).value >= t.c_int32(b).value):
		return immoffset
	else:
		return 4
def opbltu(a,b,immoffset):#for branch if less than (unsigned)
	if(t.c_uint32(a).value < t.c_uint32(b).value):#notice we make unsigned 
						      #comparison from now on 
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
		# If this branch instruction is dependent to the destination register 
		#of previous instruction we add TWO STALLS,
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
		# If we have a load type instruction, and also if next instruction 
		#needs to use the register that is supposed to
		# change in this load instruction we add ONE STALL.
		elif inst[1] in loadType:
			if inst[2][0] == instructions[instructionCounter + 1][3][0] or \
					inst[2][0] == instructions[instructionCounter + 1][4][0]:
				clockCounter += 2
				inst[5] = (clockCounter, 1)
			else:
				clockCounter += 1
				inst[5] = (clockCounter, 0)
		#  If there is no hazard we just add one cycle and continue with our 
		#instructions. The number of stalls will be 0.
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

## Test Cases
Most of the cases are taken from the lecture slides to validate with the results there. The program input used can be seen in the program memory tokens printed by the emulator. We demonstrate 5 example cases here:

These two examples demonstrate the effect of reordering instructions to reduce stalls.
```
****INSTRUCTIONS****
     0:    lw    x1     0    x0
     4:    lw    x2     8    x0
     8:   add    x3    x1    x2
    12:    sw    x3    24    x0
    16:    lw    x4    16    x0
    20:   add    x5    x1    x4
    24:    sw    x5    32    x0


********DATA********
    24:    0
    25:    0
    26:    0
    27:    0
    32:    0
    33:    0
    34:    0
    35:    0


******REGISTERS*****
x 1:         0    0x0
x 2:         0    0x0
x 3:         0    0x0
x 4:         0    0x0
x 5:         0    0x0
x 6:         0    0x0
x 7:         0    0x0
x 8:         0    0x0
x 9:         0    0x0
x10:         0    0x0
x11:         0    0x0
x12:         0    0x0
x13:         0    0x0
x14:         0    0x0
x15:         0    0x0
x16:         0    0x0
x17:         0    0x0
x18:         0    0x0
x19:         0    0x0
x20:         0    0x0
x21:         0    0x0
x22:         0    0x0
x23:         0    0x0
x24:         0    0x0
x25:         0    0x0
x26:         0    0x0
x27:         0    0x0
x28:         0    0x0
x29:         0    0x0
x30:         0    0x0
x31:         0    0x0


*******EXECUTION******
arguments and results are as (register,value) with register being -1 for not a register

  PC&order     inst.    result      arg1      arg2 clk&stall
------------------------------------------------------------
    (0, 1)        lw    (1, 0)    (0, 0)   (-1, 0)    (5, 0)
    (4, 2)        lw    (2, 0)    (0, 0)   (-1, 8)    (7, 1)
    (8, 3)       add    (3, 0)    (1, 0)    (2, 0)    (8, 0)
   (12, 4)        sw  (-1, 24)    (3, 0)    (0, 0)    (9, 0)
   (16, 5)        lw    (4, 0)    (0, 0)  (-1, 16)   (11, 1)
   (20, 6)       add    (5, 0)    (1, 0)    (4, 0)   (12, 0)
   (24, 7)        sw  (-1, 32)    (5, 0)    (0, 0)   (13, 0)


**CLOCKS AND STALLS**
Number of instructions executed:  7
Number of clock cycles:  13
Number of stalls added:  2
```


```
****INSTRUCTIONS****
     0:    lw    x1     0    x0
     4:    lw    x2     8    x0
     8:    lw    x4    16    x0
    12:   add    x3    x1    x2
    16:    sw    x3    24    x0
    20:   add    x5    x1    x4
    24:    sw    x5    32    x0


********DATA********
    24:    0
    25:    0
    26:    0
    27:    0
    32:    0
    33:    0
    34:    0
    35:    0


******REGISTERS*****
x 1:         0    0x0
x 2:         0    0x0
x 3:         0    0x0
x 4:         0    0x0
x 5:         0    0x0
x 6:         0    0x0
x 7:         0    0x0
x 8:         0    0x0
x 9:         0    0x0
x10:         0    0x0
x11:         0    0x0
x12:         0    0x0
x13:         0    0x0
x14:         0    0x0
x15:         0    0x0
x16:         0    0x0
x17:         0    0x0
x18:         0    0x0
x19:         0    0x0
x20:         0    0x0
x21:         0    0x0
x22:         0    0x0
x23:         0    0x0
x24:         0    0x0
x25:         0    0x0
x26:         0    0x0
x27:         0    0x0
x28:         0    0x0
x29:         0    0x0
x30:         0    0x0
x31:         0    0x0


*******EXECUTION******
arguments and results are as (register,value) with register being -1 for not a register

  PC&order     inst.    result      arg1      arg2 clk&stall
------------------------------------------------------------
    (0, 1)        lw    (1, 0)    (0, 0)   (-1, 0)    (5, 0)
    (4, 2)        lw    (2, 0)    (0, 0)   (-1, 8)    (6, 0)
    (8, 3)        lw    (4, 0)    (0, 0)  (-1, 16)    (7, 0)
   (12, 4)       add    (3, 0)    (1, 0)    (2, 0)    (8, 0)
   (16, 5)        sw  (-1, 24)    (3, 0)    (0, 0)    (9, 0)
   (20, 6)       add    (5, 0)    (1, 0)    (4, 0)   (10, 0)
   (24, 7)        sw  (-1, 32)    (5, 0)    (0, 0)   (11, 0)


**CLOCKS AND STALLS**
Number of instructions executed:  7
Number of clock cycles:  11
Number of stalls added:  0

```

These two examples may be expected to give stalls but do not because of the forwarding
```
****INSTRUCTIONS****
     0:   sub    x2    x1    x3
     4:   and   x12    x2    x5
     8:    or   x13    x6    x2
    12:   add   x14    x2    x2
    16:    sw   x15   100    x2


********DATA********
   100:    0
   101:    0
   102:    0
   103:    0


******REGISTERS*****
x 1:         0    0x0
x 2:         0    0x0
x 3:         0    0x0
x 4:         0    0x0
x 5:         0    0x0
x 6:         0    0x0
x 7:         0    0x0
x 8:         0    0x0
x 9:         0    0x0
x10:         0    0x0
x11:         0    0x0
x12:         0    0x0
x13:         0    0x0
x14:         0    0x0
x15:         0    0x0
x16:         0    0x0
x17:         0    0x0
x18:         0    0x0
x19:         0    0x0
x20:         0    0x0
x21:         0    0x0
x22:         0    0x0
x23:         0    0x0
x24:         0    0x0
x25:         0    0x0
x26:         0    0x0
x27:         0    0x0
x28:         0    0x0
x29:         0    0x0
x30:         0    0x0
x31:         0    0x0


*******EXECUTION******
arguments and results are as (register,value) with register being -1 for not a register

  PC&order     inst.    result      arg1      arg2 clk&stall
------------------------------------------------------------
    (0, 1)       sub    (2, 0)    (1, 0)    (3, 0)    (5, 0)
    (4, 2)       and   (12, 0)    (2, 0)    (5, 0)    (6, 0)
    (8, 3)        or   (13, 0)    (6, 0)    (2, 0)    (7, 0)
   (12, 4)       add   (14, 0)    (2, 0)    (2, 0)    (8, 0)
   (16, 5)        sw (-1, 100)   (15, 0)    (2, 0)    (9, 0)


**CLOCKS AND STALLS**
Number of instructions executed:  5
Number of clock cycles:  9
Number of stalls added:  0
```

```
****INSTRUCTIONS****
     0:   add    x1    x1    x2
     4:   add    x1    x1    x3
     8:   add    x1    x1    x4


********DATA********


******REGISTERS*****
x 1:         0    0x0
x 2:         0    0x0
x 3:         0    0x0
x 4:         0    0x0
x 5:         0    0x0
x 6:         0    0x0
x 7:         0    0x0
x 8:         0    0x0
x 9:         0    0x0
x10:         0    0x0
x11:         0    0x0
x12:         0    0x0
x13:         0    0x0
x14:         0    0x0
x15:         0    0x0
x16:         0    0x0
x17:         0    0x0
x18:         0    0x0
x19:         0    0x0
x20:         0    0x0
x21:         0    0x0
x22:         0    0x0
x23:         0    0x0
x24:         0    0x0
x25:         0    0x0
x26:         0    0x0
x27:         0    0x0
x28:         0    0x0
x29:         0    0x0
x30:         0    0x0
x31:         0    0x0


*******EXECUTION******
arguments and results are as (register,value) with register being -1 for not a register

  PC&order     inst.    result      arg1      arg2 clk&stall
------------------------------------------------------------
    (0, 1)       add    (1, 0)    (1, 0)    (2, 0)    (5, 0)
    (4, 2)       add    (1, 0)    (1, 0)    (3, 0)    (6, 0)
    (8, 3)       add    (1, 0)    (1, 0)    (4, 0)    (7, 0)


**CLOCKS AND STALLS**
Number of instructions executed:  3
Number of clock cycles:  7
Number of stalls added:  0

```

This example implements a simple loop, alongside some arbitrary operation. ıt is not rekated to the lecture slides:

```
****INSTRUCTIONS****
     0:  addi    x5    x0     5
     4:  addi    x1    x1     1
     8:   bne    x1    x5    -4
    12:  jalr    x1    16    x6
    16:   add    x0    x0    x0
    20:   add    x0    x0    x0
    24:   add    x0    x0    x0
    28:    sw    x1     4    x0
    32:    lw    x5     4    x0
    36:  srli    x5    x5     2


********DATA********
     4:    16
     5:    0
     6:    0
     7:    0


******REGISTERS*****
x 1:        16    0x10
x 2:         0    0x0
x 3:         0    0x0
x 4:         0    0x0
x 5:         4    0x4
x 6:         0    0x0
x 7:         0    0x0
x 8:         0    0x0
x 9:         0    0x0
x10:         0    0x0
x11:         0    0x0
x12:         0    0x0
x13:         0    0x0
x14:         0    0x0
x15:         0    0x0
x16:         0    0x0
x17:         0    0x0
x18:         0    0x0
x19:         0    0x0
x20:         0    0x0
x21:         0    0x0
x22:         0    0x0
x23:         0    0x0
x24:         0    0x0
x25:         0    0x0
x26:         0    0x0
x27:         0    0x0
x28:         0    0x0
x29:         0    0x0
x30:         0    0x0
x31:         0    0x0


*******EXECUTION******
arguments and results are as (register,value) with register being -1 for not a register

  PC&order     inst.    result      arg1      arg2 clk&stall
------------------------------------------------------------
    (0, 1)      addi    (5, 5)    (0, 0)   (-1, 5)    (5, 0)
    (4, 2)      addi    (1, 1)    (1, 0)   (-1, 1)    (6, 0)
    (8, 3)       bne  (-1, -4)    (1, 1)    (5, 5)    (9, 2)
    (4, 4)      addi    (1, 2)    (1, 1)   (-1, 1)   (10, 0)
    (8, 5)       bne  (-1, -4)    (1, 2)    (5, 5)   (13, 2)
    (4, 6)      addi    (1, 3)    (1, 2)   (-1, 1)   (14, 0)
    (8, 7)       bne  (-1, -4)    (1, 3)    (5, 5)   (17, 2)
    (4, 8)      addi    (1, 4)    (1, 3)   (-1, 1)   (18, 0)
    (8, 9)       bne  (-1, -4)    (1, 4)    (5, 5)   (21, 2)
   (4, 10)      addi    (1, 5)    (1, 4)   (-1, 1)   (22, 0)
   (8, 11)       bne   (-1, 4)    (1, 5)    (5, 5)   (25, 2)
  (12, 12)      jalr   (1, 16)    (6, 0)  (-1, 16)   (27, 1)
  (28, 13)        sw   (-1, 4)   (1, 16)    (0, 0)   (28, 0)
  (32, 14)        lw   (5, 16)    (0, 0)   (-1, 4)   (30, 1)
  (36, 15)      srli    (5, 4)   (5, 16)   (-1, 2)   (31, 0)


**CLOCKS AND STALLS**
Number of instructions executed:  15
Number of clock cycles:  31
Number of stalls added:  12
```

This example implements recursive function calls and is a variation of the RISC-V factorial example in the lecture notes:

```
****INSTRUCTIONS****
     0:  addi    sp    x0  1000
     4:  addi   x10    x0     5
     8:  addi    sp    sp   -16
    12:    sw    x1     8    sp
    16:    sw   x10     0    sp
    20:  addi    x5   x10    -1
    24:   bge    x5    x0    16
    28:  addi   x10    x0     1
    32:  addi    sp    sp    16
    36:  jalr    x0     0    x1
    40:  addi   x10   x10    -1
    44:   jal    x1   -36
    48:  addi    x6   x10     0
    52:    lw   x10     0    sp
    56:    lw    x1     8    sp
    60:  addi    sp    sp    16
    64:   add   x10   x10    x6
    68:  jalr    x0     0    x1


********DATA********
   904:    0
   905:    0
   906:    0
   907:    0
   912:    48
   913:    0
   914:    0
   915:    0
   920:    1
   921:    0
   922:    0
   923:    0
   928:    48
   929:    0
   930:    0
   931:    0
   936:    2
   937:    0
   938:    0
   939:    0
   944:    48
   945:    0
   946:    0
   947:    0
   952:    3
   953:    0
   954:    0
   955:    0
   960:    48
   961:    0
   962:    0
   963:    0
   968:    4
   969:    0
   970:    0
   971:    0
   976:    48
   977:    0
   978:    0
   979:    0
   984:    5
   985:    0
   986:    0
   987:    0
   992:    0
   993:    0
   994:    0
   995:    0


******REGISTERS*****
x 1:        48    0x30
x 2:       920    0x398
x 3:         0    0x0
x 4:         0    0x0
x 5:4294967295    0xffffffff
x 6:         0    0x0
x 7:         0    0x0
x 8:         0    0x0
x 9:         0    0x0
x10:         1    0x1
x11:         0    0x0
x12:         0    0x0
x13:         0    0x0
x14:         0    0x0
x15:         0    0x0
x16:         0    0x0
x17:         0    0x0
x18:         0    0x0
x19:         0    0x0
x20:         0    0x0
x21:         0    0x0
x22:         0    0x0
x23:         0    0x0
x24:         0    0x0
x25:         0    0x0
x26:         0    0x0
x27:         0    0x0
x28:         0    0x0
x29:         0    0x0
x30:         0    0x0
x31:         0    0x0


*******EXECUTION******
arguments and results are as (register,value) with register being -1 for not a register

  PC&order     inst.    result      arg1      arg2 clk&stall
------------------------------------------------------------
    (0, 1)      addi (2, 1000)    (0, 0)(-1, 1000)    (5, 0)
    (4, 2)      addi   (10, 5)    (0, 0)   (-1, 5)    (6, 0)
    (8, 3)      addi  (2, 984) (2, 1000) (-1, -16)    (7, 0)
   (12, 4)        sw   (-1, 8)    (1, 0)  (2, 984)    (8, 0)
   (16, 5)        sw   (-1, 0)   (10, 5)  (2, 984)    (9, 0)
   (20, 6)      addi    (5, 4)   (10, 5)  (-1, -1)   (10, 0)
   (24, 7)       bge  (-1, 16)    (5, 4)    (0, 0)   (13, 2)
   (40, 8)      addi   (10, 4)   (10, 5)  (-1, -1)   (14, 0)
   (44, 9)       jal   (1, 48)    (0, 0) (-1, -36)   (16, 1)
   (8, 10)      addi  (2, 968)  (2, 984) (-1, -16)   (17, 0)
  (12, 11)        sw   (-1, 8)   (1, 48)  (2, 968)   (18, 0)
  (16, 12)        sw   (-1, 0)   (10, 4)  (2, 968)   (19, 0)
  (20, 13)      addi    (5, 3)   (10, 4)  (-1, -1)   (20, 0)
  (24, 14)       bge  (-1, 16)    (5, 3)    (0, 0)   (23, 2)
  (40, 15)      addi   (10, 3)   (10, 4)  (-1, -1)   (24, 0)
  (44, 16)       jal   (1, 48)    (0, 0) (-1, -36)   (26, 1)
   (8, 17)      addi  (2, 952)  (2, 968) (-1, -16)   (27, 0)
  (12, 18)        sw   (-1, 8)   (1, 48)  (2, 952)   (28, 0)
  (16, 19)        sw   (-1, 0)   (10, 3)  (2, 952)   (29, 0)
  (20, 20)      addi    (5, 2)   (10, 3)  (-1, -1)   (30, 0)
  (24, 21)       bge  (-1, 16)    (5, 2)    (0, 0)   (33, 2)
  (40, 22)      addi   (10, 2)   (10, 3)  (-1, -1)   (34, 0)
  (44, 23)       jal   (1, 48)    (0, 0) (-1, -36)   (36, 1)
   (8, 24)      addi  (2, 936)  (2, 952) (-1, -16)   (37, 0)
  (12, 25)        sw   (-1, 8)   (1, 48)  (2, 936)   (38, 0)
  (16, 26)        sw   (-1, 0)   (10, 2)  (2, 936)   (39, 0)
  (20, 27)      addi    (5, 1)   (10, 2)  (-1, -1)   (40, 0)
  (24, 28)       bge  (-1, 16)    (5, 1)    (0, 0)   (43, 2)
  (40, 29)      addi   (10, 1)   (10, 2)  (-1, -1)   (44, 0)
  (44, 30)       jal   (1, 48)    (0, 0) (-1, -36)   (46, 1)
   (8, 31)      addi  (2, 920)  (2, 936) (-1, -16)   (47, 0)
  (12, 32)        sw   (-1, 8)   (1, 48)  (2, 920)   (48, 0)
  (16, 33)        sw   (-1, 0)   (10, 1)  (2, 920)   (49, 0)
  (20, 34)      addi    (5, 0)   (10, 1)  (-1, -1)   (50, 0)
  (24, 35)       bge  (-1, 16)    (5, 0)    (0, 0)   (53, 2)
  (40, 36)      addi   (10, 0)   (10, 1)  (-1, -1)   (54, 0)
  (44, 37)       jal   (1, 48)    (0, 0) (-1, -36)   (56, 1)
   (8, 38)      addi  (2, 904)  (2, 920) (-1, -16)   (57, 0)
  (12, 39)        sw   (-1, 8)   (1, 48)  (2, 904)   (58, 0)
  (16, 40)        sw   (-1, 0)   (10, 0)  (2, 904)   (59, 0)
  (20, 41)      addi(5, 4294967295)   (10, 0)  (-1, -1)   (60, 0)
  (24, 42)       bge   (-1, 4)(5, 4294967295)    (0, 0)   (63, 2)
  (28, 43)      addi   (10, 1)    (0, 0)   (-1, 1)   (64, 0)
  (32, 44)      addi  (2, 920)  (2, 904)  (-1, 16)   (65, 0)
  (36, 45)      jalr   (0, 40)   (1, 48)   (-1, 0)   (67, 1)


**CLOCKS AND STALLS**
Number of instructions executed:  45
Number of clock cycles:  67
Number of stalls added:  18
```
