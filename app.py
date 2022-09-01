# Copyright (c) 2021 Bruce Han. All Rights Reserved.
# Author: Bruce Han, hantingxiang@gmail.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import os
import sys
import time
import re
import argparse
import asyncio
from langdetect import detect
import numpy as np
import cv2
from PIL import Image
import datetime


async def cpp_infer(image_path, mode="universal"):
    if mode == "handwritten":
        proc = await asyncio.create_subprocess_shell(
            f"ppocr system --image_dir {image_path} --det_db_unclip_ratio 2.2 --rec_model_dir ./inference/hwrec/ --char_list_file ./hw_chars.txt --rec_mode 1",
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
        )
    else:
        proc = await asyncio.create_subprocess_shell(
            f"ppocr system --image_dir {image_path}",
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE
            )
    # stdout, stderr = await proc.communicate()
    run = proc.communicate()

    try:
        stdout, stderr = await asyncio.wait_for(run, 10)
    except asyncio.TimeoutError:
        return False, "Timeout", None, None

    exec_ok = True
    det_time = None
    rec_time = None
    results = []

    if "Aborted" in stderr.decode():
        exec_ok = False

    if stdout:
        stdout_str = stdout.decode()
        lines = stdout_str.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                if len(line.split('\t')) == 3:
                    predict, score, coord = line.split('\t')
                    score_value = eval(score.split()[-1])
                    if score_value > 0.7:
                        results.append((predict, score, coord))
                else:
                    if "Detection elapse: " in line:
                        det_time = line[18: -1]
                    elif "Recognition elapse: " in line:
                        rec_time = line[20: -1]
                    elif "Abort" in line:
                        exec_ok = False
                        break
    
    return exec_ok, results, det_time, rec_time


def check_path(image_path):
    if not os.path.exists(image_path):
        return None
    image_list = []
    if os.path.isfile(image_path) and image_path.split('.')[-1] in ['jpg', 'png', 'bmp', 'jpeg', 'rgb', 'tif', 'tiff', 'gif', 'GIF']:
        image_list.append(image_path)
        return image_list
    if os.path.isdir(image_path):
        for img_path in os.listdir(image_path):
            if img_path.split('.')[-1] in ['jpg', 'png', 'bmp', 'jpeg', 'rgb', 'tif', 'tiff', 'gif', 'GIF']:
                image_list.append(img_path)
        return image_list


def save_upload(image_bytes, image_temp_dir):
    if not os.path.exists(image_temp_dir):
        os.makedirs(image_temp_dir)
    image = Image.open(io.BytesIO(image_bytes))
    save_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    save_path = os.path.join(image_temp_dir, f"{save_name}.png")
    image.save(save_path)
    return save_path


def universal(results):
    result_list = []
    for result, _, _ in results:
        result_list.append(result)
    result_string = '\n'.join(result_list)
    return result_string


def document(results):
    table = {ord(en): ord(cn) for en, cn in zip(u',.:;?!\'"()[]', u'，。：；？！’”（）【】')}
    start_x_list = []
    end_x_list = []
    height_list = []
    for i, (_, _, coord) in enumerate(results):
        coords = coord.split()[1:]
        start_x = int(coords[0])
        end_x = int(coords[2])
        height = int(coords[-1]) - int(coords[1])
        start_x_list.append((i, start_x))
        end_x_list.append((i, end_x))
        height_list.append(height)

    if len(height_list) != 0:
        avg_height = np.mean(height_list)
    else:
        avg_height = 32

    start_x_list.sort(key=lambda x: x[1])
    end_x_list.sort(key=lambda x: x[1], reverse=True)

    # 找到缩进行
    start_x_groups = []
    start_x_temp_group = []
    last_start_x = start_x_list[0][1]
    for i, (idx, x) in enumerate(start_x_list):
        if x - last_start_x > avg_height * 1.5:
            start_x_groups.append(start_x_temp_group)
            start_x_temp_group = [(idx, x)]
            last_start_x = x
        else:
            start_x_temp_group.append((idx, x))
    start_x_groups.append(start_x_temp_group)

    # 找到分段行
    end_x_groups = []
    end_x_temp_group = []
    last_end_x = end_x_list[0][1]
    for i, (idx, x) in enumerate(end_x_list):
        if last_end_x - x > avg_height * 2:
            end_x_groups.append(end_x_temp_group)
            end_x_temp_group = [(idx, x)]
            last_end_x = x
        else:
            end_x_temp_group.append((idx, x))
    end_x_groups.append(end_x_temp_group)

    # 缩进指示
    normal_start_x = max(start_x_groups, key=len)
    indentation = [1] * len(results)
    for idx, x in normal_start_x:
        indentation[idx] = 0  # 不缩进
    
    # 换行指示
    normal_end_x = max(end_x_groups, key=len)
    full_line = [0] * len(results)
    for idx, x in normal_end_x:
        full_line[idx] = 1

    paragraphs = []
    buffer = ''
    for i, (result, _, _) in enumerate(results):
        result = result.split('\t')[0]
        try:
            lang = detect(result)
            if detect(result) == "zh-cn":
                result = result.translate(table)
        except Exception as e:
            print(e)
            print(result)
        if indentation[i] and not full_line[i]:  # 新起一段
            if buffer != '':
                paragraphs.append(buffer)
            result = "    " + result
            paragraphs.append(result)
            buffer = ''
        elif indentation[i] and full_line[i]:
            if buffer != '':
                paragraphs.append(buffer)
                buffer = ''
            result = "    " + result
            buffer += result
        else:
            if i == 0:
                buffer += result
            else:
                if full_line[i-1]:
                    buffer += result
                else:
                    paragraphs.append(buffer)
                    buffer = result
    if buffer != '':
        paragraphs.append(buffer)

    return '\n'.join(paragraphs)


def idcard(results):
    result_string = ''
    name, gender, nation, birth, address, id_ = None, None, None, None, None, None
    for predict, _, _ in results:
        result_string += predict
    result_string = result_string.replace(' ', '')

    # 姓名
    res = re.search(r"姓名(.*)性别", result_string)
    if res and len(res.group(1)) != 0:
        name = res.group(1)
    else:
        res = re.search(r"(.*)姓名", result_string)
        if res:
            name = res.group(1)
    # 性别
    index = result_string.find("性别")
    if index != -1:
        gender = result_string[index+2]
    # 民族
    res = re.search(r"民族(.*)出生", result_string)
    if res:
        nation = res.group(1)
    # 出生
    res = re.search(r"出生(.*)日", result_string)
    if res:
        birth = res.group(1) + '日'
    # 住址
    res = re.search(r"住址(.*)公民", result_string)
    if res:
        address = res.group(1)
    # 身份证号
    res = re.search(r"号码([0-9xX]*)", result_string)
    if res:
        id_ = res.group(1)

    return {"姓名": name, "性别": gender, "民族": nation, "出生": birth, "住址": address, "公民身份证号码": id_}


def handwritten_pre_local(image_path, img_temp_dir):
    gray = cv2.imread(image_path, 0)
    adjusted = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
    adjusted = cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)
    img_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + "_hw.jpg"
    img_path = os.path.join(img_temp_dir, img_name)
    # print(img_path)
    cv2.imwrite(img_path, adjusted)

    return img_path


def handwritten_pre_online(image_bytes, img_temp_dir):
    image = Image.open(io.BytesIO(image_bytes))  # Pillow Image
    if image.mode == "RGB":
        image = image.convert('L')
    gray = np.asarray(image)
    adjusted = cv2.convertScaleAbs(gray, alpha=1.5, beta=20)
    adjusted = cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)
    img_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f') + "_hw.jpg"
    img_path = os.path.join(img_temp_dir, img_name)
    # print(img_path)
    cv2.imwrite(img_path, adjusted)

    return img_path
