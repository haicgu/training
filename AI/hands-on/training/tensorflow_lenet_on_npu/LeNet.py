"""LeNet training"""

import os
import time
import sys
import argparse

from npu_bridge.npu_init import *
from tensorflow.core.protobuf.rewriter_config_pb2 import RewriterConfig
from tensorflow.core.protobuf import config_pb2

import tensorflow as tf
from matplotlib import pyplot as plt
from tensorflow.examples.tutorials.mnist import input_data
import math

from npu_bridge.estimator.npu.npu_loss_scale_optimizer import NPULossScaleOptimizer
from npu_bridge.estimator.npu.npu_loss_scale_manager import FixedLossScaleManager
from npu_bridge.estimator.npu.npu_loss_scale_manager import ExponentialUpdateLossScaleManager
from npu_bridge.estimator.npu.npu_optimizer import NPUDistributedOptimizer


def npu_tf_optimizer(opt):
    npu_opt = NPUDistributedOptimizer(opt)
    return npu_opt



def npu_session_config_init(args, session_config=None):
    """
    This function config npu session
    Args:
        args: The input paras
        session_config: npu session config
    Returns
        session_config
    """

    if ((not isinstance(session_config, config_pb2.ConfigProto)) and (not issubclass(type(session_config), config_pb2.ConfigProto))):
        session_config = config_pb2.ConfigProto()
    if (isinstance(session_config, config_pb2.ConfigProto) or issubclass(type(session_config), config_pb2.ConfigProto)):
        custom_op = session_config.graph_options.rewrite_options.custom_optimizers.add()
        custom_op.name = 'NpuOptimizer'
        custom_op.parameter_map["enable_data_pre_proc"].b = True
        custom_op.parameter_map["iterations_per_loop"].i = args.iteration_per_loop
        #calc mode
        custom_op.parameter_map["precision_mode"].s = tf.compat.as_bytes(str(args.precision_mode))
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(cur_dir, "./output")
        if (not os.path.exists(output_path)):
            os.mkdir(output_path)
        
        #profiling config
        if args.profiling == 'True':
            profiling_path = os.path.join(output_path, "profiling")
            if (not os.path.exists(profiling_path)):
                os.mkdir(profiling_path)
            custom_op.parameter_map["profiling_mode"].b = False
            custom_op.parameter_map["profiling_options"].s = tf.compat.as_bytes('{"output":"./output/profiling", "training_trace":"on", "task_trace":"on", "aicpu":"on", "fp_point":"layer_1/weights/Initializer/random_uniform/sub", "bp_point":"gradients/BiasAdd_grad/BiasAddGrad"}')

        #data_dump
        if args.data_dump_flag == 1:
            data_dump_path = os.path.join(output_path, "data_dump")
            if (not os.path.exists(data_dump_path)):
                os.mkdir(data_dump_path)

            custom_op.parameter_map["enable_dump"].b = True
            custom_op.parameter_map["dump_path"].s = tf.compat.as_bytes(data_dump_path)
            custom_op.parameter_map["dump_step"].s = tf.compat.as_bytes(args.data_dump_step)
            custom_op.parameter_map["dump_mode"].s = tf.compat.as_bytes("all")

        #over dump
        if args.over_dump == 'True':
            over_dump_path = os.path.join(output_path, "over_dump")
            if (not os.path.exists(over_dump_path)):
                os.mkdir(over_dump_path)

            custom_op.parameter_map["enable_dump_debug"].b = True
            custom_op.parameter_map["dump_path"].s = tf.compat.as_bytes(over_dump_path)
            custom_op.parameter_map["dump_debug_mode"].s = tf.compat.as_bytes("all")

        session_config.graph_options.rewrite_options.remapping = RewriterConfig.OFF
    return session_config



def get_config(args):
    """
    This function parses the command line arguments
    Args:
        args(str) : The command line arguments

    Returns
        args (dict): The arguments parsed into a dictionary
    """
    
    parser = argparse.ArgumentParser(description='Experiment parameters')
    parser.add_argument("--precision_mode", default='allow_fp32_to_fp16',
                        help="precision mode could bu \"allow_fp32_to_fp16\" or \"force_fp16\" or \"must_keep_origin_dtype\" or \"allow_mix_precision\"")
    parser.add_argument("--loss_scale_value", type=float, help="loss scale value.")
    parser.add_argument("--loss_scale_flag", type=int, default=0, help="whether to set loss scals.")
    parser.add_argument("--over_dump", default='False', help="whether to open over dump.")
    
    parser.add_argument("--data_dump_flag", type=int, default=0, help="whether to training data.")
    parser.add_argument("--data_dump_step", default='0|5|10', help="data dump step.")
    parser.add_argument("--profiling", default='False', help="whether to open profiling.")
    parser.add_argument("--random_remove", default='False', help="whether to remove random op in training.")
    parser.add_argument("--data_path", default='MNIST', help="training input data path.")

    parser.add_argument("--batch_size", type=int, default=64, help="train batch size.")
    parser.add_argument("--learing_rata", type=float, help="learning rate.")
    parser.add_argument("--steps", type=int, default=0, help="training steps")
    parser.add_argument("--ckpt_count", type=int, help="save checkpoiont max counts.")
    parser.add_argument("--epochs", type=int, default=1, help="epoch number.")
    parser.add_argument("--iteration_per_loop", default=1, type=int, help="every session run steps.")

    args, unknown = parser.parse_known_args(args)

    return args
    


def visualization(_mnist):
    """
    This function visualize imaga
    Args:
        _mnist: The image collection
    Returns
        None
    """

    for i in range(12):
        plt.subplot(3, 4, (i + 1))
        img = _mnist.train.images[(i + 1)]
        img = img.reshape(28, 28)
        plt.imshow(img)
    plt.show()


class LeNet(object):

    def __init__(self, args):
        self.batch_size = args.batch_size

    def create_eval(self, x):
        x = tf.reshape(x, [self.batch_size, 28, 28, 1])
        with tf.variable_scope('layer_1', reuse=True) as scope:
            w_1 = tf.get_variable('weights', shape=[5, 5, 1, 6])
            b_1 = tf.get_variable('bias', shape=[6])
        conv_1 = tf.nn.conv2d(x, w_1, strides=[1, 1, 1, 1], padding='SAME')
        act_1 = tf.sigmoid(tf.nn.bias_add(conv_1, b_1))
        max_pool_1 = tf.nn.max_pool(act_1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        with tf.variable_scope('layer_2', reuse=True) as scope:
            w_2 = tf.get_variable('weights', shape=[5, 5, 6, 16])
            b_2 = tf.get_variable('bias', shape=[16])
        conv_2 = tf.nn.conv2d(max_pool_1, w_2, strides=[1, 1, 1, 1], padding='SAME')
        act_2 = tf.sigmoid(tf.nn.bias_add(conv_2, b_2))
        max_pool_2 = tf.nn.max_pool(act_2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        flatten = tf.reshape(max_pool_2, shape=[(- 1), ((7 * 7) * 16)])
        with tf.variable_scope('fc_1', reuse=True) as scope:
            w_fc_1 = tf.get_variable('weight', shape=[((7 * 7) * 16), 120])
            b_fc_1 = tf.get_variable('bias', shape=[120], trainable=True)
        fc_1 = tf.nn.xw_plus_b(flatten, w_fc_1, b_fc_1)
        act_fc_1 = tf.nn.sigmoid(fc_1)
        with tf.variable_scope('fc_2', reuse=True) as scope:
            w_fc_2 = tf.get_variable('weight', shape=[120, 84])
            b_fc_2 = tf.get_variable('bias', shape=[84], trainable=True)
        fc_2 = tf.nn.xw_plus_b(act_fc_1, w_fc_2, b_fc_2)
        act_fc_2 = tf.nn.sigmoid(fc_2)
        with tf.variable_scope('fc_3', reuse=True) as scope:
            w_fc_3 = tf.get_variable('weight', shape=[84, 10])
            b_fc_3 = tf.get_variable('bias', shape=[10], trainable=True)
            tf.summary.histogram('weight', w_fc_3)
            tf.summary.histogram('bias', b_fc_3)
        fc_3 = tf.nn.xw_plus_b(act_fc_2, w_fc_3, b_fc_3)
        return fc_3

    def create(self, x):
        x = tf.reshape(x, [self.batch_size, 28, 28, 1])
        with tf.variable_scope('layer_1') as scope:
            w_1 = tf.get_variable('weights', shape=[5, 5, 1, 6])
            b_1 = tf.get_variable('bias', shape=[6])
        conv_1 = tf.nn.conv2d(x, w_1, strides=[1, 1, 1, 1], padding='SAME')
        act_1 = tf.sigmoid(tf.nn.bias_add(conv_1, b_1))
        max_pool_1 = tf.nn.max_pool(act_1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        with tf.variable_scope('layer_2') as scope:
            w_2 = tf.get_variable('weights', shape=[5, 5, 6, 16])
            b_2 = tf.get_variable('bias', shape=[16])
        conv_2 = tf.nn.conv2d(max_pool_1, w_2, strides=[1, 1, 1, 1], padding='SAME')
        act_2 = tf.sigmoid(tf.nn.bias_add(conv_2, b_2))
        max_pool_2 = tf.nn.max_pool(act_2, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding='SAME')
        flatten = tf.reshape(max_pool_2, shape=[(- 1), ((7 * 7) * 16)])
        with tf.variable_scope('fc_1') as scope:
            w_fc_1 = tf.get_variable('weight', shape=[((7 * 7) * 16), 120])
            b_fc_1 = tf.get_variable('bias', shape=[120], trainable=True)
        fc_1 = tf.nn.xw_plus_b(flatten, w_fc_1, b_fc_1)
        act_fc_1 = tf.nn.sigmoid(fc_1)
        with tf.variable_scope('fc_2') as scope:
            w_fc_2 = tf.get_variable('weight', shape=[120, 84])
            b_fc_2 = tf.get_variable('bias', shape=[84], trainable=True)
        fc_2 = tf.nn.xw_plus_b(act_fc_1, w_fc_2, b_fc_2)
        act_fc_2 = tf.nn.sigmoid(fc_2)
        with tf.variable_scope('fc_3') as scope:
            w_fc_3 = tf.get_variable('weight', shape=[84, 10])
            b_fc_3 = tf.get_variable('bias', shape=[10], trainable=True)
            tf.summary.histogram('weight', w_fc_3)
            tf.summary.histogram('bias', b_fc_3)
        fc_3 = tf.nn.xw_plus_b(act_fc_2, w_fc_3, b_fc_3)
        return fc_3

def make_dataset(image, label, batch_size, epoch=1):
    ds = tf.data.Dataset.from_tensor_slices((image, label))
    # same with data size for perfect shuffle
    ds = ds.shuffle(buffer_size=image.shape[0])
    ds = ds.repeat(epoch+1)
    ds = ds.batch(batch_size, drop_remainder=True)
    ds = ds.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
    options = tf.data.Options()
    options.experimental_threading.private_threadpool_size = 128
    options.experimental_threading.max_intra_op_parallelism = 1
    ds = ds.with_options(options)
    return ds

def train(args):
    """
    This function implement train and eval
    Args:
        args(dict) : The command line arguments

    Returns
        None
    """

    e2e_start_time = time.time()

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(cur_dir, "./output")
    if (not os.path.exists(output_path)):
        os.mkdir(output_path)

    mnist = input_data.read_data_sets(args.data_path, one_hot=True)
    train_dataset = make_dataset(mnist.train.images, mnist.train.labels, args.batch_size, args.epochs)
    test_dataset = make_dataset(mnist.test.images, mnist.test.labels, args.batch_size)
    train_iterator = tf.compat.v1.data.make_initializable_iterator(train_dataset)
    test_iterator = tf.compat.v1.data.make_initializable_iterator(test_dataset)
    train_x, train_y = train_iterator.get_next()
    test_next_element = test_iterator.get_next()

    le = LeNet(args)
    train_y_ = le.create(train_x)
    loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=train_y_, labels=train_y))

    optimizer = npu_tf_optimizer(tf.train.AdamOptimizer())
    if args.loss_scale_flag != 0:
        if args.loss_scale_value == 0:
            loss_scale_manager = ExponentialUpdateLossScaleManager(init_loss_scale=2**32, incr_every_n_steps=1000, decr_every_n_nan_or_inf=2, decr_ratio=0.5)
        elif args.loss_scale_value >= 1:
            loss_scale_manager = FixedLossScaleManager(args.loss_scale_value)
        else:
            raise ValueError("Invalid loss scale: %d" % args.loss_scale_value)
        optimizer = NPULossScaleOptimizer(optimizer, loss_scale_manager)

    train_op = optimizer.minimize(loss)
    tf.summary.scalar('loss', loss)

    x = tf.placeholder(tf.float32, [args.batch_size, 784])
    y = tf.placeholder(tf.float32, [args.batch_size, 10])
    y_ = le.create_eval(x)
    correct_pred = tf.equal(tf.argmax(y_, 1, output_type=tf.int32), tf.argmax(y, 1, output_type=tf.int32))
    accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))
    merged = tf.summary.merge_all()
    writer = tf.summary.FileWriter(output_path + '/logs')

    if args.steps > 0:
        steps = args.steps
    else:
        steps = math.ceil(mnist.train.num_examples / args.batch_size)

    with tf.Session(config=npu_session_config_init(args)) as sess:
        sess.run(train_iterator.initializer)
        sess.run(tf.global_variables_initializer())
        iteration_loop_op = util.set_iteration_per_loop(sess, train_op, args.iteration_per_loop)
        writer.add_graph(sess.graph)

        for epoch in range(args.epochs):
            for step in range(0, steps, args.iteration_per_loop):
                start_time = time.time()
                (summary, loss_value, _) = sess.run([merged, loss, iteration_loop_op])

                cost_time = (time.time()-start_time) / args.iteration_per_loop
                print("epoch : {}----step : {}----loss : {}----sec/step : {}".format(epoch, step, loss_value, cost_time))
                
                writer.add_summary(summary, step)

        sess.run(test_iterator.initializer)
        test_acc = 0
        test_count = 0
        for _ in range(10):
            (batch_xs, batch_ys) = sess.run(test_next_element)
            acc = sess.run(accuracy, feed_dict={x: batch_xs, y: batch_ys})
            test_acc += acc
            test_count += 1
            
        print('accuracy : {}'.format((test_acc / test_count)))
        saver = tf.train.Saver()
        saver.save(sess, os.path.join("./output/ckpt_npu", "mode.ckpt"))
        tf.io.write_graph(sess.graph, './output/ckpt_npu', 'graph.pbtxt', as_text=True)

        e2e_cost_time = time.time() - e2e_start_time

        with open(os.path.join(output_path, "performance_precision.txt"), "w") as file_write:
            write_str = "Final Accuracy accuracy : " + str(round((test_acc / test_count), 4))
            print(str(write_str))
            file_write.write(write_str)
            file_write.write('\r\n')

            write_str = "Final Performance ms/step : " + str(round(cost_time * 1000, 4))
            print(str(write_str))
            file_write.write(write_str)
            file_write.write('\r\n')

            write_str = "Final Training Duration sec : " + str(round(e2e_cost_time, 4))
            print(str(write_str))
            file_write.write(write_str)
            file_write.write('\r\n')



def main():
    """
    This function is interface of network
    Args:
        None
    Returns
        None
    """

    args = get_config(sys.argv[1:])
    train(args)



if __name__ == '__main__':
    main()
