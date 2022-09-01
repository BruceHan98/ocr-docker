# Copyright (c) 2021 Bruce Han. All Rights Reserved.
# Author: Bruce Han, hantingxiang@gmail.com

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from loguru import logger

from app import cpp_infer, check_path, save_upload, document, idcard, universal
from app import handwritten_pre_local, handwritten_pre_online

app = FastAPI(title='OCR')

logger.add('ocr.log', rotation='50MB', enqueue=True, serialize=False, encoding="utf-8", retention="30 days")
image_temp_dir = "./ocr_temp_imgs"
if not os.path.exists(image_temp_dir):
    os.makedirs(image_temp_dir)

# configs
supported_types = ["universal", "document", "idcard", "handwritten"]


@app.get("/")
async def root():
    return {"message": "Hello OCR!"}


@app.post("/local/", tags=["local"])
async def local(ocr_type: str, image_path: str):
    try:
        response = {
            "type": "local",
            "status": None,
            "detail": None,
            "result": None,
            "request_time": datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f'),
            "response_time": None
        }

        # 不支持的类型
        if ocr_type not in supported_types:
            # raise HTTPException(status_code=401, detail="[Error] Unsupported type")
            response["status"] = 401
            response["detail"] = "[Error] Unsupported type"
            response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            logger.info(str(response).replace('\n', ' '))
            return JSONResponse(content=jsonable_encoder(response))

        image_list = check_path(image_path)

        # 文件路径不存在
        if not image_list:
            # raise HTTPException(status_code=501, detail="[Error] Image path not exist")
            response["status"] = 501
            response["detail"] = "[Error] Image path not exist"
            response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            logger.info(str(response).replace('\n', ' '))
            return JSONResponse(content=jsonable_encoder(response))

        # 文件夹下无图片
        if len(image_list) == 0:
            # raise HTTPException(status_code=502, detail="[Error] Can't find images")
            response["status"] = 502
            response["detail"] = "[Error] Image path not exist"
            response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            logger.info(str(response).replace('\n', ' '))
            return JSONResponse(content=jsonable_encoder(response))
        
        image_result = []
        for img_path in image_list:
            # 图像预处理
            if ocr_type == "ABC_receipt" or ocr_type == "ABC_check":
                img_path = ABC_note_pre_local(img_path, ocr_type, image_temp_dir)
            elif ocr_type == "handwritten":
                img_path = handwritten_pre_local(img_path, image_temp_dir)
            
            # 执行C++推理
            exec_ok, results, det_time, rec_time = await cpp_infer(img_path, ocr_type)
            # 处理推理结果
            if not exec_ok:
                if results == "Timeout":
                    image_result.append({"image_path": img_path, "ocr_type": ocr_type, "result": "Time out"})
                    continue
                else:
                    image_result.append({"image_path": img_path, "ocr_type": ocr_type, "result": "Exec Error"})
                    continue
            if len(results) == 0:
                image_result.append({"image_path": img_path, "ocr_type": ocr_type, "result": None, "det_time": det_time, "rec_time": rec_time})
                continue

            # 推理结果后处理
            infer_result = None
            if ocr_type == "universal" or ocr_type == "handwritten":
                infer_result = universal(results)
            elif ocr_type == "document":
                infer_result = document(results)
            elif ocr_type == "idcard":
                infer_result = idcard(results)
            image_result.append({"image_path": img_path, "ocr_type": ocr_type, "result": infer_result, "det_time": det_time, "rec_time": rec_time})

            # 删除temp图像
            if ocr_type == "handwritten":
                os.system(f"rm -f {img_path}")
        
        response["status"] = 200
        response["detail"] = "OK"
        response["result"] = image_result
        response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
        logger.info(str(response).replace('\n', ' '))
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.debug(e)
        raise e


@app.post("/online/", tags=["online"])
async def online(ocr_type: str, image_bytes: bytes = File(...)):
    try:
        response = {
            "type": "online",
            "status": None,
            "detail": None,
            "result": None,
            "det_time": None,
            "rec_time": None,
            "request_time": datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f'),
            "response_time": None
        }

        # 不支持的类型
        if ocr_type not in supported_types:
            # raise HTTPException(status_code=401, detail="[Error] Unsupported type")
            response["status"] = 401
            response["detail"] = "[Error] Unsupported type"
            response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            logger.info(str(response).replace('\n', ' '))
            return JSONResponse(content=jsonable_encoder(response))

        # 图像预处理
        if ocr_type == "handwritten":
            img_save_path = handwritten_pre_online(image_bytes, image_temp_dir)
        else:
            img_save_path = save_upload(image_bytes, image_temp_dir)

        # 执行C++推理
        exec_ok, results, det_time, rec_time = await cpp_infer(img_save_path, ocr_type)
        # 处理推理结果
        if not exec_ok:
            if results == "Timeout":
                # raise HTTPException(status_code=503, detail="[Error] Timeout")
                response["status"] = 402
                response["detail"] = "[Error] Time out"
            else:
                # raise HTTPException(status_code=503, detail="[Error] Exec Error")
                response["status"] = 403
                response["detail"] = "[Error] Exec Error"
            response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            logger.info(str(response).replace('\n', ' '))
            return JSONResponse(content=jsonable_encoder(response))
        
        if len(results) == 0:
            # raise HTTPException(status_code=504, detail="[Error] Rec Error or no text region")
            response["status"] = 503
            response["detail"] = "[Error] Rec Error or no text region"
            response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
            logger.info(str(response).replace('\n', ' '))
            return JSONResponse(content=jsonable_encoder(response))

        # 推理结果后处理
        infer_result = None
        if ocr_type == "universal" or ocr_type == "handwritten":
            infer_result = universal(results)
        elif ocr_type == "document":
            infer_result = document(results)
        elif ocr_type == "idcard":
            infer_result = idcard(results)
        
        # 删除temp图片
        os.system(f"rm -f {img_save_path}")

        response["status"] = 200
        response["detail"] = "OK"
        response["result"] = infer_result
        response["det_time"] = det_time
        response["rec_time"] = rec_time
        response["response_time"] = datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')
        logger.info(str(response).replace('\n', ' '))
        return JSONResponse(content=jsonable_encoder(response))
    except Exception as e:
        logger.debug(e)
        raise e
