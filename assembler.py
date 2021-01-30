import os
import sys

def which(a,l):
	return sum([int(a==l[i])*i for i in range(len(l))])

def registerIdx(text):
	if(text=="zero"):
		return 0
	elif(text=="ra"):
		return 1
	elif(text=="sp"):
		return 2
	elif(text=="gp"):
		return 3
	elif(text=="tp"):
		return 4
	elif(text=="fp"):
		return 8
	elif(text[0]=="x"):
		res=int(text[1:])
		if(res>31 or res<0):
			raise Exception("invalid register index")
		return res
	elif(text[0]=="a"):
		res=int(text[1:])
		if(res>7 or res<0):
			raise Exception("invalid \"a\" register index")
		return res+10
	elif(text[0]=="s"):
		res=int(text[1:])
		if(res>11 or res<0):
			raise Exception("invalid \"s\" register index")
		if(res<3):
			return res+8
		else:
			return res+16
	elif(text[0]=="t"):
		res=int(text[1:])
		if(res>6 or res<0):
			raise Exception("invalid \"t\" register index")
		if(res<3):
			return 5		#BUT WHY!!!
		else:
			return res+25
	else:
		raise Exception("Invalid register syntax")


def Rtype(tokens,opcode):
	op=tokens[0]
	opidx=which(op,["add","sub","xor","or","and","sll","srl","sra","slt","sltu"])
	funct3=["000","000","100","110","111","001","101","101","010","011"][opidx]
	funct7=(["0000000","0100000"]+["0000000"]*5+["0100000"]+["0000000"]*2)[opidx]
	rd="{0:>05b}".format(registerIdx(tokens[1]))
	rs1="{0:>05b}".format(registerIdx(tokens[2]))
	rs2="{0:>05b}".format(registerIdx(tokens[3]))
	return funct7+rs2+rs1+funct3+rd+opcode


def Itype(tokens,opcode):
	op=tokens[0]
	opidx=which(op,["addi","xori","ori","andi","slli","srli","srai","slti","sltui","lb","lh","lw","lbu","lhu","jalr","ecall","ebreak"])
	funct3=["000","100","110","111","001","101","101","010","011","000","001","010","100","101","000","000","000"][opidx]
	imm="{0:>012b}".format(int(tokens[3]))#DOES NOT WORK FOR NEGATIVES AND TOO LARGE NUMBERS
	rd="{0:>05b}".format(registerIdx(tokens[1]))
	rs1="{0:>05b}".format(registerIdx(tokens[2]))
	return imm+rs1+funct3+rd+opcode

def Stype(tokens,opcode):
	pass
def Btype(tokens,opcode):
	pass
def Utype(tokens,opcode):
	pass
def Jtype(tokens,opcode):
	pass


def instruction(inputLine): #does not implement pseudoinstructions and labels
	text=str(inputLine).replace(","," ").rsplit()
	op=text[0]
	if(any([op==i for i in ["add","sub","xor","or","and","sll","srl","sra","slt","sltu"]])):
		return Rtype(text,"0110011")
	elif(any([op==i for i in ["addi","xori","ori","andi","slli","srli","srai","slti","sltui"]])):
		return Itype(text,"0010011")
	elif(any([op==i for i in ["lb","lh","lw","lbu","lhu"]])):
		return Itype(text,"0000011")
	elif(any([op==i for i in ["sb","sh","sw"]])):
		return Stype(text,"0100011")
	elif(any([op==i for i in ["beq","bne","blt","bge","bltu","bgeu"]])):
		return Btype(text,"1100011")
	elif(op=="jal"):
		return Jtype(text,"1101111")
	elif(op=="jalr"):
		return Itype(text,"1100111")
	elif(op=="lui"):
		return Utype(text,"0110111")
	elif(op=="auipc"):
		return Utype(text,"0010111")		
	elif(op=="ecall" or op=="ebreak"):
		return Itype(text,"1110011")
	else:
		raise Exception("Invalid instruction name")


inp=open(sys.argv[1],"r")
out=open(sys.argv[2],"w")

while (True):
	line=inp.readline()
	if not line:
		break
	print(instruction(line),file=out)
inp.close()
out.close()