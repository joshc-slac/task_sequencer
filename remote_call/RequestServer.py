import socket
import threading

import signal


class RequestServer:
  def __init__(self, cond_var=threading.Condition()):
    self.cv = cond_var

    self.do_work = False
    self.work_thread = threading.Thread(target=self.socket_loop, args=())
    self.setup_socket()
    self.message_queue_lock = threading.Lock()
    self.message_queue = []  # python "queue" just have to treat it like one

  # private member functions
  def setup_socket(self):
    self.HOST = "localhost"
    self.PORT = 11312
    # setup listner socket
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind((self.HOST, self.PORT))
    self.sock.settimeout(3)

  def socket_loop(self):
    # work loop gate
    while (self.do_work):
      # print("Listening for new connection")
      # listening work
      self.sock.listen(1)
      try:
        self.conn_sock, self.conn_addr = self.sock.accept()  # blocking call, see 10 second timeout init setup_socket
      except socket.timeout:
        # print("WARNING: Socket timeout detected, relistening for connection")
        continue

      with self.conn_sock:
          print('Connected by', self.conn_addr)
          while True:
              data = self.conn_sock.recv(1024)

              # enqueue bytes as string. fwiw python sucks gimme c baby
              if data.decode('utf-8') != "":
                self.message_queue_lock.acquire()
                self.message_queue.append(str(data.decode()))
                self.message_queue_lock.release()
              else:
                print("WARNING: discarding empty string")

              if not data:
                with self.cv:
                  self.cv.notify()
                break
              self.conn_sock.sendall(data)

  # public member function
  def start_work(self):
    if (self.do_work is False):
      self.do_work = True
      self.work_thread.start()
    else:
      print("WARNING: already doing work")
      return

  def stop_work(self, *args):
    if (self.do_work is True):
      self.do_work = False
      self.sock.close()
      self.work_thread.join()
    else:
      print("WARNING: not doing any work, meaningless call")
      return

  def get_message(self):
    if len(self.message_queue) == 0:
      print("WARNING: message length zero  not popping")
      return str()
    else:
      self.message_queue_lock.acquire()
      print(self.message_queue)
      mess = self.message_queue.pop(0)
      self.message_queue_lock.release()
      return mess

  def __del__(self):
    # close socket
    self.sock.close()


if __name__ == "__main__":
  r = RequestServer()
  signal.signal(signal.SIGINT, r.stop_work)
  r.start_work()
