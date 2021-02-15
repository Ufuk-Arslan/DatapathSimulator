import ctypes

class regfile:
	def __init__(self):
		self.storage=[0 for i in range(32)]
	def __getitem__(self,key):
		if(key==0):
			return 0
		else:
			return self.storage[key]
	def __setitem__(self,key,value):
		if(key==0):
			return
		else:
			self.storage[key]=value


class datamemory:
	def __init__(self):
		self.storage=dict()

	def get(self,index):#DOES NOT SIGN EXTEND
		try:
			return self.storage[index]
		except:
			return 0
	def getword(self,index):
		if(index%4!=0):
			raise Exception("Misaligned memory read address for word!")
			return
		else: #little endian
			return self.get(index)+(self.get(index+1)<<8)+(self.get(index+2)<<16)+(self.get(index+3)<<24)
	def gethalf(self,index):#DOES NOT SIGN EXTEND
		if(index%2!=0):
			raise Exception("Misaligned memory read address for half!")
			return
		else: #little endian
			return self.get(index)+(self.get(index+1)<<8)
	def write(self,index,data):
		self.storage[index]=ctypes.c_uint8(data).value
	def writehalf(self,index,data):
		if(index%2!=0):
			raise Exception("Misaligned memory write address for half!")
			return
		else: #little endian
			self.write(index,data)
			self.write(index+1,data>>8)
	def writeword(self,index,data):
		if(index%4!=0):
			raise Exception("Misaligned memory write address for word!")
			return
		else: #little endian
			self.write(index,data)
			self.write(index+1,data>>8)
			self.write(index+2,data>>16)
			self.write(index+3,data>>24)