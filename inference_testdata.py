"""Run DeepLab-ResNet on a given image.

This script computes a segmentation mask for a given image.
"""

from __future__ import print_function

import argparse
from datetime import datetime
import os
import sys
import time
import glob
from scipy import misc

from PIL import Image

import tensorflow as tf
import numpy as np

from deeplab_resnet import DeepLabResNetModel, ImageReader, decode_labels, prepare_label

SAVE_DIR = './testdata_output/'
IMG_MEAN = np.array((104.00698793,116.66876762,122.67891434), dtype=np.float32)

def get_arguments():
    """Parse all the arguments provided from the CLI.
    
    Returns:
      A list of parsed arguments.
    """
    parser = argparse.ArgumentParser(description="DeepLabLFOV Network Inference.")
    parser.add_argument("--test-img-dir", type=str,
                        help="Path to the RGB image file.")
    parser.add_argument("--model-weights", type=str,
                        help="Path to the file with model weights.")
    parser.add_argument("--save-dir", type=str, default=SAVE_DIR,
                        help="Where to save predicted mask.")
    return parser.parse_args()

def load(saver, sess, ckpt_path):
    '''Load trained weights.
    
    Args:
      saver: TensorFlow saver object.
      sess: TensorFlow session.
      ckpt_path: path to checkpoint file with parameters.
    ''' 
    saver.restore(sess, ckpt_path)
    print("Restored model parameters from {}".format(ckpt_path))

def main():
    """Create the model and start the evaluation process."""
    args = get_arguments()
    if not os.path.exists(args.save_dir):
        print("save_dir not exist,mkdir..")
        os.makedirs(args.save_dir)

    # Prepare image.
    img_path = tf.placeholder(tf.string)
    img = tf.image.decode_jpeg(tf.read_file(img_path), channels=3)
    # Convert RGB to BGR.
    img_r, img_g, img_b = tf.split(value=img, num_or_size_splits=3, axis=2)
    img = tf.cast(tf.concat([img_b, img_g, img_r], 2), dtype=tf.float32)
    # Extract mean.
    img -= IMG_MEAN

    # Create network.
    net = DeepLabResNetModel({'data': tf.expand_dims(img, dim=0)}, is_training=False)

    # Which variables to load.
    restore_var = tf.global_variables()

    # Predictions.
    raw_output = net.layers['fc1_voc12']
    raw_output_up = tf.image.resize_bilinear(raw_output, tf.shape(img)[0:2, ])
    raw_output_up = tf.argmax(raw_output_up, dimension=3)
    pred = tf.expand_dims(raw_output_up, dim=3)

    # Set up TF session and initialize variables.
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.Session(config=config)
    init = tf.global_variables_initializer()

    sess.run(init)

    # Load weights.
    loader = tf.train.Saver(var_list=restore_var)
    load(loader, sess, args.model_weights)

    test_img_list = glob.glob(os.path.join(args.test_img_dir,"*.jpg"))
    for current_img_path in test_img_list:
        # Perform inference.
        preds = sess.run(pred,feed_dict={img_path:current_img_path})

        # dont need visulization
        #msk = decode_labels(preds)
        #im = Image.fromarray(msk[0])


        #im = Image.fromarray(preds[0])


        if not os.path.exists(args.save_dir):
            os.makedirs(args.save_dir)

        img_name = os.path.basename(current_img_path)
        misc.imsave(os.path.join(args.save_dir,img_name), preds[0])
        #im.save(os.path.join(args.save_dir,img_name))


        print('The output file has been saved to {}'.format(os.path.join(args.save_dir,img_name)))

    
if __name__ == '__main__':
    main()
