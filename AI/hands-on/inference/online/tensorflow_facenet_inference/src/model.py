import tensorflow as tf
from tensorflow.core.protobuf.rewriter_config_pb2 import RewriterConfig
import time
import numpy as np
import npu_bridge

class Model(object):

    def __init__(self,model_path,input_tensor_name,output_tensor_name,batch_size=1):
        
        self.batch_size = batch_size
        self.model_path = model_path
        self.input_tensor_name = input_tensor_name
        self.output_tensor_name = output_tensor_name
        
        # Configurations of model build and tuning on the Ascend AI Processor
        config = tf.compat.v1.ConfigProto()
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
        self.graph = self.__load_model(self.model_path)
        self.input_tensor = self.graph.get_tensor_by_name(self.input_tensor_name)
        self.output_tensor = self.graph.get_tensor_by_name(self.output_tensor_name)

        # Model building is triggered when the sess.run() method is called for the first time, which takes a long time. You can tie the session to the object's lifetime.
        self.sess = tf.compat.v1.Session(config=config, graph=self.graph)

    def __load_model(self, model_file):
        """
        load frozen graph
        :param model_file:
        :return:
        """
        with tf.io.gfile.GFile(model_file, "rb") as gf:
            graph_def = tf.compat.v1.GraphDef()
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

def run_model(model, images):
    batch_images = model.batch_process(images)
    
    # ###start inference
    print("######## NOW Start inference!!! #########")
    batch_output, batch_time = model.inference(batch_images)

    print("######## Inference Finished!!! #########")
    print("Record %d batch intervals" % (len(batch_time)))
    print("In total spent", batch_time)
    
    return batch_output, batch_time