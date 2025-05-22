#!/bin/bash

for i in {0..30}
do
    python generate_video_from_images.py --folder /home/tl/data/datasets/video/vidoe_recognition_data/${i}/ --output /home/tl/data/datasets/video/vidoe_recognition_data/${i}.mp4
done