from pythonds.basic.queue import Queue
def hotPotato(newlist,num):
    simqueue = Queue()
    for name in newlist:
        simqueue.enqueue(name)
        while simqueue.size() > 1:
            for i in range(num):
                simqueue.enqueue(simqueue.dequeue())#实现一次传递
            simqueue.dequeue()
            return simqueue.dequeue()
#测试
print(hotPotato(["bill","david",'susan','jane','kent','brad'],2))