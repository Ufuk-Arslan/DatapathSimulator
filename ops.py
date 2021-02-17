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
