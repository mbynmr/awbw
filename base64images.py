import base64
from PIL import Image
from io import BytesIO
from eloplot import page_getter
from tqdm import tqdm
# from imageio import imread
# image = imread(s)
import base64
import requests


def converter():

    # page = page_getter(s)
    # resultbox = str(page.find("div", class_="resultBox").next.next)
    with open('outputs/gifMaporiginal.txt', 'r', encoding="utf8") as originalmap:
        with open('outputs/gifMap.txt', 'w') as newmap:
            for i, line in tqdm(enumerate(originalmap)):
                if len(line.split('"')) < 5:
                    newmap.write(line)
                    continue

                # ":SaluteGirl_YC_Inf:": "https://cdn.discordapp.com/emojis/1100180778232578088.png?size=96",

                if len(line.split('"')) != 5:
                    print('funky line')  # todo \"Hawke\" makes the split awks
                s = line.split('"')[-2]
                # page = page_getter(s)
                # imgg = page.find("img")
                # with open(line.split('"')[-2], "rb") as image_file:
                #     data = base64.b64encode(image_file.read())
                d = str(get_as_base64(s))
                d = d.split("'")[1]
                newline = '        "' + line.split('"')[1] + '": ' + d + ',\n'
                newmap.write(newline)
                # newmap.write(str(len(line.split('"'))) + '\n')

                # im = Image.open(BytesIO(base64.b64decode(data)))
                # im.save('image1.png', 'PNG')

                # table = page.find("div", class_="tableWrapper").find("table", class_="sortable").find("tbody")
                # str(item.next.next)


def get_as_base64(url):
    return base64.b64encode(requests.get(url).content)
