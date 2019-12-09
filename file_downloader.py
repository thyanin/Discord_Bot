	
import requests
import urllib
import concurrent.futures
import riot

url = 'https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/champion-icons/'
urls = []

def fill_urls():
    for value in riot.data_champ['data'].values():
        urls.append(url + value['key'] + '.png')


def download_image(url):
    img_bytes = requests.get(url).content
    name = riot.get_champion_name_by_id(int(url[101:-4]))
    with open(f'./champ-emoji/{name}.png', 'wb') as img_file:
        img_file.write(img_bytes)
        print(f'{url[101:]} was downloaded...')


def start_download():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(download_image, urls)
   
#fill_urls()
#start_download()