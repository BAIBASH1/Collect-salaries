import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


BASE_URL_HH = 'https://api.hh.ru/vacancies'
BASE_URL_SJ = 'https://api.superjob.ru/2.0/vacancies/'
PROGRAMMING_LANG = [
    'JavaScript',
    'Java',
    'Python',
    'Ruby',
    'PHP',
    'C++',
    'C#',
    'C',
    'Go'
]
load_dotenv()
SECRET_KEY_SJ = os.environ['SECRET_KEY_SJ']


def predict_salary(salary_from, salary_to):
    if salary_to or salary_from:
        if not salary_from:
            predicted_salary = salary_to * 0.8
        elif not salary_to:
            predicted_salary = salary_from * 1.2
        else:
            predicted_salary = (salary_to + salary_from) / 2
    else:
        predicted_salary = None

    return predicted_salary


def predict_rub_salary_hh(vacancy):
    vacancy_salary = vacancy['salary']
    if not vacancy_salary:
        predicted_salary = vacancy_salary
    elif vacancy_salary['currency'] != 'RUR':
        predicted_salary = None
    else:
        predicted_salary = predict_salary(vacancy_salary['from'], vacancy_salary['to'])
    return predicted_salary


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != 'rub':
        predicted_salary = None
    else:
        predicted_salary = predict_salary(vacancy['payment_from'], vacancy['payment_to'])
    return predicted_salary


def process_page_hh(response):
    salaries = []
    vacancies = response.json()['items']
    for vacancy in vacancies:
        predicted_salary = predict_rub_salary_hh(vacancy)
        if predicted_salary:
            salaries.append(predicted_salary)
    vacancies_processed = len(salaries)
    try:
        avg_salary = sum(salaries)/vacancies_processed
    except ZeroDivisionError:
        avg_salary = 0
    return avg_salary, vacancies_processed


def process_page_sj(response):
    salaries = []
    vacancies = response.json()['objects']
    for vacancy in vacancies:
        predicted_salary = predict_rub_salary_sj(vacancy)
        if predicted_salary:
            salaries.append(predicted_salary)
    vacancies_processed = len(salaries)
    try:
        avg_salary = sum(salaries)/vacancies_processed
    except ZeroDivisionError:
        avg_salary = 0
    return avg_salary, vacancies_processed


def collect_all_pages_hh():
    salaries_of_lang = {}
    params = {
        'text': 'Программист',
        'area': 1,
        'page': 0
    }
    for lang in PROGRAMMING_LANG:
        params['text'] = f'Программист {lang}'
        response = requests.get(BASE_URL_HH, params=params)
        response.raise_for_status()
        vacancies = response.json()
        pages = vacancies['pages']
        vacancies_found = vacancies['found']
        vacancies_processed_sum = 0
        salary_sum = 0
        average_salary = 0
        for page in range(pages):
            params['page'] = page
            response = requests.get(BASE_URL_HH, params=params)
            response.raise_for_status()
            average_salary, vacancies_processed = process_page_hh(response)
            vacancies_processed_sum += vacancies_processed
            salary_sum += vacancies_processed * average_salary
        if salary_sum:
            average_salary = salary_sum / vacancies_processed_sum
        else:
            average_salary = 0
        salaries_of_lang[lang] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed_sum,
            "average_salary": int(average_salary)
        }
    return salaries_of_lang


def collect_all_pages_sj():
    headers = {
        'X-Api-App-Id': SECRET_KEY_SJ
    }
    params = {
        'text': 'Программист',
        'town': 4
    }
    salaries_of_lang = {}
    for lang in PROGRAMMING_LANG:
        params['keywords'] = f'Программист {lang}'
        response = requests.get(BASE_URL_SJ, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()
        vacancies_found = vacancies['total']
        vacancies_processed_sum = 0
        salary_sum = 0
        average_salary = 0
        for page in range(int(vacancies_found/20)):
            params['page'] = page
            response = requests.get(BASE_URL_SJ, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()
            average_salary, vacancies_processed = process_page_sj(response)
            vacancies_processed_sum += vacancies_processed
            salary_sum += vacancies_processed * average_salary
        if salary_sum:
            average_salary = salary_sum / vacancies_processed_sum
        else:
            average_salary = 0
        salaries_of_lang[lang] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed_sum,
            "average_salary": int(average_salary)
        }
    return salaries_of_lang


def get_tables_sj(salaries_of_lang):

    table = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang, salary in salaries_of_lang.items():
        table.append([lang, salary['vacancies_found'], salary['vacancies_processed'], salary['average_salary']])
    return AsciiTable(table, 'SuperJob Moscow').table

def get_tables_hh(salaries_of_lang):
    table = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]
    for lang, salary in salaries_of_lang.items():
        table.append([lang, salary['vacancies_found'], salary['vacancies_processed'], salary['average_salary']])
    return AsciiTable(table, 'HeadHunter Moscow').table


def main():
    salaries_sj = collect_all_pages_sj()
    salaries_hh = collect_all_pages_hh()
    print(get_tables_sj(salaries_sj))
    print(get_tables_hh(salaries_hh))

if __name__=='__main__':
    main()