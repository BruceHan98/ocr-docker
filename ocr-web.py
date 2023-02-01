# Copyright (c) 2021 Bruce Han. All Rights Reserved.
# Author: Bruce Han, hantingxiang@gmail.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from PIL import Image
import requests
import streamlit as st


st.markdown(
        f"""
<style>
    .appview-container .main .block-container{{
        max-width: 50%;
        padding-top: 1rem;
        padding-right: 1rem;
        padding-left: 1rem;
        padding-bottom: 1rem;
    }}
</style>
""",
        unsafe_allow_html=True,
    )


types = ("通用识别", "文档识别", "身份证识别", "手写识别")
types_dict = {"通用识别": "universal", "文档识别": "document", "身份证识别": "idcard", "手写识别": "handwritten"}
api = "http://<your_ip>:<your_port>/online/"


@st.experimental_memo
def infer_process(ocr_type, image, api):
    data = {"ocr_type": types_dict[ocr_type]}
    file = {"image_bytes": image}
    res = requests.post(api, params=data, files=file, timeout=8000)
    return res


st.title("OCR")

ocr_type = st.selectbox("识别类型：", types)

upload_image = st.file_uploader("拖曳上传或选择本地图片")

if st.button("识别"):
    image_col, result_col = st.columns(2)
    if upload_image:
        result = infer_process(ocr_type, upload_image, api).json()
        # print(result)

        image_col.header("图片：")
        image_col.image(Image.open(upload_image))

        result_col.header("识别结果：")
        result_col.write(result)
    else:
        st.write("请选择图片！")
