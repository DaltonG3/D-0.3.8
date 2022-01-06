from genericpath import exists
import os, hashlib, calendar, time, shutil, math, pathlib
from telethon import TelegramClient, events, sync, utils
from telethon.tl import types
from FastTelethon import download_file, upload_file
from config import *
from scripts import *

timestamp = calendar.timegm(time.gmtime())
print("backup iniziato alle",timestamp)

def main():
    old_db_digest = "d41d8cd98f00b204e9800998ecf8427e"
    total_errors = []
    total_errors_files = []
    var_total_error_files = []
    print("ottengo la lista dei file presenti...")
    listOfFiles = getListOfFiles(dirName) # Get the list of all files in directory tree at given path
    n_file_total = len(listOfFiles) #conto quanti elementi ci sono in listoffiles
    print("All Elements Found == "+str(n_file_total))
    n_file_current = 1
    files_in_datastore = get_files_from_datastore() #ottengo i file gia caricati
    if debug == 1: print("listofffiles ==", listOfFiles)
    if debug == 1: print("n_file_total", n_file_total)
    for elem in listOfFiles:  #per ogni file....
        try: #in caso di errore passo al file successivo
            is_divisible = n_file_current % step == 0 #upload datastore every step file...
            if is_divisible == True:
                db_digest = get_md5("d41d8cd98f00b204e9800998ecf8427e")

                if old_db_digest != db_digest:
                    upload_datastore_func()
                old_db_digest = db_digest
            epoch_localfile, dirpath_without_root, nomefile, dimension = obtain_info(elem)
            if debug == 1: print ("epoch_localfile ==",epoch_localfile)
            if debug == 1: print("Elemento ==", dirpath_without_root)
            print("nomefile ==", nomefile)
            elementi_in_datastore = search_in_array(dirpath_without_root,files_in_datastore) #numerico
            if debug == 1: print("search in array ==", elementi_in_datastore)
            if elementi_in_datastore > 0: #ho tovato almeno un file con lo stesso nome
                files_present = search_in_datastore(dirpath_without_root) #ottengo la lista dei file che risulta presente
                 #1 o 0 ottengo l'informazione, se è un file nuovo
                found = 0 
                for file_present in files_present:
                    is_newer = check_if_newer(file_present, epoch_localfile)
                    if is_newer == 1 :
                        if debug == 1: print ("is newer!!")
                        digest = get_md5(elem)
                        is_file_present = search_in_array(digest, files_in_datastore)
                        if debug == 1:  print("is file present 1e34 ==", is_file_present)
                        if is_file_present > 0:
                            if debug == 1: print("md5 trovato!! Devo aggiornare il percorso")
                            replace_path(digest, dirpath_without_root, timestamp, epoch_localfile)
                            found=1
                    else:
                        if debug == 1: print ("is older or equal!!")
                        found = 1
                if found == 0:
                    if debug == 1: print("upload1...")
                    digest = get_md5(elem)
                    upload(elem, dimension, nomefile,digest,timestamp,epoch_localfile,dirpath_without_root, n_file_current, n_file_total)
                    if debug == 1: print("after")
            else: #non ho trovato file caricati
                digest = get_md5(elem)
                if debug == 1: print ("digest ==", digest)
                is_file_present = search_in_array(digest, files_in_datastore)
                if is_file_present > 0:
                    if debug == 1: print("md5 trovato!! Devo aggiornare il percorso")
                    if debug == 1: print(digest, dirpath_without_root, timestamp, epoch_localfile)
                    replace_path(digest, dirpath_without_root, timestamp, epoch_localfile)
                    update_is_local(digest, "yes")
                else:
                    if debug == 1: print("upload2...")
                    upload(elem, dimension, nomefile,digest,timestamp,epoch_localfile,dirpath_without_root, n_file_current, n_file_total)
            print("File",n_file_current,"di", n_file_total)
            print("")
            n_file_current += 1
        except Exception as e:
            total_errors.append(e)
            var_total_error_files = nomefile + "/" + dirpath_without_root
            total_errors_files.append(var_total_error_files)
            print("Errore! == "+str(e))
            pass
if __name__ == '__main__':
    main()
print("----------------------------------------------------------------------------------------------------")
print("Verifico la sincronia")
print("")
with client:
    md5_in_remote=client.loop.run_until_complete(main_remote_md5())
'''
datastore_array=[]
with open("d41d8cd98f00b204e9800998ecf8427e") as search:
    for line in search:
        line = line.rstrip()  # remove '\n' at end of line
        datastore_array.append(line)
'''
for string in md5_in_remote:
    if ">>digest_cache<<" not in string:
        if debug == 1: print ("line in verifica ==" ,string)
        datastore_elements = search_in_datastore(string)
        if debug == 1: print("datastore elements ==", datastore_elements)
        if datastore_elements is not None:
            for element in datastore_elements:
                if debug == 1: print("digest_cache == not in line")
                path_tmp = re.search('>>file<<(.*)>>timestamp<<', element)
                path = path_tmp.group(1)
                if debug == 1: print ("path == ", path)
                md5_tmp = re.search('>>md5<<(.*)>>file<<', element)
                md5 = md5_tmp.group(1)
                is_local = get_is_file_present(element)
                if debug == 1: print("is_local ==", is_local)
                if path is not None:
                    if is_local == "yes":
                        esiste = check_if_exists(dirName+path)
                        if debug == 1: print("exists ==", esiste)
                        if esiste == 1:
                            if os_name == "Windows":
                                if has_hidden_attribute(dirName+path) == True and hidden_files == 1:
                                    update_is_local(md5, "no")
                                    pass
                                else:
                                    epoch = get_epoch(element)
                                    epoch_localfile = get_last_time_modified(dirName+path)
                                    if debug == 1: print("if epoch", epoch,"<", epoch_localfile)
                                    if int(epoch) < epoch_localfile:
                                        update_is_local(md5, "no")
                            if os_name == "Linux":
                                non_aggiungere = 0
                                fullPath = dirName+path
                                var = fullPath.split("/")
                                for elem in var:
                                    if elem != "":
                                        if elem[0] in character_sets:
                                            update_is_local(md5, "no")
                                if non_aggiungere == 1:
                                    pass
                                else:
                                    epoch = get_epoch(element)
                                    epoch_localfile = get_last_time_modified(dirName+path)
                                    if debug == 1: print("if epoch", epoch,"<", epoch_localfile)
                                    if int(epoch) < epoch_localfile:
                                        update_is_local(md5, "no")
                        if esiste == 0:
                            update_is_local(md5, "no")
    else: #digest_cache not in string
            md5 = get_digest_cache(string) #
            if debug == 1: print("digest_cache ==", md5)
            datastore_element = search_in_datastore(md5)
            for element in datastore_element:
                if ">>digest_cache<<" not in element:
                    if debug == 1: print("element ==",element)
                    is_local = get_is_file_present(element)
                    path = get_path(element)
                    esiste=check_if_exists(dirName+path)
                    if esiste == 1:
                        if has_hidden_attribute(dirName+path) == True and hidden_files == 1:
                            update_is_local(md5, "no")
                        else:    
                            update_is_local(md5, "yes")
                    else:
                        update_is_local(md5,"no")
upload_datastore_func()


# aggiungere possibilità di ripristino per file duplicati
# velocizzare il download in ripristino se possibile
# ottimizzare i log

#D-0.3.4

#aggiunta possibilità di escludere i file nascosti
