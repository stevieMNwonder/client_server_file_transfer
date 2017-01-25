#Steven Frisbie 4561991
import os, sys, time, socket, threading, random, select, struct, hashlib

def main():

	timeOut = 10 #amount of time till retransmission

	#server
	if (len(sys.argv) == 3):
		HOST, PORT = sys.argv[1], int(sys.argv[2])
		try: # create the TCP IPv4 server socket
			sSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		except socket.error as msg:
			sSock = None  # Handle exception

		try: #bind socket to port and listen on the socket with a max number of connections at a time being 20
			sSock.bind(('', PORT))
			sSock.listen(20)
		except socket.error as msg:
			sSock = None  # Handle exception

		if sSock is None:
	        	print("Error: cannot open socket")
	        	sys.exit(1)  # If the socket cannot be opened, quit the program.

		print("Server is listening...")

		cSock, addr = sSock.accept()

		while 1:
			result = cSock.recv(512)
			checksum, FILENAME, sequenceNum, lastPacket, data = struct.unpack('40s20sbb450s', result)
			FILENAME = FILENAME.strip(b'\x00')
			FILENAME = FILENAME.decode()
			checksum = checksum.decode()
			data = data.strip(b'\x00')
			hash_object = hashlib.sha1(data)
			hex_dig = hash_object.hexdigest()
			# check if the checksum of the data on the client side is equal to the checksum of the data on this side.
			if (hex_dig == checksum):
				with open(FILENAME, 'w') as f:
					f.write(data.decode())
				print("ACK is transmitted.")
				ack = struct.pack('512s', b'ACK')
				cSock.send(ack)


	#client
	elif (len(sys.argv) == 4):
		HOST, PORT, FILENAME = sys.argv[1], int(sys.argv[2]), sys.argv[3]

		sequenceNum = 0
		byteOffset = 0

		#if the filename provided doesn't exist, let them know.
		if not(os.path.isfile(FILENAME)):
			print("No file named {}".format(FILENAME))
			return

		while 1:
			try:
				cSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			except socket.error as msg:
				cSock = None # Handle exception

			try:
				cSock.connect((HOST, PORT))
			except socket.error as msg:
				cSock = None # Handle exception

			if cSock is None:
				print("Error: cannot open socket")
				sys.exit(1) # If the socket cannot be opened, quit the program.

			#file transfer stuff
			with open(FILENAME, 'rb') as f:
				data = f.seek(byteOffset)
				data = f.read(450)
				while data:
					#create checksum of data on client side
					hash_object = hashlib.sha1(data)
					hex_dig = hash_object.hexdigest()
					checksum = hex_dig.encode()
					lastPacket = 0
					if len(data) < 450:
						lastPacket = 1
					#packs data in a neat little way that you can unpack on the server side
					packet = struct.pack('40s20sbb450s', checksum, FILENAME.encode(), sequenceNum, lastPacket, data)
					cSock.send(packet)
					#resets and initiates a retransmission of the current packet if an ack is not received.
					ready = select.select([cSock], [], [], timeOut)
					if ready[0]:
						otherData = cSock.recv(512).decode()
						otherData = otherData.rstrip(' \t\r\n\0')
						#if an ack is received and it is the last packet then close the socket.
						if otherData == 'ACK' and lastPacket:
							print("Finished Transmission. Closing Socket...")
							cSock.close()
							sys.exit()
						#if an ack is received but it isnt the last packet adjust the sequence number and byte offset in the file in case of reset.
						elif otherData == 'ACK' and not(lastPacket):
							data = f.read(450)
							byteOffset += 449
							sequenceNum += 1
					else:
						print("Timeout! Retransmitting...")


	#if not 3 or 4 args presented, then tell them this.
	else:
		print("Must enter three arguments to launch the server or four arguments to launch the client.")
		return

main()