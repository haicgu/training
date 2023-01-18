import tensorflow as tf
import os
import argparse
from tensorflow.core.protobuf.rewriter_config_pb2 import RewriterConfig
import npu_bridge
import time
import numpy as np

def parse_args():
    '''
    Set the model path, input, and output.
    :return:
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--batchsize', default=1,
                        help="""batchsize""")
    parser.add_argument('--model_path', default='pb/resnet50HC.pb',
                        help="""pb path""")
    parser.add_argument('--image_path', default='image-50000',
                        help="""the data path""")
    parser.add_argument('--input_tensor_name', default='input_data:0',
                        help="""input_tensor_name""")
    parser.add_argument('--output_tensor_name', default='resnet_model/final_dense:0',
                        help="""output_tensor_name""")
    args, unknown_args = parser.parse_known_args()
    if len(unknown_args) > 0:
        for bad_arg in unknown_args:
            print("ERROR: Unknown command line arg: %s" % bad_arg)
        raise ValueError("Invalid command line arg(s)")
    return args

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
        with tf.Session().as_default():
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
            tf.reset_default_graph()

    return np.array(imagelist), images_count, image_name_list

class Model(object):
    #set batchsize:
    args = parse_args()
    batch_size = int(args.batchsize)

    def __init__(self):

        # Configurations of model build and tuning on the Ascend AI Processor
        config = tf.ConfigProto()
        custom_op = config.graph_options.rewrite_options.custom_optimizers.add()
        custom_op.name = "NpuOptimizer"
        # Configuration 1: Run inference on the Ascend AI Processor.
        custom_op.parameter_map["use_off_line"].b = True
        # Configuration 2: In the online inference scenario, you are advised to retain the default precision selection force_fp16 to achieve better performance.
        custom_op.parameter_map["precision_mode"].s = tf.compat.as_bytes("force_fp16")
        # Configuration 3: Select the graph run mode. Set this parameter to 0 in the inference scenario or retain the default value 1 in the training scenario.
        custom_op.parameter_map["graph_run_mode"].i = 0

        # Whether you want dynamic input dimensions during execution
        #custom_op.parameter_map["dynamic_input"].b = True
        #custom_op.parameter_map["dynamic_graph_execute_mode"].s = tf.compat.as_bytes("lazy_recompile")

        # Configuration 4: Disable remapping and MemoryOptimizer.
        config.graph_options.rewrite_options.remapping = RewriterConfig.OFF
        config.graph_options.rewrite_options.memory_optimization = RewriterConfig.OFF
        # Load the model and set the input and output nodes of the model.
        args = parse_args()
        self.graph = self.__load_model(args.model_path)
        self.input_tensor = self.graph.get_tensor_by_name(args.input_tensor_name)
        self.output_tensor = self.graph.get_tensor_by_name(args.output_tensor_name)

        # Model building is triggered when the sess.run() method is called for the first time, which takes a long time. You can tie the session to the object's lifetime.
        self.sess = tf.Session(config=config, graph=self.graph)

    def __load_model(self, model_file):
        """
        load frozen graph
        :param model_file:
        :return:
        """
        with tf.gfile.GFile(model_file, "rb") as gf:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(gf.read())

        with tf.Graph().as_default() as graph:
            tf.import_graph_def(graph_def, name="")

        return graph

    def inference(self, batch_data):
        """
        do infer
        :param image_data:
        :return:
        """
        out_list = []
        batch_time = []

        for data in batch_data:
            print("================== data", data.shape, data.dtype)
            t = time.time()
            out = self.sess.run(self.output_tensor, feed_dict={self.input_tensor: data})
            batch_time.append(time.time() - t)
            out_list.append(out)
        return np.array(out_list), batch_time

    def batch_process(self, image_data):
        """
        batch
        :param image_data:images
        :param image_data:image labels
        :return:
        """
        # Get the batch information of the current input data, and automatically adjust the data to the fixed batch
        n_dim = image_data.shape[0]
        batch_size = self.batch_size

        # if data is not enough for the whole batch, you need to complete the data
        m = n_dim % batch_size
        if m < batch_size and m > 0:
            # The insufficient part shall be filled with 0 according to n dimension
            pad = np.zeros((batch_size - m, 160, 160, 3)).astype(np.float32)
            image_data = np.concatenate((image_data, pad), axis=0)

        # Define the Minis that can be divided into several batches
        mini_batch = []
        i = 0
        while i < n_dim:
            # Define the Minis that can be divided into several batches
            mini_batch.append(image_data[i: i + batch_size, :, :, :])
            i += batch_size

        return mini_batch

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

def main():
    args = parse_args()
    ###data preprocess
    tf.reset_default_graph()
    print("########NOW Start Preprocess!!!#########")
    images, images_count, image_name_list = image_process(args.image_path)
    print("images shape", images.shape, images.dtype)
    print("######## Read %d images #########" % (images_count))

    ###batch process
    print("######## NOW Start Batch!!! #########")
    model = Model()

    print("######## Object Created #########")
    batch_images = model.batch_process(images)

    # batch_images = [np.zeros((3, 160, 160, 3), dtype=np.float32) for _ in range(5)]
    # ###start inference
    print("######## NOW Start inference!!! #########")
    batch_output, batch_time = model.inference(batch_images)

    print("######## Inference Finished!!! #########")
    print("Record %d batch intervals" % (len(batch_time)))
    print("In total spent", batch_time)
    print()
    # print("batch_logits shape", batch_output[0][0].shape)

    assert len(image_name_list) == len(batch_output)

    print("==== Euclidean Distance")
    for i in range(len(image_name_list)-1):
        for j in range(i+1, len(image_name_list)):
            print("Between %s and %s: %f" % (image_name_list[i], image_name_list[j], distance(batch_output[i], batch_output[j])))
    print()
    print("==== Cosine Distance")
    for i in range(len(image_name_list)-1):
        for j in range(i+1, len(image_name_list)):
            print("Between %s and %s: %f" % (image_name_list[i], image_name_list[j], distance(batch_output[i], batch_output[j], distance_metric=1)))

if __name__ == '__main__':
    main()