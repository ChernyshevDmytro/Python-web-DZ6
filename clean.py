import pathlib as pl
import asyncio
import aiopath
import aiofiles.os
import re
import os
import shutil
import itertools
from threading import Thread

# Creating normalisation dictionary TRANS
CYRILLIC_SYMBOLS = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяєіїґ"
TRANSLATION = ("a", "b", "v", "g", "d", "e", "e", "j", "z", "i", "j", "k", "l", "m", "n", "o", "p", "r", "s", "t", "u",
               "f", "h", "ts", "ch", "sh", "sch", "", "y", "", "e", "yu", "u", "ja", "je", "ji", "g")

LIST_OF_IMAGES_SUFFIX = ['.JPEG', '.PNG', '.JPG', '.SVG']
LIST_OF_VIDEO_SUFFIX = ['.AVI', '.MP4', '.MOV', '.MKV']
LIST_OF_DOCUMENTS_SUFFIX = ['.DOC', '.DOCX', '.TXT', '.PDF', '.XLSX', '.PPTX']
LIST_OF_AUDIO_SUFFIX = ['.MP3', '.OGG', '.WAV', '.AMR']
LIST_OF_ARCHIVES_SUFFIX = ['.ZIP', '.GZ', '.TAR']
list_of_known_suffix_general = list(itertools.chain(LIST_OF_IMAGES_SUFFIX, LIST_OF_VIDEO_SUFFIX,\
    LIST_OF_DOCUMENTS_SUFFIX, LIST_OF_AUDIO_SUFFIX, LIST_OF_ARCHIVES_SUFFIX))

print (f'I know follow suffix {list_of_known_suffix_general}')


trans = {}
for cyrillic, latin in zip(CYRILLIC_SYMBOLS, TRANSLATION):
    trans[ord(cyrillic)] = latin
    trans[ord(cyrillic.upper())] = latin.upper() 
#print(trans)

# Check if Path exists
def path_verification(path_to_folder):
    path_to_folder=rf'{path_to_folder}'
    number_of_attemps=0
    
    while number_of_attemps<10:
        number_of_attemps+=1 
        path = pl.Path(path_to_folder)
        
        if (not path.exists() or path.is_file()):
            print(f'Please enter the valid path to folder\nYou have {9-number_of_attemps} attempts')
            path_to_folder = input('Enter path to folder:')

        if number_of_attemps==10:
            break         

        if  path.exists():
            valid_path_to_folder=  rf'{path_to_folder}' 
            return valid_path_to_folder

        
# List output of folders and files. Empty folders remove                 
def to_find_files_in_user_path(valid_path_to_folder):       
    founded_files=[]
    founded_folders=[]
    path = pl.Path(valid_path_to_folder) 
                          
    for elements in path.iterdir():     
    
        if elements.is_file():
            pure_path=pl.PurePath(pl.Path(elements))            
            pure_path=str(pure_path)                                       
            path_without_suffix_and_name=pure_path.replace(elements.suffix, '')
            path_without_suffix_and_name=pure_path.replace(elements.name, '')
            elements_name_without_suffix = elements.name.replace(elements.suffix, '')        
            founded_files.append([elements_name_without_suffix, elements.suffix, path_without_suffix_and_name])
                               
 
        if elements.is_dir():            
            founded_folders.append(os.fspath(elements))
            path_to_folder_iterate=pl.Path(elements)
            to_find_files_in_user_path(path_to_folder_iterate)
    #print(founded_files)
    #print(founded_folders)    
    return valid_path_to_folder, founded_files, founded_folders
   

def normalize(founded_files,founded_folders, valid_path_to_folder):     
    
    founded_files_normalized=[]
    founded_folders_normalized=[]
    path_length = len(valid_path_to_folder)+1 
    
    for i in founded_files:
        #print(i)
        if 'archives' in i[2] or 'video' in i[2] or 'audio' in i[2] or 'documents' in i[2] or 'images' in i[2]:
            founded_files_normalized.append([fr"{i[0]}", fr"{i[1]}", fr"{i[2]}"])

        else:    
            a=i[0] 
            a=i[0].translate(trans)
            d=re.sub(r'(\W)', '_', fr"{a}")
            founded_files_normalized.append([fr"{d}", fr"{i[1]}", fr"{i[2]}"])

    for j in founded_folders:

        if 'archives' in j or 'video' in j or 'audio' in j or 'documents' in j or 'images' in j:
            founded_folders_normalized.append(fr'{j}')

        else:
            translated_path=j[path_length:].translate(trans)            
            translated_and_normalized_path=re.sub(r'[^\w^\\]', '_', fr"{translated_path}")
            founded_folders_normalized.append(fr'{j[0:path_length]}{translated_and_normalized_path}')     
          
    return  founded_files_normalized, founded_folders_normalized


async def renaming_finded_files(founded_files_normalized, founded_files):
    
    for  founded_file, founded_file_normalized in zip(founded_files, founded_files_normalized): 
    
        if founded_file[0]!=founded_file_normalized[0]:
            await aiofiles.os.rename( fr'{founded_file[2]}{founded_file[0]}{founded_file[1]}', fr'{founded_file[2]}{founded_file_normalized[0]}{founded_file_normalized[1]}')


async def renaming_finded_folders(founded_folders, founded_folders_normalized):
   
    for  founded_folder, founded_folder_normalized in zip(founded_folders, founded_folders_normalized):
        
        if founded_folder!=founded_folder_normalized:
            #print(founded_folder)
            #print(founded_folder_normalized)
            await aiofiles.os.rename( f'{founded_folder}', f'{founded_folder_normalized}')   


async def moving_pictures_to_separate_folder(founded_files, path_to_folder):
    list_of_images=[]
    for k in founded_files:

        if k[1].upper() in LIST_OF_IMAGES_SUFFIX and fr"{path_to_folder}\images" not in  fr"{k[2]}":            
            list_of_images.append(f"{k[0]}{k[1]}")

            if not await aiopath.AsyncPath(fr"{path_to_folder}\images").exists():
                await aiofiles.os.mkdir(fr'{path_to_folder}\images')

            await aiofiles.os.replace(fr'{k[2]}{k[0]}{k[1]}' , fr"{path_to_folder}\images\{k[0]}{k[1]}")
    print(f"List of images: {list_of_images}")    


async def moving_video_to_separate_folder(founded_files, path_to_folder):
    list_of_video=[]    

    for k in founded_files:
        
        if k[1].upper() in LIST_OF_VIDEO_SUFFIX and fr"{path_to_folder}\images" not in  fr"{k[2]}":            
            list_of_video.append(f"{k[0]}{k[1]}")

            list_of_video.append(f"{k[0]}{k[1]}")
            if not await aiopath.AsyncPath(fr"{path_to_folder}\video").exists():
                await aiofiles.os.mkdir(fr'{path_to_folder}\video')
           
            await aiofiles.os.replace(fr'{k[2]}{k[0]}{k[1]}' , fr"{path_to_folder}\video\{k[0]}{k[1]}")
    print(f"List of video: {list_of_video}") 

async def moving_documents_to_separate_folder(founded_files, path_to_folder):
    list_of_documents=[]    
    for k in founded_files:
        #print(founded_files)
        if k[1].upper() in LIST_OF_DOCUMENTS_SUFFIX and fr"{path_to_folder}\documents" not in fr"{k[2]}":        
            
            list_of_documents.append(f"{k[0]}{k[1]}")
            
            if not await aiopath.AsyncPath(fr"{path_to_folder}\documents").exists():
                await aiofiles.os.mkdir(fr'{path_to_folder}\documents')                
            
            await aiofiles.os.replace(fr'{k[2]}{k[0]}{k[1]}' , fr"{path_to_folder}\documents\{k[0]}{k[1]}")          
    print(f"List of documents: {list_of_documents}")  

    
async def moving_audio_to_separate_folder(founded_files, path_to_folder):
    list_of_audio=[]
    for k in founded_files:
        
        if k[1].upper() in LIST_OF_AUDIO_SUFFIX and fr"{path_to_folder}\audio" not in  fr"{k[2]}":
            list_of_audio.append(f"{k[0]}{k[1]}")

            if not await aiopath.AsyncPath(fr"{path_to_folder}\audio").exists():
                await aiofiles.os.mkdir(fr'{path_to_folder}\audio')
            
            await aiofiles.os.replace(fr'{k[2]}{k[0]}{k[1]}' , fr"{path_to_folder}\audio\{k[0]}{k[1]}")  
    print(f"List of audio: {list_of_audio}")  
 
async def moving_archives_to_separate_folder(founded_files, path_to_folder):
    list_of_archives=[]
    for k in founded_files:
        
        if k[1].upper() in LIST_OF_ARCHIVES_SUFFIX and fr"{path_to_folder}\archives" not in  fr"{k[2]}":
            list_of_archives.append(f"{k[0]}{k[1]}") 

            if not await aiopath.AsyncPath(fr"{path_to_folder}\archives").exists():
               await aiofiles.os.mkdir(fr'{path_to_folder}\archives')            
                        
            shutil.unpack_archive(fr'{k[2]}{k[0]}{k[1]}',  fr"{path_to_folder}\archives\{k[0]}")             
    print(f"List of archives: {list_of_archives}")  


async def moving_other_filesto_separate_folder(founded_files, path_to_folder):
    list_of_unknown_suffix=set()
    list_of_known_suffix=set()
    
    list_of_other_files=[]
    for k in founded_files:
        list_of_known_suffix.add(k[1])

        if 'archives' in k[2] or 'video' in k[2] or 'audio' in k[2] or 'documents' in k[2] or 'images' in k[2]:
            continue

        elif k[1].upper() not in list_of_known_suffix_general:      
            
            list_of_other_files.append(f"{k[0]}{k[1]}")
            
            if not await aiopath.AsyncPath(fr"{path_to_folder}\other_files").exists():
                await aiofiles.os.mkdir(fr'{path_to_folder}\other_files')
            list_of_unknown_suffix.add(k[1])
            
            await aiofiles.os.replace(fr'{k[2]}{k[0]}{k[1]}' , fr"{path_to_folder}\other_files\{k[0]}{k[1]}")
        elif k[1].upper() in list_of_known_suffix_general:
            list_of_known_suffix.add(k[1])


    print(f"List of other files: {list_of_other_files}") 
    print (f"List of known suffix: {list_of_known_suffix}\nList of unknown suffix: {list_of_unknown_suffix}")       


async def del_empty_dirs(valid_path_to_folder):
    path =  aiopath.AsyncPath(valid_path_to_folder)
    
    for items in os.scandir(path):
        item_path = os.path.join(path, items)

        if await aiofiles.os.path.isdir(item_path):
            await del_empty_dirs(item_path)

            if not os.scandir(item_path) and 'archives' not in item_path and 'video' not in item_path\
            and 'audio' not in item_path and 'documents' not in item_path and 'images' not in item_path:
                await aiofiles.os.rmdir(item_path)


collect_functions = [moving_pictures_to_separate_folder, moving_video_to_separate_folder, moving_documents_to_separate_folder, moving_audio_to_separate_folder, moving_archives_to_separate_folder, moving_other_filesto_separate_folder]




async def futures(futures):

    await asyncio.gather(*futures)



def clean():
    path_to_folder = input('Enter path to folder:')        
    valid_path_to_folder=path_verification(path_to_folder) 
    valid_path_to_folder, founded_files, founded_folders =  to_find_files_in_user_path(valid_path_to_folder)
    #print(founded_files)     
    founded_files_normalized, founded_folders_normalized= normalize(founded_files,founded_folders, valid_path_to_folder)
    list_of_rename_futures = [renaming_finded_files(founded_files_normalized, founded_files), renaming_finded_folders(founded_folders, founded_folders_normalized)]
  
     
    for i in collect_functions: 
        list_of_rename_futures.append(i(founded_files_normalized, valid_path_to_folder))    
    list_of_rename_futures.append(del_empty_dirs(valid_path_to_folder))
    asyncio.run(futures(list_of_rename_futures))

    

clean()
