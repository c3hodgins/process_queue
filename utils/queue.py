from datetime import datetime

class QueueNode():
    def __init__(self, filename):
        if filename != "DUMMY" or filename != "HEAD":
            self.next = None
            self.process_name = filename
            self.start_time = datetime.now()
        
    def dump(self):
        return self.process_name, self.start_time

class TaskQueue():
    def __init__(self, max_num_tasks = 10):
        self.max_num_tasks = 10
        self.head = None
        self.tail = None
        self.length = 0
        
    def __len__(self):
        return self.length
    
    def push(self, node: QueueNode):
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self.length+=1
        print(node.dump())
        
    def l_push(self, node: QueueNode):
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            node.next = self.head
            self.head = node
        self.length+=1
        print(node.dump())
    
    def r_pop(self):
        if self.head is None:
            return None
        if self.head.next is None:
            val = self.head
            self.head = None
            self.tail = None
            self.length-=1
            return val
        
        dummy = self.head
        while(dummy.next.next is not None):
            dummy = dummy.next
        val = dummy.next
        dummy.next = None
        
        self.length-=1
        return val
    
    def pop(self):
        if self.head is None:
            return None
        val = self.head
        self.head = self.head.next
        if self.head is None:
            self.tail = None
        self.length -= 1
        return val
            
    
    def dump(self):
        if self.head is not None and self.head.next is not None:
            dummy = self.head
            while(dummy.next is not None):
                print(dummy.dump())
                dummy = dummy.next
        