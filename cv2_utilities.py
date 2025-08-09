#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import inspect
import re
from typing import cast

import numpy as np
import cv2
import PIL
from PIL import Image

try:
    from logit import pv
except ImportError:
    from pyutilities.logit import pv


def show_image(image: cv2.typing.MatLike):
    for line in inspect.getframeinfo(inspect.currentframe().f_back)[3]:
        # print(line)
        m = re.search(r'\bimgShow\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)', line)
        if m:
            title = m.group(1)

    cv2.imshow(title, image)
    _ = cv2.waitKey(0)


def read_image(impath: str, flags: int = cv2.IMREAD_UNCHANGED):
    # load the image from disk
    # impath_gbk = impath.encode('gbk')        # unicode转gbk，字符串变为字节数组
    # return cv2.imread(impath_gbk.decode(), cv2.IMREAD_UNCHANGED)    # 字节数组直接转字符串，不解码
    return cv2.imdecode(np.fromfile(impath, dtype=np.uint8), flags)


def scale_image(image: cv2.typing.MatLike, w: int, h: int, interp: int = cv2.INTER_AREA):
    """
    Args:
        interp: cv.INTER_NEAREST    最近邻插值    cv.INTER_LINEAR 	双线性插值
                cv.INTER_CUBIC  三次样条插值      cv.INTER_AREA 	使用像素区域关系重新采样。
    """
    return cv2.resize(image, (w, h), interpolation=interp)


def rotate_image(image: cv2.typing.MatLike, degree: float):
    # Shape of image in terms of pixels.
    h, w = cast(tuple[int, int], image.shape[:2])

    ll = max(w, h)
    cx, cy = (ll // 2, ll // 2)
    padding_w = (ll - w) // 2  # 指定零填充的宽度
    padding_h = (ll - h) // 2  # 指定零填充的高度

    # 在原图像做对称的零填充，使得图片由矩形变为方形
    image_padded: cv2.typing.MatLike = np.zeros(shape=(ll, ll, 3), dtype=np.uint8)
    image_padded[padding_h : padding_h + h, padding_w : padding_w + w, :] = image

    # getRotationMatrix2D creates a matrix needed for transformation.
    # - (cX, cY): 旋转的中心点坐标
    # - degree: 旋转的度数，正度数表示逆时针旋转，而负度数表示顺时针旋转。
    # - 1.0：旋转后图像的大小，1.0原图，2.0变成原来的2倍，0.5变成原来的0.5倍
    rm = cv2.getRotationMatrix2D((cx, cy), degree, 1)
    rotated_padded = cv2.warpAffine(image_padded, rm, (ll, ll))

    image = rotated_padded[
        padding_w : padding_w + w, padding_h : padding_h + h, :
    ]
    return image


def read_exif(fname: str): #定义获取图片exif的方法
    """ Get embedded EXIF data from image file."""
    ret = {}     #创建一个字典对象存储exif的条目如相机品牌：相应品牌这样的数据
    try:
        # image = PIL.Image.open(fname)      # 创建图像对象
        image = Image.open(fname)      # 创建图像对象
        if hasattr(image, '_getexif'):      # 检查图像对象有无_getexif属性，发现也有getexif属性，内容好像差不多
            exif_info = image._getexif()   # 取出img的_getexif属性，这是一个字典对象
            if exif_info is not None:
                for tag, value in exif_info.items():
                    decoded = PIL.ExifTags.TAGS.get(tag, tag)
                    ret[decoded] = value
    except IOError:
        print('IOERROR: ' + fname)
    return ret


def decode_gpsinfo(gps_info):
    """
        00 	VersionID 	int8u[4]
        (tags 0x0001-0x0006 used for camera location according to MWG 2.0.)
        01 	LatitudeRef 	string[2] 	'N' = North 'S' = South
        02 	Latitude 	float64u[3] 
        03 	LongitudeRef 	string[2] 'E' = East 'W' = West
        04 	Longitude 	float64u[3] 	 
        05 	AltitudeRef 	int8u   0 = Above Sea Level 1 = Below Sea Level
            2 = Positive Sea Level (sea-level ref) 3 = Negative Sea Level (sea-level ref)
        06 	Altitude 	float64u 	 
        07 	TimeStamp 	float64u[3] 	(UTC time of GPS fix. When writing,
            date is stripped off if present, and time is adjusted to UTC if it includes a timezone)
        08 	Satellites 	string 	 
        09 	Status 	string[2] 	'A' = Measurement Active 'V' = Measurement Void
        10 	MeasureMode 	string[2] 	2 = 2-Dimensional Measurement 3 = 3-Dimensional Measurement
        11 	DOP 	float64u 	 
        12 	SpeedRef 	string[2] 	'K' = km/h 'M' = mph 'N' = knots
        13 	Speed 	float64u 	 
        14 	TrackRef 	string[2] 	'M' = Magnetic North 'T' = True North
        15 	Track 	float64u 	 
        16 	ImgDirectionRef 	string[2] 	'M' = Magnetic North 'T' = True North
        17 	ImgDirection 	float64u 	 
        18 	MapDatum 	string
        (tags 0x0013-0x001a used for subject location according to MWG 2.0) 	 
        19 	DestLatitudeRef 	string[2]   'N' = North 'S' = South
        20 	DestLatitude 	float64u[3] 	 
        21 	DestLongitudeRef 	string[2] 	'E' = East 'W' = West
        22 	DestLongitude 	float64u[3] 	 
        23 	DestBearingRef 	string[2] 	'M' = Magnetic North 'T' = True North
        24 	DestBearing 	float64u 	 
        25 	DestDistanceRef 	string[2] 	'K' = Kilometers 'M' = Miles 'N' = Nautical Miles
        26 	DestDistance        float64u 	 
        27 	ProcessingMethod 	undef 	   (values of "GPS", "CELLID", "WLAN" or "MANUAL" by the EXIF spec.)
        28 	AreaInformation 	undef 	 
        29 	DateStamp 	string[11] 	(when writing, time is stripped off if present,
                after adjusting date/time to UTC if time includes a timezone. Format is YYYY:mm:dd)
        30 	Differential        int16u 	0 = No Correction 1 = Differential Corrected
        31 	HPositioningError   float64u
    """
    gpsitem_dict = {1: "LatitudeRef", 2: "Latitude", 3: "LongitudeRef", 4: "Longitude",
        5: "AltitudeRef", 6: "Altitude", 7: "TimeStamp", 8: "Satellites", 9: "Status",
        10: "MeasureMode", 11: "DOP", 12: "SpeedRef", 13: "Speed", 14: "TrackRef",
        15: "Track", 16: "ImgDirectionRef", 17: "ImgDirection", 18: "MapDatum",
        19: "DestLatitudeRef", 20: "DestLatitude", 21: "DestLongitudeRef",
        22: "DestLongitude", 23: "DestBearingRef", 24: "DestBearing",
        25: "DestDistanceRef", 26: "DestDistance", 27: "ProcessingMethod",
        28: "AreaInformation", 29: "DateStamp", 30: "Differential", 31: "HPositioningError"}
    gpsinfo_decoded = {}
    for tag, val in gps_info.items():
        key = gpsitem_dict[tag]
        val_decoded = val
        match key:
            case "LatitudeRef":
                val_decoded = "North" if val == "N" else "South"
            case "LongitudeRef":
                val_decoded = "East" if val == "E" else "West"
            case "SpeedRef":
                val_decoded = {"K": "km/h", "M": "mph", "N": "knots"}.get(val, "Unknown")
            case "ImgDirectionRef":
                val_decoded = {"M": "Magnetic North", "T": "True North"}.get(val, "Unknown")
            case "DestBearingRef":
                val_decoded = {"M": "Magnetic North", "T": "True North"}.get(val, "Unknown")
            case _:
                pass
        gpsinfo_decoded[key] = val_decoded
    return gpsinfo_decoded


if __name__ == '__main__':
    pv(cv2.__version__)
