# GLOBAL VARIABLES (code smell)
data = []
result = 0


def process(x, y):
    global result
    temp = 0

    # magic numbers
    if x > 10:
        temp = x * 42
    else:
        temp = x * 42

    # duplicate code
    for i in range(len(y)):
        if y[i] % 2 == 0:
            result += y[i]

    for i in range(len(y)):
        if y[i] % 2 == 0:
            result += y[i]

    # deep nesting
    for i in range(len(y)):
        for j in range(len(y)):
            for k in range(len(y)):
                if y[i] == y[j]:
                    if y[j] == y[k]:
                        if y[i] > 0:
                            print("found something")

    # unused variable
    unused = 12345

    # inefficient string concatenation
    s = ""
    for i in range(100):
        s = s + str(i)

    # bad naming
    a = 5
    b = 6
    c = a + b

    # dead code
    if False:
        print("this will never run")

    # poor exception handling
    try:
        z = x / 0
    except:
        pass

    return result


def main():
    nums = [1,2,3,4,5,6,7,8,9,10]

    # repeated logic
    sum1 = 0
    for i in nums:
        sum1 += i

    sum2 = 0
    for i in nums:
        sum2 += i

    print(process(5, nums))
    print(sum1)
    print(sum2)


main()