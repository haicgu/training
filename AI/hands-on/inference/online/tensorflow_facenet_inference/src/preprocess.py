import os
import tensorflow as tf
import numpy as np

def normalize(inputs):
    '''
   Normalize input images.
    :param inputs: 
    :return: 
    '''
    mean = [121.0, 115.0, 100.0]
    std =  [70.0, 68.0, 71.0]
    mean = tf.expand_dims(tf.expand_dims(mean, 0), 0)
    std = tf.expand_dims(tf.expand_dims(std, 0), 0)
    inputs = inputs - mean
    inputs = inputs * (1.0 / std)
    return inputs

def normalize_facenet(inputs):
    inputs = inputs - 127.5
    inputs = inputs / 128.0
    return inputs

def image_process(image_path):
    '''
    Preprocess input images.
    :param image_path: 
    :return: 
    '''
    image_name_list = []
    imagelist = []
    images_count = 0
    for file in os.listdir(image_path):
        with tf.compat.v1.Session().as_default():
            image_file = os.path.join(image_path, file)
            image_name = image_file.split('/')[-1].split('.')[0]
            print("Image name:", image_name)
            #images preprocessing
            image= tf.gfile.FastGFile(image_file, 'rb').read()
            img = tf.image.decode_jpeg(image, channels=3)
            # bbox = tf.constant([0.1,0.1,0.9,0.9])
            bbox = tf.constant([0.,0.,1.0,1.0])
            img = tf.image.crop_and_resize(img[None, :, :, :], bbox[None, :], [0], [160, 160])[0]
            img = tf.clip_by_value(img, 0., 255.)
            img = normalize_facenet(img)
            img = tf.cast(img, tf.float32)
            images_count = images_count + 1
            img = img.eval()
            imagelist.append(img)
            image_name_list.append(image_name)
            tf.compat.v1.reset_default_graph()

    return np.array(imagelist), images_count, image_name_list

def distance(embeddings1, embeddings2, distance_metric=0):
    if distance_metric==0:
        # Euclidian distance
        diff = np.subtract(embeddings1, embeddings2)
        dist = np.sum(np.square(diff),1)
    elif distance_metric==1:
        # Distance based on cosine similarity
        dot = np.sum(np.multiply(embeddings1, embeddings2), axis=1)
        norm = np.linalg.norm(embeddings1, axis=1) * np.linalg.norm(embeddings2, axis=1)
        similarity = dot / norm
        dist = np.arccos(similarity) / np.pi
    else:
        raise 'Undefined distance metric %d' % distance_metric 
        
    return dist