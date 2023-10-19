from fastapi_users import fastapi_users, FastAPIUsers
import pickle

from fastapi import FastAPI, Depends, UploadFile, HTTPException

from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from auth.auth import auth_backend
from auth.database import User
from auth.manager import get_user_manager
from auth.shemas import UserRead, UserCreate

import pandas as pd
import numpy as np
import xgboost as xgb
import os
import aiofiles
from io import BytesIO
import seaborn as sns
import matplotlib.pyplot as plt
import base64
import tempfile

app = FastAPI(
    title="AI"
)

# Добавьте настройки CORS, чтобы фронтенд мог общаться с бэкендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def calculate_month_difference_1(row):
    if row["Месяц2"] >= row["Месяц1"]:
        return row["Месяц2"] - row["Месяц1"]
    else:
        return (12 - row["Месяц1"]) + row["Месяц2"]


# Загрузка модели при запуске сервера
model = None
with open("xgboost_model.pkl", "rb") as model_file:
    model = pickle.load(model_file)


@app.post("/get_ml")
async def upload_json(json_data: dict):
    # В json_data будет содержаться переданный JSON-файл
    # Вы можете провести обработку данных здесь

    # Пример обработки: просто вернуть тот же JSON-файл
    print(json_data)
    return json_data


@app.post("/upload/")
async def upload_file(file: UploadFile):
    try:
        #Чтение CSV файл, который загрузил пользователь
        data = pd.read_csv(file.file)
        
        #ML модель
        def ml(data):
            new_data = pd.DataFrame({'Номер строчки': [],
                                     'Состояние': [],
                                     'Сумма': [],
                                     'Процент': [],
                                     'y': []})
            new_data['Номер строчки'] = data.index + 1
            new_data['Состояние'] = 'Критическое'
            new_data['y'] = 1
            data['exp17'] = data['Изменение позиции заказа на закупку: изменение даты поставки на бумаге'] - \
                            data['Изменение позиции заказа на закупку: дата поставки']
            data['exp5'] = data.apply(calculate_month_difference_1, axis=1)
            data['Дней между 0_8'] = data['Дней между 0_1'].abs() + \
                                  data['Дней между 1_2'].abs() + \
                                  data['Дней между 2_3'].abs() + \
                                  data['Дней между 3_4'].abs() + \
                                  data['Дней между 4_5'].abs() + \
                                  data['Дней между 5_6'].abs() + \
                                  data['Дней между 6_7'].abs() + \
                                  data['Дней между 7_8'].abs()

            data['exp1'] = data['Длительность'] - data['До поставки']

            data['exp2'] = data['Балансовая единица'] / data['До поставки']
            data['exp2'] = data['exp2'].fillna(0)
            data['exp2'] = data['exp2'].replace(np.inf, 0)
            data['exp2'] = data['exp2'].replace(-np.inf, 0)
            data.loc[data['exp2'] < 0, 'exp2'] = 0

            data['exp25'] = data['Балансовая единица'] / data['Длительность']
            data['exp25'] = data['exp25'].fillna(0)
            data['exp25'] = data['exp25'].replace(np.inf, 0)
            data['exp25'] = data['exp25'].replace(-np.inf, 0)
            data.loc[data['exp25'] < 0, 'exp25'] = 0

            data['Согласование заказа 2'] = data['Согласование заказа 2'] - data['Согласование заказа 1']
            data['Согласование заказа 3'] = data['Согласование заказа 3'] - data['Согласование заказа 2'] - data['Согласование заказа 1']

            data['Сумма'] = data['Сумма'] * data['ЕИ']
            data['Количество'] = data['Количество'] * data['ЕИ']

            data['Зак_Бе'] = data['Закупочная организация']*100 + data['Балансовая единица']

            new_data['Процент'] = model.predict(xgb.DMatrix(data=data))
            new_data.loc[new_data['Процент'] <= 0.35, 'y'] = 0
            new_data.loc[new_data['Процент'] <= 0.35, 'Состояние'] = "Позволительное"
            new_data['Сумма'] = data['Сумма'].round(3)
            new_data['Процент'] = new_data['Процент'].round(3)
            return new_data

        result_data = ml(data)

        # Создайте временный буфер для хранения CSV-файла
        temp_buffer = BytesIO()
        result_data.to_csv(temp_buffer, index=False)
        temp_buffer.seek(0)

        # Создайте временный файл для сохранения результатов
        temp_filename = "result_data.csv"

        # Асинхронно сохраните файл
        async with aiofiles.open(temp_filename, mode="wb") as temp_file:
            await temp_file.write(temp_buffer.read())

        # Асинхронно отправьте файл пользователю
        return FileResponse(temp_filename, headers={"Content-Disposition": f"attachment; filename={temp_buffer}"})
        
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/get_file/")
async def get_file():
    # Составьте путь к файлу
    file_path = "result_data.csv"

    # Проверьте, существует ли файл
    if os.path.exists(file_path):
        # Отправьте файл в HTTP-ответе
        return FileResponse(file_path)
    else:
        # Если файл не найден, верните ошибку или сообщение
        return {"error": "File not found"}
    

@app.get("/get_distribution_schedule/")
async def get_file():
    file_path = "result_data.csv"
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
        labels = ["Допустимо", "Критично"]
        rad = 1.45
        a = data['y'].value_counts()
        colors = sns.color_palette('bright')[0:5]
        plt.pie(a, labels=labels, colors=colors, autopct='%.0f%%', radius=rad)
        plt.savefig('Distribution schedule.png')
        plt.close()
        with open("Distribution schedule.png", "rb") as f:
            return {"image": base64.b64encode(f.read()).decode()}

    else:
        return {"error": "File not found"}


@app.get("/get_distributio_sums/")
async def get_file():
    file_path = "result_data.csv"
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
        a = data.loc[data.y == 1, 'Сумма'].sum()
        b = data.loc[data.y == 0, 'Сумма'].sum()
        labels = ["Критично", "Допустим"]
        bar_colors = ['tab:red', 'tab:green']
        fig2, ax2 = plt.subplots()
        ax2.bar(labels, [a, b], color=bar_colors)
        ax2.set_ylabel('Сумма заказа')
        plt.savefig('Distribution sums.png')
        plt.close()
        with open("Distribution sums.png", "rb") as f:
            return {"image": base64.b64encode(f.read()).decode()}

    else:
        return {"error": "File not found"}


@app.get("/get_distribution_probability/")
async def get_file():
    file_path = "result_data.csv"
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
        data["Процент"] = data["Процент"].round(2)
        plt.hist(data["Процент"], bins=np.arange(0, 1.01, 0.1),
                 edgecolor='k')
        plt.xlabel('Уверенность модели в %')
        plt.ylabel('Частота')
        xticks = np.arange(0, 1.01, 0.1)
        plt.xticks(xticks, ['{}'.format(int(x * 100)) for x in xticks])
        plt.savefig('Distribution probability.png')
        plt.close()
        with open("Distribution probability.png", "rb") as f:
            return {"image": base64.b64encode(f.read()).decode()}


    else:
        return {"error": "File not found"}


@app.post("/get_new_table_gran/")
async def get_file(gran: float):
    if gran is None:
        raise HTTPException(status_code=400, detail="Значение 'gran' не было отправлено.")
    
    file_path = "result_data.csv"
    if os.path.exists(file_path):
        data = pd.read_csv(file_path)
        data['y'] = 1
        data['Состояние'] = "Критично"
        data.loc[data['Процент'] <= gran/100, 'y'] = 0
        data.loc[data['Процент'] <= gran/100, 'Состояние'] = "Допустимо"

        temp_filename = "result_data.csv"
        temp_buffer = BytesIO()
        data.to_csv(temp_buffer, index=False)
        temp_buffer.seek(0)

        async with aiofiles.open(temp_filename, mode="wb") as temp_file:
            await temp_file.write(temp_buffer.read())
        
        print({"message": f"Значение 'gran' равно {gran}"})

        return FileResponse(temp_filename, headers={"Content-Disposition": f"attachment; filename={temp_file}"})
    else:
        return {"error": "File not found"}


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

current_user = fastapi_users.current_user()

@app.get("/protected-route")
def protected_route(user: User = Depends(current_user)):
    return f"Hello, {user.username}"


@app.get("/unprotected-route")
def unprotected_route():
    return f"Hello, anonym"