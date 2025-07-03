import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from PIL import Image
# from tqdm import tqdm


# outputs/pics/maxquality.png shouldn't get edited
# backup in case: https://media.discordapp.net/stickers/1374624356373626900.webp?size=160&quality=lossless

# todo
#  find palette
#  threshold to palette with an arbitrary range, doesn't matter much
#  create mockup output of what the image would look like on the site afterwards
#  customise palette
#  repeat manually :D

def pixel_art():
    folder = 'outputs/pics/nelldoro/'
    pic = "maxquality.png"
    dims = (32, 32)

    scaling_img(folder + pic, dims)
    img = mpimg.imread(folder + pic.split('.png')[0] + f'{dims[0]}x{dims[1]}.png')

    armies = ['OS', 'BM', 'GE', 'YC', 'BH', 'RF', 'GS', 'BD', 'AB', 'JS', 'CI',
              'PC', 'TG', 'PL', 'AR', 'WN', 'AA', 'NE', 'SC']
    palette = make_palette(armies)
    selection = convert_to_palette(img, palette)
    np.savetxt(folder + "atteem1.txt", selection, fmt='%.0f')
    tiles = ['plain', 'mtn', 'forest', 'river', 'road', 'sea', 'shoal', 'reef', 'pipe', 'miss', 'tele', 'neu', *armies]
    # print(tiles)
    dic = {}
    for i in range(len(tiles)):
        dic.update({i: tiles[i]})
    print(dic)
    # guide = [tiles[e] for e in selection]
    # np.savetxt(folder + "atteem2.csv", guide)

    # plt.imsave(folder + "outputatteem1.png", img)


def scaling_img(imgpath, dims):
    img = Image.open(imgpath)
    resized_img = img.resize(dims)
    resized_img.save(imgpath.split('.png')[0] + '32x32.png')


def make_palette(armies):
    palette = np.zeros([12 + len(armies), 3])
    palette[0, :] = [160, 239, 77]  # plains 14[168, 240, 80]2[104, 232, 56]
    palette[1, :] = [186, 189, 84]  # mtn 5[152, 104, 48]4[248, 232, 144]1[208,128,48]6[168, 240, 80]
    palette[2, :] = [115, 224, 50]  # forest 4[168, 240, 80]7[104, 232, 56]5[88, 200, 16]
    palette[3, :] = [66, 115, 248]  # river 11[56, 120, 248]5[88, 104, 248]
    palette[4, :] = [184, 176, 168]  # road
    palette[5, :] = [88, 104, 248]  # sea
    palette[6, :] = [112, 176, 248]  # shoal
    palette[7, :] = [125, 143, 210]  # reef6[88, 104, 248]4[112, 176, 248]2[56, 120, 248]2[208, 128, 48]2[248, 232, 144]
    palette[8, :] = [176, 144, 136]  # pipe
    palette[9, :] = [255, 255, 255]  # missile
    palette[10, :] = [0, 0, 0]  # tele
    palette[11:, :] = palette_country_decisions(armies)
    return palette

def palette_country_decisions(armies):
    palette6 = np.zeros([1 + len(armies), 6])
    palette6[0, :] = [248, 248, 248, 104, 80, 56]  # neutral [248, 248, 248] [104, 80, 56]

    palette6[1, :] = [248, 72, 48, 104, 80, 56]  # OS
    palette6[2, :] = [88, 104, 248, 104, 80, 56]  # BM
    palette6[3, :] = [88, 200, 16, 104, 80, 56]  # GE
    palette6[4, :] = [240, 240, 8, 104, 80, 56]  # YC
    palette6[5, :] = [96, 72, 160, 79, 48, 112]  # BH
    palette6[6, :] = [208, 70, 93, 119, 11, 35]  # RF
    palette6[7, :] = [129, 127, 128, 86, 92, 114]  # GS
    palette6[8, :] = [207, 179, 158, 147, 82, 50]  # BD
    palette6[9, :] = [252, 163, 57, 104, 80, 56]  # AB
    palette6[10, :] = [166, 182, 153, 104, 80, 56]  # JS
    palette6[11, :] = [54, 86, 209, 20, 43, 135]  # CI
    palette6[12, :] = [255, 102, 204, 104, 80, 56]  # PC
    palette6[13, :] = [68, 172, 163, 10, 89, 82]  # TG
    palette6[14, :] = [164, 70, 210, 110, 25, 153]  # PL
    palette6[15, :] = [157, 175, 18, 96, 107, 13]  # AR
    palette6[16, :] = [190, 137, 136, 169, 63, 63]  # WN
    palette6[17, :] = [109, 186, 242, 62, 121, 204]  # AA
    palette6[18, :] = [87, 74, 74, 47, 40, 40]  # NE
    palette6[19, :] = [137, 168, 188, 60, 74, 111]  # SC

    palette3 = np.zeros([1 + len(armies), 3])
    for i in range(int(palette6.shape[0])):
        palette3[i, :] = [(palette6[i, 0] * 9 / 16) + (palette6[i, 3]  * 7 / 16),
                          (palette6[i, 1] * 9 / 16) + (palette6[i, 4]  * 7 / 16),
                          (palette6[i, 2] * 9 / 16) + (palette6[i, 5]  * 7 / 16)]
        # palette3[i, :] = [palette6[i, 0], palette6[i, 1], palette6[i, 2]]  # todo decide if this is better
    return palette3


def convert_to_palette(img, palette):
    selection = np.zeros([len(img[:, 0, 0]), len(img[0, :, 0])])
    for x in range(len(img[:, 0, 0])):
        for y in range(len(img[0, :, 0])):
            nums = img[x, y, :]
            nums = nums * 255
            if nums[0] != 0:
                pass
            distances = np.sqrt(np.square(nums[0] - palette[:, 0]) +
                                np.square(nums[1] - palette[:, 1]) +
                                np.square(nums[2] - palette[:, 2]))
            selection[x, y] = np.argmin(distances)
    return selection


def thresholder():
    original_pic = mpimg.imread("Q1/edges.JPG")
    threshold_pic_mean = np.zeros_like(original_pic)
    for rgb in range(3):
        threshold_value = average(original_pic[:, :, rgb], 'mean')
        threshold_pic_mean[:, :, rgb] = (original_pic[:, :, rgb] >= threshold_value)

    threshold_pic_med = np.zeros_like(original_pic)
    for rgb in range(3):
        threshold_value = average(original_pic[:, :, rgb], 'median')
        threshold_pic_med[:, :, rgb] = (original_pic[:, :, rgb] >= threshold_value)

    threshold_pic_mode = np.zeros_like(original_pic)
    for rgb in range(3):
        threshold_value = average(original_pic[:, :, rgb], 'mode')
        threshold_pic_mode[:, :, rgb] = (original_pic[:, :, rgb] >= threshold_value)

    threshold_pic_range = np.zeros_like(original_pic)
    for rgb in range(3):
        threshold_value = average(original_pic[:, :, rgb])
        threshold_pic_range[:, :, rgb] = (original_pic[:, :, rgb] >= threshold_value)

    plt.imsave("Q1/threshold_in.png", original_pic)
    plt.imsave("Q1/threshold_out_mean.png", threshold_pic_mean * 255)
    plt.imsave("Q1/threshold_out_med.png", threshold_pic_med * 255)
    plt.imsave("Q1/threshold_out_mode.png", threshold_pic_mode * 255)
    plt.imsave("Q1/threshold_out_range.png", threshold_pic_range * 255)
    # greyscale_pic = np.rint(greyscale_pic / np.amax(greyscale_pic))


def average(i, average_type=None):  # returns the specified average (defaults to halfway through the range)
    if average_type is not None:
        if average_type == 'mean':
            return np.mean(i)
        if average_type == 'median':
            return np.median(i)
        if average_type == 'mode':
            mode = None
            mode_store = 0
            for j in np.arange(start=0, stop=(255 + 1), step=1):
                this_j = np.sum(i == j)
                if mode is None or this_j > mode_store:
                    mode_store = this_j
                    mode = j
            return mode
        else:
            raise ValueError(f"You must supply a valid average type. '{average_type}' is not valid")
    return (255 + 0) / 2  # if a threshold method isn't provided, take half the range
