import imghdr
import os
import threading
from time import sleep

import bs4
import requests


def exclude_downloaded_wallpapers():
    """Исключает загруженные обои."""
    with open('excluded_wallpapers.txt', 'r+') as f:
        excluded_wallpapers = f.read().split('\n')
        excluded_num = 0
        for wallpaper in wallhaven_new:
            if wallpaper[:6] not in excluded_wallpapers:
                f.write(wallpaper + '\n')
                excluded_num += 1

        print('Исключено:', excluded_num)


def image(soup):
    """Получает изображение."""
    image_url = soup.select('#wallpaper')[0]['src']
    image_res = requests.get(image_url)

    return image_res


def download_image(image_file, image_res):
    """Загружает изображение."""
    with open(image_file, 'wb') as f:
        for chunk in image_res.iter_content(100_000):
            f.write(chunk)


def download_wallpapers(page):
    global total_loaded
    global general_url_images
    toplist_url = f'https://wallhaven.cc/toplist?page={page}'
    res = requests.get(toplist_url)
    soup = bs4.BeautifulSoup(res.text, features='html.parser')

    # Получение URL-адреса каждого изображения.
    images_links = [
        a['href'][len(general_url_images):] for a in soup.find_all('a', {'class': 'preview'})
    ]

    for link in images_links:
        if link in excluded_wallpapers:
            # Если изображение в списке исключенных обоев, то продолжаем со следующего цикла.
            continue

        image_file = os.path.join(download_path, os.path.basename(link))

        sleep(1)
        try:
            res = requests.get(general_url_images + link)
            res.raise_for_status()
        except requests.HTTPError:
            print('unloaded wallpaper: ' + general_url_images + link)
            sleep(1)
            continue

        soup = bs4.BeautifulSoup(res.text, features='html.parser')

        sleep(1)
        download_image(image_file, image(soup))
        total_loaded += 1

    print(f'Page {page} is done'.center(30, '-'))


if __name__ == '__main__':
    print("""
    ║╦║ ╔╗ ║ ║ ║║ ╔╗ ╗╔ ╔═ ║║
    ║║║ ╠╣ ║ ║ ╠╣ ╠╣ ║║ ╠═ ╬║
    ╚╩╝ ║║ ╚ ╚ ║║ ║║ ╚╝ ╚═ ║╬
    """)

    # Сохраняет обои в папке new.
    download_path = '/home/aitmyrza/Wallhaven/new/'
    os.makedirs(download_path, exist_ok=True)

    total_loaded = 0
    general_url_images = 'https://wallhaven.cc/w/'

    with open('excluded_wallpapers.txt') as f:
        """Получает список исключенных обоев."""
        excluded_wallpapers = f.read().split('\n')

    download_threads = []
    for i in range(1, 6):
        download_thread = threading.Thread(target=download_wallpapers, args=[i])
        download_threads.append(download_thread)
        download_thread.start()

    # Ожидание завершения всех потоков выполнения.
    for download_thread in download_threads:
        download_thread.join()

    print(f'\nВсего загружено: {total_loaded}')

    wallhaven_new = os.listdir(download_path)
    exclude_downloaded_wallpapers()

    for wallpaper in wallhaven_new:
        """Добавляет тип к названиям обоев."""
        if wallpaper.endswith('.jpg') or wallpaper.endswith('.png'):
            continue

        img_png = imghdr.what(download_path + wallpaper)
        if img_png == 'png':
            os.rename(download_path + wallpaper, download_path + wallpaper + '.png')
        else:
            os.rename(download_path + wallpaper, download_path + wallpaper + '.jpg')
