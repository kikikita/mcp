import requests
import json
import pandas as pd

# URL вашего MCP client
url = "http://localhost:8021/process"

df = pd.read_excel('text_layer_output.xlsx')
df = df.dropna()
df['target_param'] = df['dept'].str.extract('(\d+)')
df = df.dropna(subset=['target_param'])
df['target_param'] = df['target_param'].astype(int)
df['podr'] = df['dept'].str.split(r'\\').str[1]
podraz = df['podr'].unique().tolist()
all_data = []
for index, row in df.iterrows():
    payload = {
        "prompt": f"Прочти текст и предположи, какое структурное подразделение ФНС будет ответственным за письмо. "
                  f"Их может быть несколько ответственных за разные задачи в письме, если это так, дай описание кто чем будет заниматься.\n"
                  f"Подразделения ФНС: {podraz}\n"
                  "Для решения используй инструменты в формате JSON {name: <name_of_tool>, "
                  "arguments: <arguments for tool>}, "
                  "чтобы получить функциональные обязанности об определенном подразделении.\n"
                  f"Номер подразделения равен номеру документа\n"
                  "Верни только цифру подразделения без рассуждений.\n"
                  f"Текст: {row['text']}"

    }

    headers = {
        "Content-Type": "application/json"
    }

    # Делаем POST-запрос
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # Печатаем результат
    if response.status_code == 200:
        data = response.json()
        all_data.append(data["response"])
        print("Ответ модели", data["response"], "\n", f"Правильный ответ: {row['target_param']}")
    else:
        print(f"Ошибка {response.status_code}: {response.text}")
        all_data.append('')

df_concat = pd.concat([df, pd.DataFrame(all_data, columns=['answer'])], axis=0, ignore_index=True)
df_concat.to_excel('results.xlsx', index=False)
pd.DataFrame(all_data, columns=['answer']).to_csv('answers.csv')
