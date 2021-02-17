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

