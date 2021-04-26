

from pid4nb.zen import zen 



folder = './output/20210421_0'

#zen.create((folder))
#b = zen.read_bucket(folder)    
zen.upload(folder)
#r = zen.get(794114)
    
f2 = zen.file_list(folder)
