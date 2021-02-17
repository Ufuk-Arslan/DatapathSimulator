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
