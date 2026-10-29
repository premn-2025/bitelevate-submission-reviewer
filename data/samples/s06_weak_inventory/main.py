import csv, sys
def main():
    f = sys.argv[1]
    data = []
    try:
        r = csv.reader(open(f))
        for row in r:
            data.append(row)
    except:
        print("error")
    total = 0
    low = []
    names = {}
    for i in range(1, len(data)):
        row = data[i]
        try:
            q = int(row[2])
            p = float(row[3])
        except:
            continue
        total = total + q * p
        if q < 5:
            low.append(row[1])
        if row[1] in names:
            names[row[1]] = names[row[1]] + q
        else:
            names[row[1]] = q
        if q == 0:
            print("out of stock", row[1])
        if p > 1000:
            print("expensive", row[1])
        if row[0] == "":
            print("missing id on line", i)
    print("total value", total)
    print("low stock", low)
    best = None
    for k in names:
        if best is None or names[k] > names[best]:
            best = k
    print("most stocked", best)
    for k in names:
        print(k, names[k])
    count = 0
    for k in names:
        count = count + 1
    print("items", count)
    avg = 0
    if count > 0:
        avg = total / count
    print("avg value per item", avg)
    for row in data[1:]:
        if len(row) < 4:
            print("short row", row)
    print("done")
main()
