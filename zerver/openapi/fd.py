zuliprc = open(".zuliprc","w")
zuliprc.writelines(["[api]\n",
                    "email="  + "\n",
                      "key=" + "\n"
                        "site=",
                       ])
zuliprc.close()
print(zuliprc)