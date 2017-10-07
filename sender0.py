import socket
import pickle
import random
import sys
import time

def beginConnection(log,starttime,s,receiver_host_ip,receiver_port):
  #3 Way Handshake
  value = {'SYN':True,'ACK':False,'FIN':False,'seq_num':random.randint(0,10000),'ack_num':0,'data':''}
  message = pickle.dumps(value)
  s.sendto(message,(receiver_host_ip, receiver_port)) #sends SYN
  #log writing chunk--------------------------------------------
  curtime = time.time()*1000
  curtime = curtime-starttime
  log.write('snd\t'+str(curtime)+'\tS\t'+str(value['seq_num'])+'\t'+str(len(value['data']))+'\t'+str(value['ack_num'])+'\n')
  #-------------------------------------------------------------
  print ('SYN packet sent')
  message, client = s.recvfrom(1024) #reads SYN+ACK
  message = pickle.loads(message)
  #log writing chunk--------------------------------------------
  curtime = time.time()*1000
  curtime = curtime-starttime
  log.write('rcv\t'+str(curtime)+'\tSA\t'+str(message['seq_num'])+'\t'+str(len(message['data']))+'\t'+str(message['ack_num'])+'\n')
  #-------------------------------------------------------------
  print ('SYN+ACK received')
  if(message['SYN'] == True and message['ACK'] == True):
    value = {'SYN':False,'ACK':True,'FIN':False,'seq_num':message['ack_num'],'ack_num':message['seq_num']+1,'data':''}
    message = pickle.dumps(value)
    s.sendto(message,(receiver_host_ip, receiver_port)) #sends ACK
    #log writing chunk--------------------------------------------
    curtime = time.time()*1000
    curtime = curtime-starttime
    log.write('snd\t'+str(curtime)+'\tA\t'+str(value['seq_num'])+'\t'+str(len(value['data']))+'\t'+str(value['ack_num'])+'\n')
    #-------------------------------------------------------------
    print ('ACK packet sent')
    message = pickle.loads(message)
    return message
    
def fileRead(seq_num,MSS,f):
  EOFFlag = False
  size = 0
  while EOFFlag == False:
    chunk = f.read(MSS)
    size += len(chunk)
    if chunk == '':
      #reached EOF
      EOFFlag = True
      break
    data[seq_num] = chunk
    seq_num += MSS
  return data, size

def endConnection(log,starttime,s,message,receiver_host_ip,receiver_port,totalData,totalSegment,totalDropped,totalRetransmit,totalDuplicate):
  #3 Way FIN
  value = {'SYN':False,'ACK':False,'FIN':True,'seq_num':message['seq_num'],'ack_num':message['ack_num'], 'data':''}
  message = pickle.dumps(value)
  s.sendto(message,(receiver_host_ip,receiver_port))
  #log writing chunk--------------------------------------------
  curtime = time.time()*1000
  curtime = curtime-starttime
  log.write('snd\t'+str(curtime)+'\tF\t'+str(value['seq_num'])+'\t'+str(len(value['data']))+'\t'+str(value['ack_num'])+'\n')
  #-------------------------------------------------------------
  print ('FIN packet sent')
  while 1:
    #empties the buffer until it finds the FIN ACK packet and quits
    message, client = s.recvfrom(1024) #reads SYN+ACK
    message = pickle.loads(message)
    if(message['FIN'] == True and message['ACK'] == True):
      #log writing chunk--------------------------------------------
      curtime = time.time()*1000
      curtime = curtime-starttime
      log.write('rcv\t'+str(curtime)+'\tFA\t'+str(message['seq_num'])+'\t'+str(len(message['data']))+'\t'+str(message['ack_num'])+'\n')
      #-------------------------------------------------------------
      print ('FIN+ACK received')
      value = {'SYN':False,'ACK':True,'FIN':False,'seq_num':message['ack_num'],'ack_num':message['seq_num']+1,'data':''}
      message = pickle.dumps(value)
      s.sendto(message,(receiver_host_ip,receiver_port))
      #log writing chunk--------------------------------------------
      curtime = time.time()*1000
      curtime = curtime-starttime
      log.write('snd\t'+str(curtime)+'\tA\t'+str(value['seq_num'])+'\t'+str(len(value['data']))+'\t'+str(value['ack_num'])+'\n')
      #-------------------------------------------------------------
      print ('ACK packet sent, terminating connection')
      #log endnote writing chunk------------------------------------
      log.write('---------------------------------------------------------------\n')
      log.write('Amount of data transferred: '+str(totalData)+' bytes\n')
      log.write('Number of data segments sent: '+str(totalSegment)+'\n')
      log.write('Number of packets dropped: '+str(totalDropped)+'\n')
      log.write('Number of retransmitted segments: '+str(totalRetransmit)+'\n')
      log.write('Number of duplicate acknowledgements: '+str(totalDuplicate)+'\n')
      s.close()
      f.close()
      log.close()
      print ('Connection terminated')
      sys.exit()


if __name__ == '__main__':#might comment them first, then add as more are implemented
  starttime = time.time()*1000
  #arg reading chunk
  receiver_host_ip = sys.argv[1]
  receiver_port = int(sys.argv[2])
  f = open(sys.argv[3],'r') #use read() to read, argument is number of chars
  MSS = int(sys.argv[4])
  MWS = int(sys.argv[5])
  timeout = float(sys.argv[6])/1000
  pdrop = float(sys.argv[7])
  seed = int(sys.argv[8])
  
  #initialization chunk
  message = '' #initialise message
  EOFFlag = False
  finalACK = False
  goToFin = False
  data = {}
  allSent = False
  totalData = 0
  totalSegment = 0
  totalDropped = 0
  totalRetransmit = 0
  totalDuplicate = 0
  log = open('Sender_log.txt','w')#cleans file of previous content
  log.close()
  log = open('Sender_log.txt','a')
  random.seed(seed)
  #UDP packet structure SYN, ACK, FIN, seq_num, ack_num, data, end_seq_num
  
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  try:
    #3way handshake
    message = beginConnection(log,starttime,s,receiver_host_ip,receiver_port)
    
    #initiate correct seq_num
    start_seq_num = message['seq_num']
    sender_ack_num = message['ack_num']

    #send message here
    while goToFin == False:
      sent = 0
      firstSent = False
      ##data reading module------------------------------------------
      if EOFFlag == False:
        data, size = fileRead(start_seq_num,MSS,f)
        end_seq_num = size+start_seq_num
        EOFFlag = True
      ##-------------------------------------------------------------
      
      ##data sending module------------------------------------------
      for i in range(0,1):
        multiplier = i*MSS
        sequence = start_seq_num+multiplier
        if sequence < end_seq_num and allSent == False:
          value = {'SYN':True,'ACK':False,'FIN':False,'seq_num':sequence,'ack_num':sender_ack_num,'data':data[sequence]}
          message = pickle.dumps(value)
          
          if random.random() > pdrop:
            if i == 0:
              firstSent = True
            s.sendto(message,(receiver_host_ip,receiver_port))
            totalData += len(value['data'])
            totalSegment += 1
            sent += 1
            #log writing chunk--------------------------------------------
            curtime = time.time()*1000
            curtime = curtime-starttime
            log.write('snd\t'+str(curtime)+'\tD\t'+str(value['seq_num'])+'\t'+str(len(value['data']))+'\t'+str(value['ack_num'])+'\n')
            #-------------------------------------------------------------
          else:
            if i == 0:
              firstSent = False
            #PLD module in action
            totalDropped += 1
            #log writing chunk--------------------------------------------
            curtime = time.time()*1000
            curtime = curtime-starttime
            log.write('drop\t'+str(curtime)+'\tD\t'+str(value['seq_num'])+'\t'+str(len(value['data']))+'\t'+str(value['ack_num'])+'\n')
            #-------------------------------------------------------------
          message = pickle.loads(message)
          
        else:
          print ('all packet sent')
          allSent = True
          break
      ##--------------------------------------------------------------
      
      ##ACK checking module-------------------------------------------
      for j in range(0,1):
        #checks acks with the same amount of undropped packets
        s.settimeout(timeout)
        try:
          rec_message,client = s.recvfrom(1024)
          rec_message = pickle.loads(rec_message)
          #log writing chunk--------------------------------------------
          curtime = time.time()*1000
          curtime = curtime-starttime
          log.write('rcv\t'+str(curtime)+'\tA\t'+str(rec_message['seq_num'])+'\t'+str(len(rec_message['data']))+'\t'+str(rec_message['ack_num'])+'\n')

          if allSent == True:
            pass

          if rec_message['ack_num'] == end_seq_num:
            diff = sent-len(value['data'])
            final_size = sent-diff
          else:
            final_size = MSS
          
          if (rec_message['ACK'] == True and rec_message['ack_num'] >= (start_seq_num+final_size) and rec_message['ack_num'] < end_seq_num and firstSent == True):
            start_seq_num = rec_message['ack_num']
          elif (rec_message['ACK'] == True and rec_message['ack_num'] >= (start_seq_num+final_size) and rec_message['ack_num'] == end_seq_num and firstSent == True):
            start_seq_num = rec_message['ack_num']
            goToFin = True
            break
          else:
            #retransmit
            allSent = False
            totalRetransmit += 1
            totalDuplicate += 1
            #retransmit
        
        except socket.timeout:
          #timeouts and retransmit
          allSent = False
          totalRetransmit += 1

    message['seq_num'] = start_seq_num
    #3way fin
    endConnection(log,starttime,s,message,receiver_host_ip,receiver_port,totalData,totalSegment,totalDropped,totalRetransmit,totalDuplicate)

  except socket.error:
    print ('ERROR.\n')
