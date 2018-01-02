# coding: u8

from __future__ import print_function, unicode_literals

import colorsys
import itertools
import math
import os
import os.path as osp
import platform
import random
import subprocess
import time
import traceback
#图片处理类
from PIL import Image, ImageDraw


# 选择Python的版本
if int(platform.python_version_tuple()[0]) == 2:
    range = xrange
    zip = itertools.izip
else:
    defalut_range = range
    range = lambda *args: defalut_range(*(int(arg) for arg in args))


class Otsu(object):

    def __init__(self, path, debug=False):
        #打开 adb 截图的图片进行分析路径。
        self.im = Image.open(path)

        self.w, self.h = self.im.size
        self.pixels = self.im.load()
        self.draw = ImageDraw.Draw(self.im)

        self.hero_pos = self.find_hero()
        print('hero pos:', self.hero_pos)

        is_hero_on_left = self.hero_pos[0] < self. w / 2

        bg_hsv = self.get_background_hsv()
        print('background hsv:', bg_hsv)

        top_most, lr_most = self.find_most(is_hero_on_left, bg_hsv)
        print('top most pos：', top_most)
        print('left/right most pos', lr_most)

        self.center_pos = top_most[0], lr_most[1]
        print('center pos', self.center_pos)

        self.draw_pos(self.hero_pos)
        self.draw_pos(top_most)
        self.draw_pos(lr_most)
        self.draw_pos(self.center_pos)

        cx, cy = self.center_pos
        hx, hy = self.hero_pos
        self.draw.line((cx, cy, hx, hy), fill=(0, 255, 0), width=8)
        self.im.save(path + '.debug.png')

        if debug:
            self.im.show()
            self.erase_background(bg_hsv)
            self.im.show()
    #选择小人位置
    def find_hero(self):
        hero_poses = []
        for y in range(self.h / 3, self.h * 2 / 3):
            for x in range(self.w):
                # is purple
                if self.pixels[x, y] == (56, 56, 97, 255):
                    hero_poses.append((x, y))
        # 获取平均值
        return [int(sum(i) / len(i)) for i in zip(*hero_poses)]

    def rgb_to_hsv(self, r, g, b, a=255):
        h, s, v = colorsys.rgb_to_hsv(r / 255., g / 255., b / 255.)
        return int(h * 255.), int(s * 255.), int(v * 255.)

    def get_background_hsv(self):
        #除了背景颜色方便处理
        bg_color = self.pixels[10, 800]
        return self.rgb_to_hsv(*bg_color)

    def erase_background(self, bg_hsv):
        for y in range(self.h / 4, self.h * 2 / 3):
            for x in range(self.w):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if self.is_same_color(h, s, v, bg_hsv):
                    self.im.putpixel((x, y), (0, 0, 0))
                else:
                    self.im.putpixel((x, y), (255, 255, 255))

    def find_most(self, is_hero_on_left, bg_hsv):
        hero_radius = 25
        if is_hero_on_left:
            # 在右上角开始扫描
            from_x = self.w - 1
            to_x = self.hero_pos[0] + hero_radius
            step = -1
        else:
            # 在左下角开始扫描
            from_x = 0
            to_x = self.hero_pos[0] - hero_radius
            step = 1

        from_y, to_y = self.h / 4, self.hero_pos[1]

        top_most = self.find_top_most(bg_hsv, from_x, to_x, from_y, to_y, step)
        lr_most = self.find_lr_most(bg_hsv, from_x, to_x, from_y, to_y, step)
        return top_most, lr_most
    # 扫描出 右上角的点
    def find_top_most(self, bg_hsv, from_x, to_x, from_y, to_y, step):
        for y in range(from_y, to_y):
            for x in range(from_x, to_x, step):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if not self.is_same_color(h, s, v, bg_hsv):
                    return x, y
    # 扫描出 左下角的点
    def find_lr_most(self, bg_hsv, from_x, to_x, from_y, to_y, step):
        for x in range(from_x, to_x, step):
            for y in range(from_y, to_y):
                h, s, v = self.rgb_to_hsv(*self.pixels[x, y])
                if not self.is_same_color(h, s, v, bg_hsv):
                    return x, y

    def is_same_color(self, h, s, v, bg_hsv):
        bg_h, bg_s, bg_v = bg_hsv
        return (abs(h - bg_h) < 15) and (abs(s - bg_s) < 20)

    def draw_pos(self, pos, color=(0, 255, 0)):
        x, y = pos
        r = 25
        self.draw.ellipse((x, y, x + r, y + r), fill=color, outline=color)

    def get_holding(self):
        line_length = int(math.sqrt(
            pow(self.center_pos[0] - self.hero_pos[0], 2) + \
            pow(self.center_pos[1] - self.hero_pos[1], 2)
        ))

        length_time = line_length * 1.5

        holding = min(950, max(length_time, 300))

        print('length, duration, holding: ', line_length, length_time, holding)
        print()

        return int(holding)


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
            stdin=subprocess.PIPE, shell=True)
    stdout, stderr = p.communicate()
    if stderr:
        print(stderr)
    p.wait()
    return stdout, stderr



screenshot_director = '/tmp/wechat_micro_jump_game_screenshot'
if not osp.exists(screenshot_director):
    os.makedirs(screenshot_director)


jump_times = itertools.count(0)
while True:
    try:
        debug = False

        if debug:
          
            fn = '6.png'
            fp = osp.join(screenshot_director, fn)
        else:
            fn = str(next(jump_times)) + '.png'
            fp = osp.join(screenshot_director, fn)

            run_cmd('adb shell screencap -p /sdcard/s.png')
            run_cmd('adb pull /sdcard/s.png {}'.format(fp))

        print(fp)

        otsu = Otsu(fp, debug=debug)
        holding = otsu.get_holding()

        if debug:
            raise KeyboardInterrupt
        else:
            
            rand_x = lambda: random.randint(0, otsu.w)
            rand_y = lambda: random.randint(0, otsu.h * 3 / 4)
            x1, y1 = rand_x(), rand_y()
            x2, y2 = rand_x(), rand_y()

            run_cmd('adb shell input swipe {0} {1} {2} {3} {4}'.format(
                x1, y1, x2, y2, holding))
            time.sleep(2)
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        traceback.print_exc()
time.sleep(2)