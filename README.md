# APDe-MVS
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Paper](https://img.shields.io/badge/Paper-APDeMVS-red.svg)](https://doi.org/10.1016/j.patcog.2025.112593)

## Introduction

APDe-MVS is the enhanced version of [APD-MVS](https://github.com/whoiszzj/APD-MVS.git). Based on APD-MVS, we introduce some new contributions to make the reconstruction performance better.

1. We propose a focal weight for the deformable PM, which forces our deformable PM to take all the anchor pixels into account, further improving reconstruction accuracy.  
1. **We propose a detailed analysis of the motivation and problems with geometric consistency. Based on this, we develop an inconsistency-aware impetus strategy.** 
1. We propose a SAM plug-in in our pipeline, enabling semantic-aware depth discontinuity detection in memory-insensitive applications. 
1. Besides, we introduce a visibility conflict filter plug-in in the point cloud fusion stage, enhancing the reconstruction quality. 

Moreover, we have appropriately optimized the code to make it more feature-rich and user-friendly. If you find this project useful for your research, please cite:  

```
@article{ZENG2025112593,
    title = {Matching Ambiguity-Resilient Multi-View Stereo via Adaptive Patch Deformation},
    journal = {Pattern Recognition},
    pages = {112593},
    year = {2025},
    issn = {0031-3203},
    doi = {https://doi.org/10.1016/j.patcog.2025.112593},
    url = {https://www.sciencedirect.com/science/article/pii/S0031320325012567},
    author = {Zhaojie Zeng and Yuesong Wang and Tao Guan}
}
```

## Dependencies

The code has been tested on Ubuntu 24.04, and you can modify the CMakeList.txt to compile on Windows.
* [Cuda](https://developer.nvidia.cn/zh-cn/cuda-toolkit) >= 11.8
* [OpenCV](https://opencv.org/) >= 4.6.0
* [Boost](https://www.boost.org/) >= 1.78.0
* [cmake](https://cmake.org/) >= 3.23

If you want to use segmentation models such as SAM as plugins for reconstruction, you also need to install the corresponding model libraries. For example, for [SAM](https://github.com/facebookresearch/segment-anything.git):

``` sh
pip install git+https://github.com/facebookresearch/segment-anything.git
```


## Usage
### Compile APDe-MVS

```  sh
git clone https://github.com/whoiszzj/APDe-MVS.git
cd APDe-MVS
mkdir build & cd build
cmake ..
make
conda create -n APDe-MVS python=3.12
conda activate APDe-MVS
pip install git+https://github.com/facebookresearch/segment-anything.git
```
### Prepare Datasets

#### ETH Dataset

You may download [train](https://www.eth3d.net/data/multi_view_training_dslr_undistorted.7z) and [test](https://www.eth3d.net/data/multi_view_test_dslr_undistorted.7z) dataset from ETH3D, and use the script [*colmap2mvsnet.py*](./colmap2mvsnet.py) to convert the dataset format(you may refer to [MVSNet](https://github.com/YoYo000/MVSNet#file-formats)). You can use the "scale" option in the script to generate any resolution you need.

```python
python colmap2mvsnet.py --dense_folder <ETH3D data path, such as ./ETH3D/office> --save_folder <The path to save> --scale_factor 2 # half resolution
```

#### Tanks & Temples Dataset

We use the version provided by MVSNet. The dataset can be downloaded from [here](https://drive.google.com/file/d/1YArOJaX9WVLJh4757uE8AEREYkgszrCo/view), and the format is exactly what we need.

#### Other Dataset

Such as DTU and BlenderMVS, you may explore them yourself. 

!!! But remember to modify the [ReadCamera](https://github.com/whoiszzj/APDe-MVS/blob/03cf0b4071cdc1538a445ab7256f04ac8f2b4dcd/APD.cpp#L85) function!!!

### Run
Assuming you have completed the data preparation above, your directory should look like this:
```
./data/ETH3D/  # dataset root path
├── ...
├── meadow
├── office  # scan name
│   ├── cams
│   │   ├── 00000000_cam.txt
│   │   ├── 00000001_cam.txt
│   │   ├── 00000002_cam.txt
│   │   ├── ...
│   │   └── 00000025_cam.txt
│   ├── images
│   │   ├── 00000000.jpg
│   │   ├── 00000001.jpg
│   │   ├── 00000002.jpg
│   │   ├── ...
│   │   └── 00000025.jpg
│   └── pair.txt
└── pipe
```

Compared to APD-MVS, we now provide a Python runner script [run.py](https://github.com/whoiszzj/APDe-MVS/blob/master/run.py) for single-scene runs and batch runs across an entire dataset. Below we use the ETH3D dataset (root path `./data/ETH3D`) to introduce the features of `run.py` with a few usage examples.

| Parameter        | Description                                                  |
| ---------------- | ------------------------------------------------------------ |
| data_dir         | Root directory of the dataset, e.g., `./data/ETH3D`         |
| APD_path         | Path to the compiled APDe executable, default `./build/APD` |
| resume           | When running the full dataset, skip scenes already finished; checks if `APD/APD.ply` exists under the output path. |
| gpu_num          | Number of GPUs to use when training the whole dataset.       |
| work_num         | Number of scans processed per GPU.                           |
| scans            | List of scene names to process (list of strings). If empty, runs all scenes under `<data_dir>`. |
| reservation      | Delay start time, e.g., `3h30m10s` starts after 3h 30m 10s.  |
| no_fuse          | Run depth estimation only, skip fusion. After fusion, intermediate results (depth, normal, etc.) are written; you can later run fusion-only. |
| only_fuse        | Run fusion only without re-running depth estimation; requires existing depth predictions. |
| memory_cache     | If host memory is sufficient, keep intermediates in memory to reduce IO. In this mode, even after depth finishes, depth/normal maps are not written to disk; fusion runs directly and only the final point cloud is kept. |
| flush            | Manually flush intermediate outputs (e.g., depth maps) to disk after depth estimation finishes. |
| no_sam           | Disable the SAM plugin. By default, before depth estimation, the script [tools/run_SAM.py](https://github.com/whoiszzj/APDe-MVS/blob/master/tools/run_SAM.py) is used to obtain SAM segmentations. |
| no_impetus       | Disable inconsistency-aware impetus. Enabled by default; recommended to keep on. |
| no_weak_filter   | Disable visibility conflict filter. Enabled by default; recommended to keep on. |
| no_color         | Do not export point colors.                                   |
| dry_run          | Print the commands only; do not execute reconstruction.       |
| backup_code      | Back up the code.                                             |
| ETH3D_train      | Quickly select all 13 scenes in the ETH3D train set. Overrides `scans`. |
| ETH3D_test       | Quickly select all 12 scenes in the ETH3D test set. Overrides `scans`. |
| TaT_intermediate | Quickly select all 7 scenes in Tanks and Temples Intermediate set. Overrides `scans`. |
| TaT_advanced     | Quickly select all 6 scenes in Tanks and Temples Advanced set. Overrides `scans`. |
| export_anchor    | Export anchor information; use `anchor_vis.py` to visualize intermediates. |
| export_curve     | Export Reliable Curve. Visualization code is not included; feel free to use GPT/Cursor to help visualize. |

Assume your server has many CPU threads but low turbo frequency, a large amount of RAM with slow IO, and 4× A100 GPUs.

Demo 1: Run all scenes in the ETH3D train set.

```sh
#!/bin/bash
make 
cmake --build ./build --target APD -j 4

# run depth estimation
python run.py \
    --APD_path ./build/APD \
    --data_dir $HOME/Work/Data/ETH3D/data \
    --memory_cache \  # Use host memory to accelerate IO
    --no_fuse \   # Run depth only; skip fusion. Exports final depth and normal maps
    --gpu_num 4 \  # Use 4 GPUs
    --backup_code \
    --ETH3D_train
    
# If you're renting GPUs, you can now release the GPU resources
# run fusion
python run.py \
    --APD_path ./build/APD \
    --data_dir $HOME/Work/Data/ETH3D/data \
    --only_fuse \   # Run fusion only
    --work_num 4 \  # Multithreaded fusion; fuse 4 scenes in parallel
    --no_color \  # Do not export colors (exporting is recommended)
    --ETH3D_train
# evaluation
# You may need to adjust some parameters to match your environment.
# Also ensure ETH3D's official evaluation script can run properly.
# python tools/eval_eth_train.py --work_num 4 --data_dir /home/zzj/Work/Data/ETH3D/data
# It will output a score table after completion
```

Demo 2: Run a single scene in a dataset, e.g., `office` in ETH3D.

```sh
python run.py \
   --APD_path ./build/APD \
   --data_dir $HOME/Work/Data/ETH3D/data \
   --memory_cache \
   --backup_code \
   --flush \  # Flush intermediate outputs after depth estimation
   --scans office  # Scene name
```

Finally, a brief introduction to the script `tools/run_SAM.py`:

| Parameter  | Description                                                  |
| ---------- | ------------------------------------------------------------ |
| work_dir   | Same as `data_dir` in `run.py`; root directory of the dataset |
| max_size   | Maximum image size used during SAM. For example, if the original H×W is 4000×6000 and `max_size` is 900, masks are generated at 600×900 (aspect-preserving). During depth estimation, the masks are automatically matched to each image resolution. |
| model_type | SAM model size: `vit_h`, `vit_b`, `vit_l`                    |
| scans      | List of scene names to process (list of strings). If empty, runs all scenes under `<data_dir>`. |

If you consider SAM a bit out of date, you can replace it with a model like SAM2 to improve quality, speed, and memory usage. Note that you will need small script adjustments while keeping the mask format consistent.


## Acknowledgements

This code largely benefits from the following repositories: [ACMM](https://github.com/GhiXu/ACMM.git), [Colmap](https://github.com/colmap/colmap.git), [SAM](https://github.com/facebookresearch/segment-anything.git). Thanks to their authors for opening the source of their excellent works.

If you have any question or find some bugs, please leave it in [Issues](https://github.com/whoiszzj/APDe-MVS/issues)! Thank you!
