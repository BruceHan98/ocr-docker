### 1. 简介

本项目利用强悍的 [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) 工具库和 Docker 完成通用的 OCR 服务化部署。OCR 推理功能采用基于 paddlepaddle 框架的 [C++ 推理](https://github.com/PaddlePaddle/PaddleOCR/tree/release/2.5/deploy/cpp_infer) 代码实现文本检测与文本识别，具体的 OCR 功能（通用 OCR 识别、身份证识别、文档识别等）使用 Python 实现。C++ 大大提高了推理速度，而 Python 提高了 OCR 功能的编写效率。最后用 FastAPI 封装接口并通过 Docker 部署，使用 streamlit 实现了简单的前端 demo。

### 2. 项目结构

```bash
├── build
│   ├── opencv3					# opencv 安装文件
│   ├── paddle_inference		     # paddle 预测库
├── ppocr					     # C++ 推理代码
├── app.py					     # OCR 功能模块代码
├── Dockerfile
├── LICENSE.txt
├── ocr-web.py				        # streamlit 前端 demo
├── requirements.txt
├── run_docker.sh
├── server.py					# FastAPI
```

**Paddle 预测库**

使用 Paddle 官方 docker 减少了很多自己编译 paddle 预测库的麻烦，直接去[官网](https://paddle-inference.readthedocs.io/en/latest/user_guides/download_lib.html)下载对应的 paddle 预测库后解压。

**OpenCV 库**

编译 OpenCV 库的安装文件夹。

**cpp infer**

C++ 推理的代码修改自 PaddleOCR/deploy/cpp_infer，放在 ppocr 文件夹下。

以上文件可通过[链接](https://pan.baidu.com/s/1UDNw0m6fUwnBuW-9dGQOrg?pwd=0m38)下载。（文件较多，git 传输容易断）

### 3. 部署

1.克隆项目代码

```ba
git clone https://github.com/BruceHan98/ocr-docker
cd ocr-docker
```

2.通过[链接](https://pan.baidu.com/s/1UDNw0m6fUwnBuW-9dGQOrg?pwd=0m38)下载 build 与 ppocr 文件并解压到项目路径下。

3.制作 docker 镜像并运行 docker 容器

```bash
bash run_docker.sh
```

可在 run_docker.sh 中修改 FastAPI 端口（默认为 9000）。

4.运行前端 demo

修改 ocr-web.py 中的 `your_ip_address` 为项目部署的 ip 地址，`your_port_num` 为FastAPI 端口号。

```bash
pip install streamlit		# 安装 streamlit
streamlit run ocr-web.py
```

FastAPI 接口文档：http://your_ip_address:your_port_num/docs

前端 demo：http://localhost:8501	(注：localhost 为运行 streamlit 的主机地址）

效果展示：

![image-20220902014041553](https://s2.loli.net/2022/09/02/TYlygxNwvRzfKS9.png)



开源协议：[Apache 2.0 license](https://github.com/PaddlePaddle/PaddleOCR/blob/master/LICENSE)

