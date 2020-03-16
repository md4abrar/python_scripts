number_shoes = int(raw_input("Number of shoes"))
shoe_number = list(input("shoes number 6,7,8 "))
cus = int(raw_input("Number of customers"))


Earning = 0

for i in range(1, cus + 1 ):
    s , p = input("Enter size, price")  
    if s in shoe_number:
       print ("Yeah Shoe sold")
       Earning = Earning + p 
       print ("Your earning till now {}".format(Earning))
       shoe_number.remove(s)
       number_shoes = number_shoes - 1
    else:
        print ("Shoes not available")

print (Earning)