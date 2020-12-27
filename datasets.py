# code-checked
# server-checked

import cv2
import numpy as np
import os
import os.path as osp
import random
import torch
from torch.utils import data

import pickle

def generate_scale_label(image, label):
    f_scale = 0.5 + random.randint(0, 16)/10.0
    image = cv2.resize(image, None, fx=f_scale, fy=f_scale, interpolation=cv2.INTER_LINEAR)
    label = cv2.resize(label, None, fx=f_scale, fy=f_scale, interpolation=cv2.INTER_NEAREST)
    return image, label

def id2trainId(label, id_to_trainid):
    label_copy = label.copy()
    for k, v in id_to_trainid.items():
        label_copy[label == k] = v
    return label_copy

################################################################################
# Cityscapes
################################################################################
class DatasetCityscapesAugmentation(data.Dataset):
    def __init__(self, root, list_path, max_iters=None, crop_size=(512, 512), ignore_label=255):
        self.root = root
        self.list_path = list_path
        self.crop_h, self.crop_w = crop_size
        self.ignore_label = ignore_label

        self.img_ids = [i_id.strip().split() for i_id in open(list_path)]
        print ("DatasetCityscapesAugmentation - num unique examples: %d" % len(self.img_ids))
        if not max_iters==None:
                self.img_ids = self.img_ids * int(np.ceil(float(max_iters) / len(self.img_ids)))
        print ("DatasetCityscapesAugmentation - num examples: %d" % len(self.img_ids))

        self.files = []
        for item in self.img_ids:
            image_path, label_path = item
            name = osp.splitext(osp.basename(label_path))[0]
            img_file = osp.join(self.root, image_path)
            label_file = osp.join(self.root, label_path)
            self.files.append({
                "img": img_file,
                "label": label_file,
                "name": name,
                "weight": 1
            })

        self.id_to_trainid = {-1: ignore_label, 0: ignore_label, 1: ignore_label, 2: ignore_label,
                              3: ignore_label, 4: ignore_label, 5: ignore_label, 6: ignore_label,
                              7: 0, 8: 1, 9: ignore_label, 10: ignore_label, 11: 2, 12: 3, 13: 4,
                              14: ignore_label, 15: ignore_label, 16: ignore_label, 17: 5,
                              18: ignore_label, 19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12, 26: 13, 27: 14,
                              28: 15, 29: ignore_label, 30: ignore_label, 31: 16, 32: 17, 33: 18}

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        datafiles = self.files[index]
        image = cv2.imread(datafiles["img"], cv2.IMREAD_COLOR)
        label = cv2.imread(datafiles["label"], cv2.IMREAD_GRAYSCALE)

        label = id2trainId(label, self.id_to_trainid)

        size = image.shape
        name = datafiles["name"]
        image, label = generate_scale_label(image, label)
        image = np.asarray(image, np.float32)

        mean = (102.9801, 115.9465, 122.7717)
        image = image[:,:,::-1]
        image -= mean

        img_h, img_w = label.shape
        pad_h = max(self.crop_h - img_h, 0)
        pad_w = max(self.crop_w - img_w, 0)
        if pad_h > 0 or pad_w > 0:
            img_pad = cv2.copyMakeBorder(image, 0, pad_h, 0,
                pad_w, cv2.BORDER_CONSTANT,
                value=(0.0, 0.0, 0.0))
            label_pad = cv2.copyMakeBorder(label, 0, pad_h, 0,
                pad_w, cv2.BORDER_CONSTANT,
                value=(self.ignore_label,))
        else:
            img_pad, label_pad = image, label

        img_h, img_w = label_pad.shape
        h_off = random.randint(0, img_h - self.crop_h)
        w_off = random.randint(0, img_w - self.crop_w)
        image = np.asarray(img_pad[h_off : h_off+self.crop_h, w_off : w_off+self.crop_w], np.float32)
        label = np.asarray(label_pad[h_off : h_off+self.crop_h, w_off : w_off+self.crop_w], np.float32)
        image = image.transpose((2, 0, 1))

        flip = np.random.choice(2)*2 - 1
        image = image[:, :, ::flip]
        label = label[:, ::flip]

        return image.copy(), label.copy(), np.array(size), name

class DatasetCityscapesEval(data.Dataset):
    def __init__(self, root, list_path, ignore_label=255):
        self.root = root
        self.list_path = list_path
        self.ignore_label = ignore_label

        self.img_ids = [i_id.strip().split() for i_id in open(list_path)]
        print ("DatasetCityscapesEval - num examples: %d" % len(self.img_ids))

        self.files = []
        for item in self.img_ids:
            image_path, label_path = item
            name = osp.splitext(osp.basename(label_path))[0]
            img_file = osp.join(self.root, image_path)
            label_file = osp.join(self.root, label_path)
            self.files.append({
                "img": img_file,
                "label": label_file,
                "name": name,
                "weight": 1
            })

        self.id_to_trainid = {-1: ignore_label, 0: ignore_label, 1: ignore_label, 2: ignore_label,
                              3: ignore_label, 4: ignore_label, 5: ignore_label, 6: ignore_label,
                              7: 0, 8: 1, 9: ignore_label, 10: ignore_label, 11: 2, 12: 3, 13: 4,
                              14: ignore_label, 15: ignore_label, 16: ignore_label, 17: 5,
                              18: ignore_label, 19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12, 26: 13, 27: 14,
                              28: 15, 29: ignore_label, 30: ignore_label, 31: 16, 32: 17, 33: 18}

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        datafiles = self.files[index]
        image = cv2.imread(datafiles["img"], cv2.IMREAD_COLOR)
        label = cv2.imread(datafiles["label"], cv2.IMREAD_GRAYSCALE)

        if not os.path.exists(datafiles["img"]): # (26 out of 25000 images are missing)
            return self.__getitem__(0)

        label = id2trainId(label, self.id_to_trainid)

        size = image.shape
        name = datafiles["name"]

        image = np.asarray(image, np.float32)

        mean = (102.9801, 115.9465, 122.7717)
        image = image[:,:,::-1]
        image -= mean

        image = image.transpose((2, 0, 1))

        return image.copy(), label.copy(), np.array(size), name

class DatasetCityscapesEvalSeq(data.Dataset):
    def __init__(self, data_path, sequence="00"):
        self.data_path = data_path

        self.img_dir = self.data_path + "/leftImg8bit/demoVideo/stuttgart_" + sequence + "/"

        self.examples = []

        file_names = os.listdir(self.img_dir)
        for file_name in file_names:
            img_id = file_name.split("_leftImg8bit.png")[0]

            img_path = self.img_dir + file_name

            example = {}
            example["img_path"] = img_path
            example["img_id"] = img_id
            self.examples.append(example)

        self.num_examples = len(self.examples)
        print ("DatasetCityscapesEvalSeq - num examples: %d" % self.num_examples)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, index):
        datafiles = self.examples[index]
        image = cv2.imread(datafiles["img_path"], cv2.IMREAD_COLOR)
        size = image.shape
        name = datafiles["img_id"]
        image = np.asarray(image, np.float32)

        mean = (102.9801, 115.9465, 122.7717)
        image = image[:,:,::-1]
        image -= mean

        image = image.transpose((2, 0, 1))

        return image.copy(), np.array(size), name






################################################################################
# Synscapes
################################################################################
class DatasetSynscapesAugmentation(data.Dataset):
    def __init__(self, root, root_meta, type="train", max_iters=None, crop_size=(512, 512), ignore_label=255):
        self.root = root
        self.root_meta = root_meta
        self.crop_h, self.crop_w = crop_size
        self.ignore_label = ignore_label

        if type == "train":
            with open(root_meta + "/train_img_ids.pkl", "rb") as file: # (needed for python3)
                self.img_ids = pickle.load(file)
        elif type == "val":
            with open(root_meta + "/val_img_ids.pkl", "rb") as file: # (needed for python3)
                self.img_ids = pickle.load(file)
        else:
            raise Exception("type must be either 'train' or 'val'!")

        print ("DatasetSynscapesAugmentation - num unique examples: %d" % len(self.img_ids))
        if not max_iters==None:
                self.img_ids = self.img_ids * int(np.ceil(float(max_iters) / len(self.img_ids)))
        print ("DatasetSynscapesAugmentation - num examples: %d" % len(self.img_ids))

        self.files = []
        for img_id in self.img_ids:
            self.files.append({
                "img": self.root + "/img/rgb-2k/" + img_id + ".png",
                "label": self.root_meta + "/gtFine/" + img_id + ".png",
                "name": img_id,
                "weight": 1
            })

        self.id_to_trainid = {-1: ignore_label, 0: ignore_label, 1: ignore_label, 2: ignore_label,
                              3: ignore_label, 4: ignore_label, 5: ignore_label, 6: ignore_label,
                              7: 0, 8: 1, 9: ignore_label, 10: ignore_label, 11: 2, 12: 3, 13: 4,
                              14: ignore_label, 15: ignore_label, 16: ignore_label, 17: 5,
                              18: ignore_label, 19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12, 26: 13, 27: 14,
                              28: 15, 29: ignore_label, 30: ignore_label, 31: 16, 32: 17, 33: 18}

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        datafiles = self.files[index]
        image = cv2.imread(datafiles["img"], cv2.IMREAD_COLOR)
        label = cv2.imread(datafiles["label"], cv2.IMREAD_GRAYSCALE)

        if not os.path.exists(datafiles["img"]): # (26 out of 25000 images are missing)
            return self.__getitem__(0)

        label = id2trainId(label, self.id_to_trainid)

        size = image.shape
        name = datafiles["name"]
        image, label = generate_scale_label(image, label)
        image = np.asarray(image, np.float32)

        mean = (102.9801, 115.9465, 122.7717)
        image = image[:,:,::-1]
        image -= mean

        img_h, img_w = label.shape
        pad_h = max(self.crop_h - img_h, 0)
        pad_w = max(self.crop_w - img_w, 0)
        if pad_h > 0 or pad_w > 0:
            img_pad = cv2.copyMakeBorder(image, 0, pad_h, 0,
                pad_w, cv2.BORDER_CONSTANT,
                value=(0.0, 0.0, 0.0))
            label_pad = cv2.copyMakeBorder(label, 0, pad_h, 0,
                pad_w, cv2.BORDER_CONSTANT,
                value=(self.ignore_label,))
        else:
            img_pad, label_pad = image, label

        img_h, img_w = label_pad.shape
        h_off = random.randint(0, img_h - self.crop_h)
        w_off = random.randint(0, img_w - self.crop_w)
        image = np.asarray(img_pad[h_off : h_off+self.crop_h, w_off : w_off+self.crop_w], np.float32)
        label = np.asarray(label_pad[h_off : h_off+self.crop_h, w_off : w_off+self.crop_w], np.float32)
        image = image.transpose((2, 0, 1))

        flip = np.random.choice(2)*2 - 1
        image = image[:, :, ::flip]
        label = label[:, ::flip]

        return image.copy(), label.copy(), np.array(size), name

class DatasetSynscapesEval(data.Dataset):
    def __init__(self, root, root_meta, type="val", ignore_label=255):
        self.root = root
        self.root_meta = root_meta
        self.ignore_label = ignore_label

        if type == "train":
            with open(root_meta + "/train_img_ids.pkl", "rb") as file: # (needed for python3)
                self.img_ids = pickle.load(file)
        elif type == "val":
            with open(root_meta + "/val_img_ids.pkl", "rb") as file: # (needed for python3)
                self.img_ids = pickle.load(file)
        else:
            raise Exception("type must be either 'train' or 'val'!")

        print ("DatasetSynscapesEval - num examples: %d" % len(self.img_ids))

        self.files = []
        for img_id in self.img_ids:
            self.files.append({
                "img": self.root + "/img/rgb-2k/" + img_id + ".png",
                "label": self.root_meta + "/gtFine/" + img_id + ".png",
                "name": img_id,
                "weight": 1
            })

        self.id_to_trainid = {-1: ignore_label, 0: ignore_label, 1: ignore_label, 2: ignore_label,
                              3: ignore_label, 4: ignore_label, 5: ignore_label, 6: ignore_label,
                              7: 0, 8: 1, 9: ignore_label, 10: ignore_label, 11: 2, 12: 3, 13: 4,
                              14: ignore_label, 15: ignore_label, 16: ignore_label, 17: 5,
                              18: ignore_label, 19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12, 26: 13, 27: 14,
                              28: 15, 29: ignore_label, 30: ignore_label, 31: 16, 32: 17, 33: 18}

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        datafiles = self.files[index]
        image = cv2.imread(datafiles["img"], cv2.IMREAD_COLOR)
        label = cv2.imread(datafiles["label"], cv2.IMREAD_GRAYSCALE)

        if not os.path.exists(datafiles["img"]): # (26 out of 25000 images are missing)
            return self.__getitem__(0)

        label = id2trainId(label, self.id_to_trainid)

        size = image.shape
        name = datafiles["name"]

        image = np.asarray(image, np.float32)

        mean = (102.9801, 115.9465, 122.7717)
        image = image[:,:,::-1]
        image -= mean

        image = image.transpose((2, 0, 1))

        return image.copy(), label.copy(), np.array(size), name

################## Njupt ############
class Njupteval(data.Dataset):
    def __init__(self, root, list_path=None, ignore_label=255):
        self.root = root
        self.list_path = list_path
        self.ignore_label = ignore_label

        self.img_ids = ['njupt1.jpg','njupt2.jpg','njupt3.jpg']
        print ("DatasetCityscapesEval - num examples: %d" % len(self.img_ids))

        self.files = []
        for item in self.img_ids:
            name = os.path.splitext(item)[0]
            image_path = item
            # name = osp.splitext(osp.basename(label_path))[0]
            img_file = osp.join(self.root, image_path)
            self.files.append({
                "img": img_file,
                "name": name,
                "weight": 1
            })

        self.id_to_trainid = {-1: ignore_label, 0: ignore_label, 1: ignore_label, 2: ignore_label,
                              3: ignore_label, 4: ignore_label, 5: ignore_label, 6: ignore_label,
                              7: 0, 8: 1, 9: ignore_label, 10: ignore_label, 11: 2, 12: 3, 13: 4,
                              14: ignore_label, 15: ignore_label, 16: ignore_label, 17: 5,
                              18: ignore_label, 19: 6, 20: 7, 21: 8, 22: 9, 23: 10, 24: 11, 25: 12, 26: 13, 27: 14,
                              28: 15, 29: ignore_label, 30: ignore_label, 31: 16, 32: 17, 33: 18}

    def __len__(self):
        return len(self.files)

    def __getitem__(self, index):
        datafiles = self.files[index]
        image = cv2.imread(datafiles["img"], cv2.IMREAD_COLOR)
        #label = cv2.imread(datafiles["label"], cv2.IMREAD_GRAYSCALE)

        if not os.path.exists(datafiles["img"]): # (26 out of 25000 images are missing)
            return self.__getitem__(0)

        #label = id2trainId(label, self.id_to_trainid)

        size = image.shape
        name = datafiles["name"]

        image = np.asarray(image, np.float32)

        mean = (102.9801, 115.9465, 122.7717)
        image = image[:,:,::-1]
        image -= mean

        image = image.transpose((2, 0, 1))

        return image.copy(), np.array(size), name