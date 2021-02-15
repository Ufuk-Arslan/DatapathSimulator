import ops
import mem
import sys


class machine:
	def __init__(self,filename):
		self.instmem=dict()
		self.datamem=mem.datamemory()
		self.reg=mem.regfile()
		self.dump=list()
		addr=int(0)
		inp=open(filename,"r")
		##digest the input lines to instmem
		while(True):
			line=inp.readline()
			if not line:
				break
			text=str(line).replace(","," ").replace("("," ").replace(")"," ").rsplit()#["add","x5","x0","x1"]
			self.instmem[addr]=text
			addr+=4
		self.PC=0
		self.counter=0
	def instruction(self,inputLine): #does not implement pseudoinstructions and labels
		text=self.instmem[self.PC]#["add","x5","x0","x1"]
		op=text[0]
		self.counter+=1
		if(any([op==i for i in ["add","sub","xor","or","and","sll","srl","sra","slt","sltu"]])):
			#Rtype
			d=self.regIdx(text[1])
			s1=self.regIdx(text[2])
			arg1=self.reg[s1]
			s2=self.regIdx(text[3])
			arg2=self.reg[s2]
			result=getattr(ops,"op"+op)(arg1,arg2)
			self.reg[d]=result
			self.dump.append([(self.PC,self.counter),op,(d,result),(s1,arg1),(s2,arg2),(-1,-1)])
			self.PC+=4
		elif(any([op==i for i in ["addi","xori","ori","andi","slli","srli","srai","slti","sltui"]])):
			#Itype
			d=self.regIdx(text[1])
			s1=self.regIdx(text[2])
			arg1=self.reg[s1]
			s2=-1
			arg2=int(text[3])
			immop=op[:len(op)-1]
			result=getattr(ops,"op"+immop)(arg1,arg2)
			self.reg[d]=result
			self.dump.append([(self.PC,self.counter),op,(d,result),(s1,arg1),(s2,arg2),(-1,-1)])
			self.PC+=4
		elif(any([op==i for i in ["lb","lh","lw","lbu","lhu"]])):#I HAVE DOUBTS CHECK AGAIN
			#Like Itype
			d=self.regIdx(text[1])
			s1=self.regIdx(text[3])
			arg1=self.reg[s1]
			s2=-1
			arg2=int(text[2])
			location=arg1+arg2
			result=getattr(ops,"op"+op)(self.datamem,location)
			self.reg[d]=result
			self.dump.append([(self.PC,self.counter),op,(d,result),(s1,arg1),(s2,arg2),(-1,-1)])
			self.PC+=4			
		elif(any([op==i for i in ["sb","sh","sw"]])):
			#Stype
			s1=self.regIdx(text[1])
			s2=self.regIdx(text[3])
			arg1=self.reg[s1]
			arg2=self.reg[s2]
			immptr=int(text[2])
			location=immptr+arg2
			result=getattr(ops,"op"+op)(self.datamem,location,arg1)#what will be read from memory later is returned here
			self.dump.append([(self.PC,self.counter),op,(-1,immptr),(s1,arg1),(s2,arg2),(-1,-1)])
			self.PC+=4			
		elif(any([op==i for i in ["beq","bne","blt","bge","bltu","bgeu"]])):
			#Btype
			s1=self.regIdx(text[1])
			s2=self.regIdx(text[2])
			arg1=self.reg[s1]
			arg2=self.reg[s2]
			immptr=int(text[3])
			offset=getattr(ops,"op"+op)(arg1,arg2,immptr)
			self.dump.append([(self.PC,self.counter),op,(-1,offset),(s1,arg1),(s2,arg2),(-1,-1)])
			self.PC+=offset
		elif(op=="jal"):				#TRY THIS
			#Jtype
			d=self.regIdx(text[1])
			offset=int(text[2])
			self.reg[d]=self.PC+4
			self.dump.append([(self.PC,self.counter),op,(d,self.PC+4),(0,0),(-1,offset),(-1,-1)])
			self.PC+=offset
		elif(op=="jalr"):				#TRY THIS
			#Like Itype
			d=self.regIdx(text[1])
			s1=self.regIdx(text[3])
			arg1=self.reg[s1]
			s2=-1
			arg2=int(text[2])
			location=arg1+arg2
			result=self.PC+4
			self.reg[d]=result
			self.dump.append([(self.PC,self.counter),op,(d,result),(s1,arg1),(s2,arg2),(-1,-1)])
			self.PC+=arg1+arg2			
		elif(op=="lui"):				#TRY THIS
			#Utype
			d==self.regIdx(text[1])
			arg1=int(text[2])
			result=arg1<<12
			self.reg[d]=result;
			self.dump.append([(self.PC,self.counter),op,(d,result),(0,0),(-1,arg1),(-1,-1)])
			self.PC+=4
		elif(op=="auipc"):				#TRY THIS
			#Utype
			d==self.regIdx(text[1])
			arg1=int(text[2])
			result=(arg1<<12)+self.PC
			self.reg[d]=result;
			self.dump.append([(self.PC,self.counter),op,(d,result),(0,0),(-1,arg1),(-1,-1)])
			self.PC+=4			
		elif(op=="ecall" or op=="ebreak"):
			#Itype
			pass
		else:
			raise Exception("Invalid instruction name")

	def run(self):
		while(True):
			try:
				inst=self.instmem[self.PC]
			except:
				return
			if(len(inst)==0):
				return
			self.instruction(inst)

	def regIdx(self, text):
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
	def showdump(self):
		print("\n\n********DUMP********")
		for i in self.dump:
			res=""
			for j in i:
				res+="%10s"%(str(j))
			print(res)
	def showprogram(self):
		print("\n\n****INSTRUCTIONS****")
		for i in sorted(self.instmem):
			res=""
			for j in self.instmem[i]:
				res+="%6s"%(str(j))
			print(res)
	def showdata(self):
		print("\n\n********DATA********")
		for i in sorted(self.datamem.storage):
			print(str(i)+"\t:"+str(self.datamem.storage[i]))
	def showregs(self):
		print("\n\n******REGISTERS*****")
		for i in range(1,32):
			print("x%2d:%10d    0x%x"%(i,self.reg[i],self.reg[i]))


mymac=machine(sys.argv[1])
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

#UFUK: x0 registerinde ve immediatelarda(register -1) dependency olmaması lazım, senin kısımda onu kontrol eder misin?
