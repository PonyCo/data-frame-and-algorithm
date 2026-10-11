from pythonds.basic.stack import Stack
def baseConverter(decNumber,base):
    digits = "0123456789ABCDEF"#进制识别，共可识别到十五个进制
    remstack = Stack()
    while decNumber > 0:
        rem = decNumber % base
        remstack.push(rem)
        decNumber = decNumber // base
    newString = ""
    while not remstack.isEmpty():
        newString = newString + digits[remstack.pop()]
    return newString
#测试
print(baseConverter(25,2))
print(baseConverter(25,16))